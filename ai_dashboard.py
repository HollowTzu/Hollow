import os
import json
import urllib.request
import xml.etree.ElementTree as ET
import yfinance as yf
from bs4 import BeautifulSoup
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List

# -------------------------------------------------------------------
# 1. Define Pydantic Schema
# -------------------------------------------------------------------
class AssetBias(BaseModel):
    asset: str = Field(description="Asset ticker and name with exact live price (e.g., NQ ($19,850.25))")
    bias: str = Field(description="Trading bias: BEARISH, BULLISH, or NEUTRAL")
    biasClass: str = Field(description="CSS class: badge-bearish, badge-bullish, or badge-neutral")
    horizon: str = Field(description="Timeframe and day bias (e.g., 1–3 Days | Day Bias: Short)")
    driver: str = Field(description="1-sentence fundamental/macro explanation based on news")
    invalidation: str = Field(description="Key technical price level or fundamental trigger to flip bias")

class DeskNote(BaseModel):
    geopolitical_transmission: str = Field(description="Headline summary of rate & macro environment")
    physical_deficit: str = Field(description="Headline summary of commodity/supply conditions")

class DashboardAnalysis(BaseModel):
    desk_note: DeskNote
    bias_data: List[AssetBias]

# -------------------------------------------------------------------
# 2. Scrape Live Market Prices Safely (yfinance)
# -------------------------------------------------------------------
def fetch_live_prices():
    """Fetches accurate real-time prices for the tracked asset list."""
    tickers = {
        "NQ (NASDAQ 100)": "NQ=F",
        "S&P 500 (ES)": "ES=F",
        "GOLD (XAUUSD)": "GC=F",
        "SILVER (XAGUSD)": "SI=F",
        "BTCUSD (BITCOIN)": "BTC-USD",
        "CRUDE OIL (WTI)": "CL=F"
    }
    
    price_data = {}
    for name, symbol in tickers.items():
        try:
            ticker = yf.Ticker(symbol)
            fast_info = ticker.fast_info
            last_price = fast_info.last_price or fast_info.previous_close
            price_data[name] = round(last_price, 2)
        except Exception as e:
            print(f"Price fetch failed for {symbol}: {e}")
            price_data[name] = "N/A"
            
    return price_data

# -------------------------------------------------------------------
# 3. Scrape News Headlines Safely
# -------------------------------------------------------------------
def fetch_raw_news():
    """Scrapes raw headlines from public RSS with safety fallbacks."""
    rss_url = "https://search.cnbc.com/rs/search/combined:rss?q=markets"
    req = urllib.request.Request(rss_url, headers={'User-Agent': 'Mozilla/5.0'})
    headlines = []
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            root = ET.fromstring(response.read())
            for item in root.findall('./channel/item')[:8]:
                title = item.find('title')
                if title is not None and title.text:
                    headlines.append(title.text)
    except Exception as e:
        print(f"News fetch warning: {e}")
        
    return headlines or [
        "Global markets adjust as Treasury yields move alongside interest rate expectations.",
        "Energy prices fluctuate amid changing international supply dynamics."
    ]

