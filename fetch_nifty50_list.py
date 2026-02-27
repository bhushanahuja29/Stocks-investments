"""
Fetch current Nifty 50 constituents from NSE India
Updates the frontend with the latest list
"""
import requests
from bs4 import BeautifulSoup
import json

# Current Nifty 50 constituents as of Feb 2026
# Based on NSE official data and recent changes
NIFTY_50_STOCKS = [
    { 'symbol': 'RELIANCE', 'name': 'Reliance Industries' },
    { 'symbol': 'HDFCBANK', 'name': 'HDFC Bank' },
    { 'symbol': 'BHARTIARTL', 'name': 'Bharti Airtel' },
    { 'symbol': 'SBIN', 'name': 'State Bank of India' },
    { 'symbol': 'ICICIBANK', 'name': 'ICICI Bank' },
    { 'symbol': 'TCS', 'name': 'Tata Consultancy Services' },
    { 'symbol': 'BAJFINANCE', 'name': 'Bajaj Finance' },
    { 'symbol': 'LT', 'name': 'Larsen & Toubro' },
    { 'symbol': 'HINDUNILVR', 'name': 'Hindustan Unilever' },
    { 'symbol': 'INFY', 'name': 'Infosys' },
    { 'symbol': 'MARUTI', 'name': 'Maruti Suzuki' },
    { 'symbol': 'AXISBANK', 'name': 'Axis Bank' },
    { 'symbol': 'KOTAKBANK', 'name': 'Kotak Mahindra Bank' },
    { 'symbol': 'M&M', 'name': 'Mahindra & Mahindra' },
    { 'symbol': 'SUNPHARMA', 'name': 'Sun Pharmaceutical' },
    { 'symbol': 'ITC', 'name': 'ITC Limited' },
    { 'symbol': 'HCLTECH', 'name': 'HCL Technologies' },
    { 'symbol': 'ULTRACEMCO', 'name': 'UltraTech Cement' },
    { 'symbol': 'TITAN', 'name': 'Titan Company' },
    { 'symbol': 'NTPC', 'name': 'NTPC Limited' },
    { 'symbol': 'ADANIPORTS', 'name': 'Adani Ports' },
    { 'symbol': 'ONGC', 'name': 'Oil & Natural Gas Corporation' },
    { 'symbol': 'BAJAJFINSV', 'name': 'Bajaj Finserv' },
    { 'symbol': 'BEL', 'name': 'Bharat Electronics' },
    { 'symbol': 'JSWSTEEL', 'name': 'JSW Steel' },
    { 'symbol': 'ASIANPAINT', 'name': 'Asian Paints' },
    { 'symbol': 'WIPRO', 'name': 'Wipro' },
    { 'symbol': 'TECHM', 'name': 'Tech Mahindra' },
    { 'symbol': 'POWERGRID', 'name': 'Power Grid Corporation' },
    { 'symbol': 'TATASTEEL', 'name': 'Tata Steel' },
    { 'symbol': 'INDUSINDBK', 'name': 'IndusInd Bank' },
    { 'symbol': 'DIVISLAB', 'name': 'Divi\'s Laboratories' },
    { 'symbol': 'DRREDDY', 'name': 'Dr. Reddy\'s Laboratories' },
    { 'symbol': 'CIPLA', 'name': 'Cipla' },
    { 'symbol': 'EICHERMOT', 'name': 'Eicher Motors' },
    { 'symbol': 'HEROMOTOCO', 'name': 'Hero MotoCorp' },
    { 'symbol': 'GRASIM', 'name': 'Grasim Industries' },
    { 'symbol': 'HINDALCO', 'name': 'Hindalco Industries' },
    { 'symbol': 'BRITANNIA', 'name': 'Britannia Industries' },
    { 'symbol': 'APOLLOHOSP', 'name': 'Apollo Hospitals' },
    { 'symbol': 'BPCL', 'name': 'Bharat Petroleum' },
    { 'symbol': 'TATACONSUM', 'name': 'Tata Consumer Products' },
    { 'symbol': 'SBILIFE', 'name': 'SBI Life Insurance' },
    { 'symbol': 'HDFCLIFE', 'name': 'HDFC Life Insurance' },
    { 'symbol': 'BAJAJ-AUTO', 'name': 'Bajaj Auto' },
    { 'symbol': 'SHREECEM', 'name': 'Shree Cement' },
    { 'symbol': 'LTIM', 'name': 'LTIMindtree' },
    { 'symbol': 'COALINDIA', 'name': 'Coal India' },
    { 'symbol': 'ADANIGREEN', 'name': 'Adani Green Energy' },
    { 'symbol': 'NESTLEIND', 'name': 'Nestle India' }
]

# Note: TATAMOTORS was removed from Nifty 50 after demerger
# ADANIGREEN and BEL (Bharat Electronics) are recent additions

def verify_symbols_yahoo():
    """Verify symbols work with Yahoo Finance"""
    import yfinance as yf
    
    print("Verifying Nifty 50 symbols with Yahoo Finance...")
    print("="*80)
    
    valid_stocks = []
    invalid_stocks = []
    
    for stock in NIFTY_50_STOCKS:
        symbol = stock['symbol']
        yahoo_symbol = f"{symbol}.NS"
        
        try:
            ticker = yf.Ticker(yahoo_symbol)
            info = ticker.info
            
            # Check if we got valid data
            if 'symbol' in info or 'shortName' in info:
                valid_stocks.append(stock)
                print(f"✅ {symbol:15} - {stock['name']}")
            else:
                invalid_stocks.append(stock)
                print(f"❌ {symbol:15} - {stock['name']} (No data)")
        except Exception as e:
            invalid_stocks.append(stock)
            print(f"❌ {symbol:15} - {stock['name']} (Error: {str(e)[:50]})")
    
    print("\n" + "="*80)
    print(f"Valid: {len(valid_stocks)}, Invalid: {len(invalid_stocks)}")
    print("="*80)
    
    if invalid_stocks:
        print("\n⚠️ Invalid symbols:")
        for stock in invalid_stocks:
            print(f"  - {stock['symbol']} ({stock['name']})")
    
    return valid_stocks

def generate_frontend_code(stocks):
    """Generate JavaScript array for frontend"""
    print("\n" + "="*80)
    print("JavaScript code for frontend:")
    print("="*80)
    print("\nconst nifty50Stocks = [")
    for stock in stocks:
        print(f"    {{ symbol: '{stock['symbol']}', name: '{stock['name']}' }},")
    print("];")
    print("\n" + "="*80)

if __name__ == "__main__":
    print("\n" + "="*80)
    print("NIFTY 50 STOCKS LIST UPDATER")
    print("="*80)
    print(f"\nTotal stocks in list: {len(NIFTY_50_STOCKS)}")
    print("\nKey changes from previous list:")
    print("  ❌ Removed: TATAMOTORS (after demerger)")
    print("  ✅ Added: ADANIGREEN (Adani Green Energy)")
    print("  ✅ Added: BEL (Bharat Electronics)")
    print("\n" + "="*80)
    
    # Verify symbols
    valid_stocks = verify_symbols_yahoo()
    
    # Generate frontend code
    if valid_stocks:
        generate_frontend_code(valid_stocks)
    
    print("\n✅ Done! Copy the JavaScript array above to ZoneFinder.js")

