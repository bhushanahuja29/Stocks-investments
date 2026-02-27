"""
TradingView Auto Scraper with Keyboard Controls
Opens Chrome, navigates to charts, presses Alt+R and W, takes screenshots
"""
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

# Nifty 50 stocks
NIFTY_50_STOCKS = [
    'RELIANCE', 'HDFCBANK', 'BHARTIARTL', 'SBIN', 'ICICIBANK',
    'TCS', 'BAJFINANCE', 'LT', 'HINDUNILVR', 'INFY',
    'MARUTI', 'AXISBANK', 'KOTAKBANK', 'M&M', 'SUNPHARMA',
    'ITC', 'HCLTECH', 'ULTRACEMCO', 'TITAN', 'NTPC',
    'ADANIPORTS', 'ONGC', 'BAJAJFINSV', 'BEL', 'JSWSTEEL',
    'ASIANPAINT', 'WIPRO', 'TECHM', 'POWERGRID', 'TATASTEEL',
    'INDUSINDBK', 'DIVISLAB', 'DRREDDY', 'CIPLA', 'EICHERMOT',
    'HEROMOTOCO', 'GRASIM', 'HINDALCO', 'BRITANNIA', 'APOLLOHOSP',
    'BPCL', 'TATACONSUM', 'SBILIFE', 'HDFCLIFE', 'BAJAJ-AUTO',
    'SHREECEM', 'LTIM', 'COALINDIA', 'ADANIGREEN', 'NESTLEIND'
]

def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║   TradingView Auto Scraper with Keyboard Controls      ║
║   Alt+R to reset, W for Weekly timeframe               ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    print("🚀 Starting Chrome...")
    
    # Chrome options
    options = Options()
    options.add_argument('--start-maximized')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    try:
        driver = webdriver.Chrome(options=options)
        print("✅ Chrome started!")
        
        # Create screenshot directory
        os.makedirs('tradingview_screenshots', exist_ok=True)
        
        print("\n⚠️ IMPORTANT:")
        print("   Make sure you're logged into TradingView")
        print("   Script will:")
        print("   1. Open each chart")
        print("   2. Type '1w' and press Enter (Weekly timeframe)")
        print("   3. Press Alt+R to reset view")
        print("   4. Take screenshot")
        print()
        
        input("Press ENTER to start scraping...")
        
        # Scrape all stocks
        for i, symbol in enumerate(NIFTY_50_STOCKS, 1):
            print(f"\n[{i}/{len(NIFTY_50_STOCKS)}] 📊 {symbol}")
            
            try:
                # Navigate to chart with your template
                url = f"https://in.tradingview.com/chart/Vhwft9jB/?symbol=NSE%3A{symbol}"
                print(f"   🌐 Loading chart...")
                driver.get(url)
                
                # Wait for page to load
                time.sleep(8)
                
                # Type '1w' and press Enter to set Weekly timeframe FIRST
                print(f"   ⌨️  Typing '1w' + Enter (weekly timeframe)...")
                actions = ActionChains(driver)
                actions.send_keys('1w').send_keys(Keys.RETURN).perform()
                time.sleep(3)
                
                # THEN Press Alt+R to reset chart view
                print(f"   ⌨️  Pressing Alt+R (reset view)...")
                actions = ActionChains(driver)
                actions.key_down(Keys.ALT).send_keys('r').key_up(Keys.ALT).perform()
                time.sleep(3)
                
                # Take screenshot
                screenshot_path = f'tradingview_screenshots/{symbol}_NSE.png'
                driver.save_screenshot(screenshot_path)
                print(f"   📸 Screenshot saved!")
                
            except Exception as e:
                print(f"   ❌ Error: {str(e)[:80]}")
            
            # Small delay between stocks
            time.sleep(2)
        
        # Summary
        print("\n" + "="*70)
        print("✅ SCRAPING COMPLETE!")
        print("="*70)
        print(f"\n📁 Screenshots saved to: tradingview_screenshots/")
        print(f"📊 Total: {len(NIFTY_50_STOCKS)} stocks")
        
        print("\n💡 Next Step:")
        print("   python ocr_red_boxes.py")
        print("   This will extract levels from the screenshots")
        
        input("\nPress ENTER to close Chrome...")
        driver.quit()
        print("✅ Done!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("1. Chrome is not already running")
        print("2. Profile 3 exists and has TradingView logged in")
        print("3. ChromeDriver is installed")

if __name__ == "__main__":
    main()
