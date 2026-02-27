"""
Update Backend with TradingView Scraped Levels
Converts TradingView JSON data to backend-compatible format
"""
import json
import os
from datetime import datetime

def load_latest_tradingview_data():
    """Load the most recent TradingView scraping results"""
    # Find all tradingview_levels_*.json files
    json_files = [f for f in os.listdir('.') if f.startswith('tradingview_levels_') and f.endswith('.json')]
    
    if not json_files:
        print("❌ No TradingView data files found")
        print("   Run: python tradingview_scraper_advanced.py first")
        return None
    
    # Get the most recent file
    latest_file = sorted(json_files)[-1]
    print(f"📂 Loading: {latest_file}")
    
    with open(latest_file, 'r') as f:
        data = json.load(f)
    
    print(f"✅ Loaded data for {len(data)} stocks")
    return data


def convert_to_backend_format(tv_data):
    """Convert TradingView data to backend zone format"""
    backend_data = {}
    
    for symbol, stock_data in tv_data.items():
        levels = stock_data.get('levels', [])
        
        if not levels:
            continue
        
        # Convert levels to zones (each level becomes a zone)
        zones = []
        for i, level in enumerate(levels):
            zone = {
                'top': level,
                'bottom': level * 0.98,  # 2% below as zone bottom
                'date': stock_data.get('timestamp', datetime.now().isoformat())[:10],
                'rally_length': 1,  # Placeholder
                'total_move_pct': 0,  # Placeholder
                'source': 'tradingview_scraper'
            }
            zones.append(zone)
        
        backend_data[symbol] = {
            'symbol': symbol,
            'timeframe': stock_data.get('timeframe', '1W'),
            'zones': zones,
            'count': len(zones),
            'success': True,
            'source': 'tradingview',
            'screenshot': stock_data.get('screenshot', ''),
            'timestamp': stock_data.get('timestamp', '')
        }
    
    return backend_data


def save_backend_data(backend_data, output_file='tradingview_backend_data.json'):
    """Save converted data for backend use"""
    with open(output_file, 'w') as f:
        json.dump(backend_data, f, indent=2)
    
    print(f"✅ Backend data saved to: {output_file}")
    print(f"📊 Total stocks: {len(backend_data)}")


def generate_backend_integration_code():
    """Generate Python code for backend integration"""
    code = '''
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
'''
    
    return code


def main():
    """Main execution"""
    print("""
╔══════════════════════════════════════════════════════════╗
║   Update Backend with TradingView Data                   ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    # Load TradingView data
    tv_data = load_latest_tradingview_data()
    if not tv_data:
        return
    
    print("\n" + "="*60)
    print("📊 TradingView Data Summary")
    print("="*60)
    
    for symbol, data in list(tv_data.items())[:5]:  # Show first 5
        levels = data.get('levels', [])
        print(f"\n{symbol}:")
        print(f"  Timeframe: {data.get('timeframe', 'N/A')}")
        print(f"  Levels: {len(levels)}")
        if levels:
            print(f"  Sample: {levels[:3]}")
    
    if len(tv_data) > 5:
        print(f"\n... and {len(tv_data) - 5} more stocks")
    
    # Convert to backend format
    print("\n" + "="*60)
    print("🔄 Converting to backend format...")
    print("="*60)
    
    backend_data = convert_to_backend_format(tv_data)
    
    # Save backend data
    save_backend_data(backend_data)
    
    # Generate integration code
    print("\n" + "="*60)
    print("📝 Backend Integration Code")
    print("="*60)
    
    integration_code = generate_backend_integration_code()
    
    # Save integration code
    with open('backend_integration_code.py', 'w') as f:
        f.write(integration_code)
    
    print("\n✅ Integration code saved to: backend_integration_code.py")
    
    # Instructions
    print("\n" + "="*60)
    print("📋 Next Steps")
    print("="*60)
    print("""
1. Copy tradingview_backend_data.json to project root:
   cp tradingview_backend_data.json crypto_levels_bhushan/

2. Add integration code to backend/main.py:
   - Copy code from backend_integration_code.py
   - Add to crypto_levels_bhushan/backend/main.py

3. Restart backend:
   cd crypto_levels_bhushan/backend
   python main.py

4. Test with frontend:
   - Select "Indian Stocks" market type
   - Search for RELIANCE or any Nifty 50 stock
   - Verify levels match TradingView

5. Schedule daily updates:
   - Run tradingview_scraper_advanced.py daily
   - Run this script to update backend data
   - Restart backend to reload data
    """)
    
    print("="*60)
    print("✅ Backend update preparation complete!")
    print("="*60)


if __name__ == "__main__":
    main()
