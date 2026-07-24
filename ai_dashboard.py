import json
import requests
from bs4 import BeautifulSoup
from typing import Dict

# -------------------------------------------------------------------
# TradingEconomics Scraper for Live Prices
# -------------------------------------------------------------------
TE_URLS = {
    "GOLD (XAUUSD)": "https://tradingeconomics.com/commodity/gold",
    "SILVER (XAGUSD)": "https://tradingeconomics.com/commodity/silver",
    "CRUDE OIL (WTI)": "https://tradingeconomics.com/commodity/crude-oil",
    "NQ (NASDAQ 100)": "https://tradingeconomics.com/us/nasdaq-100",
    "S&P 500 (ES)": "https://tradingeconomics.com/us/sp-500",
    "BTCUSD (BITCOIN)": "https://tradingeconomics.com/crypto/bitcoin"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def fetch_live_prices() -> Dict[str, str]:
    prices = {}
    
    for name, url in TE_URLS.items():
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                
                # TradingEconomics embeds the primary price in the #p element
                price_elem = soup.find("id", id="p") or soup.select_one("#p")
                
                if price_elem:
                    raw_price = price_elem.text.strip().replace(",", "")
                    val = float(raw_price)
                    prices[name] = f"${val:,.2f}"
                else:
                    # Fallback lookup in price table
                    price_table_cell = soup.select_one("table.table td#p")
                    if price_table_cell:
                        val = float(price_table_cell.text.strip().replace(",", ""))
                        prices[name] = f"${val:,.2f}"
                    else:
                        prices[name] = "FETCH_FAILED"
            else:
                prices[name] = "FETCH_FAILED"
        except Exception as e:
            print(f"[ERROR] Failed scraping {name} from TradingEconomics: {e}")
            prices[name] = "FETCH_FAILED"

    print(f"[DEBUG] TradingEconomics Fetched Prices:\n{json.dumps(prices, indent=2)}")
    return prices
