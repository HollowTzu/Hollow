import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

def get_latest_macro_news():
    """Fetches real-time financial headlines from a public RSS feed."""
    rss_url = "https://finance.yahoo.com/news/rssindex"
    
    req = urllib.request.Request(
        rss_url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        items = root.findall('./channel/item')
        if len(items) >= 2:
            headline_1 = items[0].find('title').text
            headline_2 = items[1].find('title').text
            return headline_1, headline_2
    except Exception as e:
        print(f"Error fetching RSS news: {e}")
        
    # Fallback context if RSS stream is temporarily offline
    return (
        "Markets are actively balancing diplomatic mediation headlines out of the Middle East against sticky inflation readings.",
        "Precious metals consolidate as industrial demand drivers remain unyielding across AI infrastructure and solar manufacturing."
    )

def generate_updated_dashboard():
    # 1. Define Updated Bias Card Data Structure
    updated_bias_data = [
        {
            "asset": "NQ (NASDAQ 100)",
            "bias": "BEARISH",
            "biasClass": "badge-bearish",
            "horizon": "1–3 Days | Bias: Short",
            "driver": "Crude oil surge lifts bond yields, applying heavy valuation pressure on growth tech.",
            "invalidation": "Flip condition: Reclaim above resistance near 29,400."
        },
        {
            "asset": "S&P 500 (ES)",
            "bias": "NEUTRAL",
            "biasClass": "badge-neutral",
            "horizon": "1–5 Days | Bias: Range",
            "driver": "Consolidating below key levels as energy inflation fears weigh on broad risk appetite.",
            "invalidation": "Flip condition: Sustained break above multi-month consolidation boundaries."
        },
        {
            "asset": "GOLD (XAUUSD)",
            "bias": "BEARISH",
            "biasClass": "badge-bearish",
            "horizon": "Intraday | Bias: Short/Range",
            "driver": "High US yields reinforce Fed rate hike odds, suppressing non-yielding bullion.",
            "invalidation": "Flip condition: Safe-haven demand spike driving spot decisively past $4,150 resistance."
        },
        {
            "asset": "SILVER (XAGUSD)",
            "bias": "NEUTRAL",
            "biasClass": "badge-neutral",
            "horizon": "1–3 Days | Bias: Mean Reversion",
            "driver": "Riding between structural industrial deficits and short-term pressure from elevated dollar yields.",
            "invalidation": "Flip condition: Decisive break outside multi-week technical consolidation range."
        },
        {
            "asset": "BTCUSD (BITCOIN)",
            "bias": "NEUTRAL",
            "biasClass": "badge-neutral",
            "horizon": "3–7 Days | Bias: Range",
            "driver": "Rebound testing key resistance; higher energy yields cap momentum for digital risk assets.",
            "invalidation": "Flip condition: Confirmed breakout above $67,000 or breakdown below $63,000."
        },
        {
            "asset": "CRUDE OIL (WTI)",
            "bias": "BULLISH",
            "biasClass": "badge-bullish",
            "horizon": "1–3 Days | Bias: Long",
            "driver": "Supply routing disruption risks around Hormuz/Red Sea keeping crude firm toward $90.",
            "invalidation": "Flip condition: De-escalation agreement directly opening trade chokepoints."
        }
    ]

    # 2. Read index.html from disk
    with open('index.html', 'r', encoding='utf-8') as f:
        html_content = f.read()

    # 3. Parse DOM Tree with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')

    # 4. Fetch Live RSS Headlines
    geo_headline, supply_headline = get_latest_macro_news()

    # 5. Target the Desk Note element and overwrite text word-for-word
    desk_note_header = soup.find("div", string=lambda t: t and "INSTITUTIONAL SESSION DESK NOTE" in t)
    
    if desk_note_header and desk_note_header.parent:
        content_div = desk_note_header.parent.find_all("div")[1] if len(desk_note_header.parent.find_all("div")) > 1 else desk_note_header.parent
        
        # Inject dynamic headlines directly into DOM node
        new_html_content = (
            f"<b>GEOPOLITICAL & RATE TRANSMISSION:</b> {geo_headline}<br><br>"
            f"<b>STRUCTURAL PHYSICAL DEFICIT:</b> {supply_headline}"
        )
        content_div.clear()
        content_div.append(BeautifulSoup(new_html_content, 'html.parser'))

    # 6. Convert modified DOM back to HTML string
    modified_html = str(soup)

    # 7. Update JavaScript Array using Regex
    formatted_json = json.dumps(updated_bias_data, indent=2)
    pattern = r'const dashboardData = \[.*?\];'
    replacement = f'const dashboardData = {formatted_json};'

    if re.search(pattern, modified_html, flags=re.DOTALL):
        updated_html = re.sub(pattern, replacement, modified_html, flags=re.DOTALL)
    else:
        updated_html = modified_html

    # 8. Write updated file back to index.html
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(updated_html)

    print("index.html text and JS data structure updated successfully.")

if __name__ == '__main__':
    generate_updated_dashboard()