# -------------------------------------------------------------------
# 4. AI Analysis Step (GitHub Models Inference)
# -------------------------------------------------------------------
def analyze_market_with_ai(headlines: List[str], prices: dict) -> DashboardAnalysis:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN environment variable is not set by GitHub Actions.")

    client = OpenAI(
        base_url="https://models.github.ai/inference",
        api_key=token
    )
    
    prompt = f"""
    You are an institutional macro strategist.
    
    EXACT REAL-TIME MARKET PRICES:
    {json.dumps(prices, indent=2)}

    LIVE MARKET HEADLINES:
    {headlines}

    Generate market bias cards using the EXACT real-time prices supplied above in the asset title (e.g., "NQ ($19,850.25)").
    Ensure invalidation price levels realistically align with these live price points.

    Respond ONLY in valid JSON matching this exact structure:
    {{
      "desk_note": {{
        "geopolitical_transmission": "1-2 sentence rate & macro summary",
        "physical_deficit": "1-2 sentence commodity supply summary"
      }},
      "bias_data": [
        {{
          "asset": "NQ ($19,850.25)",
          "bias": "BEARISH",
          "biasClass": "badge-bearish",
          "horizon": "1–3 Days | Day Bias: Short",
          "driver": "1-sentence fundamental driver",
          "invalidation": "Technical or macro trigger with precise price level"
        }},
        {{
          "asset": "S&P 500 ($5,520.10)",
          "bias": "BULLISH",
          "biasClass": "badge-bullish",
          "horizon": "1–3 Days | Day Bias: Long",
          "driver": "1-sentence fundamental driver",
          "invalidation": "Technical or macro trigger with precise price level"
        }},
        {{
          "asset": "GOLD ($2,400.50)",
          "bias": "NEUTRAL",
          "biasClass": "badge-neutral",
          "horizon": "1–3 Days | Day Bias: Neutral",
          "driver": "1-sentence fundamental driver",
          "invalidation": "Technical or macro trigger with precise price level"
        }},
        {{
          "asset": "SILVER ($29.10)",
          "bias": "BULLISH",
          "biasClass": "badge-bullish",
          "horizon": "1–3 Days | Day Bias: Long",
          "driver": "1-sentence fundamental driver",
          "invalidation": "Technical or macro trigger with precise price level"
        }},
        {{
          "asset": "BTCUSD ($67,400.00)",
          "bias": "BULLISH",
          "biasClass": "badge-bullish",
          "horizon": "1–3 Days | Day Bias: Long",
          "driver": "1-sentence fundamental driver",
          "invalidation": "Technical or macro trigger with precise price level"
        }},
        {{
          "asset": "CRUDE OIL ($78.30)",
          "bias": "BEARISH",
          "biasClass": "badge-bearish",
          "horizon": "1–3 Days | Day Bias: Short",
          "driver": "1-sentence fundamental driver",
          "invalidation": "Technical or macro trigger with precise price level"
        }}
      ]
    }}
    """

    completion = client.chat.completions.create(
        model="openai/gpt-4o",
        messages=[
            {"role": "system", "content": "You are a quantitative finance API that outputs purely JSON based on accurate input data."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )
    
    return DashboardAnalysis.model_validate_json(completion.choices[0].message.content)

# -------------------------------------------------------------------
# 5. Inject Generated Data into index.html
# -------------------------------------------------------------------
def update_html_dashboard():
    headlines = fetch_raw_news()
    prices = fetch_live_prices()
    
    print(f"Fetched live prices: {prices}")
    print(f"Scraped {len(headlines)} headlines. Running GitHub Models AI analysis...")
    
    analysis = analyze_market_with_ai(headlines, prices)

    with open('index.html', 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    # Update Desk Note
    note_container = soup.find('div', id='desk-note-content')
    if note_container:
        note_container.clear()
        note_html = (
            f"<b>GEOPOLITICAL &amp; RATE TRANSMISSION:</b> {analysis.desk_note.geopolitical_transmission}<br><br>"
            f"<b>STRUCTURAL PHYSICAL DEFICIT:</b> {analysis.desk_note.physical_deficit}"
        )
        note_container.append(BeautifulSoup(note_html, 'html.parser'))

    # Update Bias Cards Grid
    bias_container = soup.find('div', class_='bias-grid')
    if bias_container:
        bias_container.clear()
        for card in analysis.bias_data:
            inv_parts = card.invalidation.split(':', 1)
            label = inv_parts[0] if len(inv_parts) > 1 else "Flip condition"
            val = inv_parts[1] if len(inv_parts) > 1 else card.invalidation

            card_html = f"""
            <div class="bias-card">
              <div class="bias-head">
                <span class="bias-asset">{card.asset}</span>
                <span class="bias-badge {card.biasClass}">{card.bias}</span>
              </div>
              <div class="bias-meta">Swing Horizon: {card.horizon}</div>
              <div class="bias-driver">{card.driver}</div>
              <div class="bias-invalidation"><b>{label}:</b>{val}</div>
            </div>
            """
            bias_container.append(BeautifulSoup(card_html, 'html.parser'))

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(soup.prettify())

    print("index.html updated successfully with live market prices and AI analysis.")

if __name__ == '__main__':
    update_html_dashboard()
