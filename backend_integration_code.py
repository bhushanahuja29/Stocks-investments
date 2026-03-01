
# Add to crypto_levels_bhushan/backend/main.py

import json
from pathlib import Path

# Load TradingView data at startup
TRADINGVIEW_DATA = {}
TRADINGVIEW_DATA_FILE = Path(__file__).parent.parent / "tradingview_backend_data.json"

def load_tradingview_data():
    """Load TradingView scraped data"""
    global TRADINGVIEW_DATA
    try:
        if TRADINGVIEW_DATA_FILE.exists():
            with open(TRADINGVIEW_DATA_FILE, 'r') as f:
                TRADINGVIEW_DATA = json.load(f)
            print(f"✅ Loaded TradingView data for {len(TRADINGVIEW_DATA)} stocks")
        else:
            print("⚠️ TradingView data file not found")
    except Exception as e:
        print(f"❌ Error loading TradingView data: {e}")

# Call on startup
load_tradingview_data()

# Modify compute_zones_indian_stocks function
def compute_zones_indian_stocks(symbol: str, timeframe: str, version: str = "v3"):
    """
    Compute support zones for Indian stocks using TradingView data
    Falls back to Yahoo Finance if TradingView data not available
    """
    # Try TradingView data first
    if symbol in TRADINGVIEW_DATA:
        tv_data = TRADINGVIEW_DATA[symbol]
        print(f"✅ Using TradingView data for {symbol}")
        return tv_data
    
    # Fallback to Yahoo Finance
    print(f"⚠️ TradingView data not found for {symbol}, using Yahoo Finance")
    return fetch_yahoo_data_indian(symbol, timeframe, version)
