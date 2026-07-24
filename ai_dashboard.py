import os
import urllib.request
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List

# -------------------------------------------------------------------
# 1. Define Pydantic Schema
# -------------------------------------------------------------------
class AssetBias(BaseModel):
    asset: str = Field(description="Asset ticker and name (e.g., NQ (NASDAQ 100))")
    bias: str = Field(description="Trading bias: BEARISH, BULLISH, or NEUTRAL")
    biasClass: str = Field(description="CSS class: badge-bearish, badge-bullish, or badge-neutral")
    horizon: str = Field(description="Timeframe and day bias (e.g., 1–3 Days | Day Bias: Short)")
    driver: str = Field(description="1-sentence fundamental/macro explanation based on news")
    invalidation: str = Field(description="Key technical or fundamental trigger to flip bias")

class DeskNote(BaseModel):
    geopolitical_transmission: str = Field(description="Headline summary of rate & macro environment")
    physical_deficit: str = Field(description="Headline summary of commodity/supply conditions")

class DashboardAnalysis(BaseModel):
    desk_note: DeskNote
    bias_data: List[AssetBias]

# -------------------------------------------------------------------
# 2. Scrape News Headlines
# -------------------------------------------------------------------
def fetch_raw_news():
    """Scrapes raw headlines from public RSS."""
    rss_url = "https://search.cnbc.com/rs/search/combined:rss?q=markets"
    req = urllib.request.Request(rss_url, headers={'User-Agent': 'Mozilla/5.0'})
    headlines = []
    
    try:
        with urllib.request.urlopen(req) as response:
            root = ET.fromstring(response.read())
            for item in root.findall('./channel/item')[:8]:
                title = item.find('title')
                if title is not None and title.text:
                    headlines.append(title.text)
    except Exception as e:
        print(f"News fetch error: {e}")
        
    return headlines or ["Markets track central bank signals and Treasury yield movements."]

# -------------------------------------------------------------------
# 3. AI Analysis Step (Generates Structured JSON)
# -------------------------------------------------------------------
def analyze_market_with_ai(headlines: List[str]) -> DashboardAnalysis:
    client = genai.Client()
    
    prompt = f"""
    You are a quantitative institutional macro strategist.
    Analyze these live market headlines:
    {headlines}

    Generate market bias cards for: NQ (NASDAQ 100), S&P 500 (ES), GOLD (XAUUSD), SILVER (XAGUSD), BTCUSD (BITCOIN), CRUDE OIL (WTI).
    Determine realistic institutional drivers, invalidation criteria, and short-term biases based on current rate & market conditions.
    """

    # Enforce structured output schema using active model gemini-2.5-flash
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=DashboardAnalysis,
        ),
    )
    
    # Parse output as Python Pydantic object
    return DashboardAnalysis.model_validate_json(response.text)

# -------------------------------------------------------------------
# 4. Inject Generated Data into index.html
# -------------------------------------------------------------------
def update_html_dashboard():
    headlines = fetch_raw_news()
    print(f"Scraped {len(headlines)} headlines. Running AI analysis...")
    
    analysis = analyze_market_with_ai(headlines)

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

    print("index.html updated successfully with AI-generated analysis.")

if __name__ == '__main__':
    update_html_dashboard()
