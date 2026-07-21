import os
import re
import json
import urllib.request
from bs4 import BeautifulSoup

def fetch_json(url):
    """Utility function to fetch JSON data from public endpoints."""
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def calculate_macro_regime():
    """Fetches key market indicators to determine daily risk-on/risk-off status."""
    # Fetch live Gold spot price from public API as an example anchor
    gold_data = fetch_json("https://api.gold-api.com/price/XAU")
    
    # Default baseline regime parameters
    regime = "MODERATE RISK-ON"
    vix_estimate = "~14.5"
    meter_width = "68%"
    
    # Custom quantitative logic can be expanded here based on yield/index API feeds
    if gold_data and "price" in gold_data:
        price = gold_data["price"]
        print(f"Current Gold Reference Price: ${price}")
        # Example dynamic adjustment rule:
        if price > 4150:
            regime = "DEFENSIVE / RISK-OFF"
            meter_width = "35%"
            vix_estimate = "~18.2"
        elif price < 4000:
            regime = "STRONG RISK-ON"
            meter_width = "85%"
            vix_estimate = "~12.8"

    return regime, meter_width, vix_estimate

def update_html_dashboard():
    html_file = "index.html"
    if not os.path.exists(html_file):
        print(f"Error: {html_file} not found in directory.")
        return

    with open(html_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    # 1. Update Cross-Asset Risk Gauge
    regime, meter_width, vix = calculate_macro_regime()
    
    status_el = soup.find(class_="risk-status")
    if status_el:
        status_el.string = regime
        
    fill_el = soup.find(class_="risk-fill")
    if fill_el:
        fill_el["style"] = f"height:100%; width:{meter_width}; background: linear-gradient(90deg, var(--short), var(--amber), var(--long));"

    # 2. Update Asset Bias Badges Dynamically (Example setup for Daily Bias cards)
    bias_cards = soup.find_all(class_="bias-card")
    
    # Example daily updates for cards
    card_updates = {
        "NQ (NASDAQ 100)": {"badge": "BULLISH · STRONG", "class": "badge-bullish", "driver": "Tech earnings expansion holding key value area; systematic bid active."},
        "S&P 500 (ES)": {"badge": "BULLISH · MODERATE", "class": "badge-bullish", "driver": "Broad equity index breadth absorbing supply; corporate buybacks active."},
        "GOLD (XAUUSD)": {"badge": "BEARISH · SHORT-TERM", "class": "badge-bearish", "driver": "US real yield pressure and hawkish Fed rate repricing capping upside momentum."},
        "SILVER (XAGUSD)": {"badge": "NEUTRAL · RANGE", "class": "badge-neutral", "driver": "Torn between Gold macro yield pressure and strong industrial demand fundamentals."},
        "BTCUSD (BITCOIN)": {"badge": "BULLISH · STRONG", "class": "badge-bullish", "driver": "Sustained institutional spot ETF net inflows & macro global liquidity expansion."},
        "CRUDE OIL (WTI)": {"badge": "BEARISH · MODERATE", "class": "badge-bearish", "driver": "Commercial inventories building while OPEC maintains output baseline."}
    }

    for card in bias_cards:
        asset_el = card.find(class_="bias-asset")
        if asset_el and asset_el.string in card_updates:
            asset_name = asset_el.string
            update_data = card_updates[asset_name]
            
            # Update badge text and CSS class
            badge_el = card.find(class_="bias-badge")
            if badge_el:
                badge_el.string = update_data["badge"]
                badge_el["class"] = ["bias-badge", update_data["class"]]
                
            # Update driver text
            driver_el = card.find(class_="bias-driver")
            if driver_el:
                driver_el.string = update_data["driver"]

    # Save updated HTML back to file
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(str(soup))
        
    print(f"Successfully updated {html_file} at market open.")

if __name__ == "__main__":
    update_html_dashboard()
