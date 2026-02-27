"""
Update Backend with OCR-Extracted Levels
"""
import json
import sys
import os
import glob
import requests
from datetime import datetime

BACKEND_URL = "http://localhost:5000"

def update_backend(data):
    """Send levels to backend API"""
    
    successful_updates = 0
    failed_updates = 0
    
    for entry in data:
        if not entry.get('success'):
            print(f"⏭️  Skipping {entry['symbol']} (no data)")
            continue
        
        symbol = entry['symbol']
        print(f"\n📊 Updating {symbol}...")
        
        # Prepare data for backend
        payload = {
            'symbol': symbol,
            'exchange': entry.get('exchange', 'NSE'),
            'market_type': entry.get('market_type', 'indian_stock'),
            'support_levels': entry['support_levels'],
            'resistance_levels': entry['resistance_levels'],
            'source': entry.get('source', 'TradingView OCR'),
            'timestamp': entry['timestamp']
        }
        
        try:
            # Update levels endpoint
            response = requests.post(
                f"{BACKEND_URL}/api/levels/update",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"   ✅ Updated successfully")
                successful_updates += 1
            else:
                print(f"   ❌ Error: {response.status_code} - {response.text}")
                failed_updates += 1
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Cannot connect to backend at {BACKEND_URL}")
            print(f"   Make sure backend is running!")
            return False
        except Exception as e:
            print(f"   ❌ Error: {e}")
            failed_updates += 1
    
    print("\n" + "="*70)
    print(f"✅ Updated: {successful_updates}")
    print(f"❌ Failed: {failed_updates}")
    print("="*70)
    
    return True

def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║   Update Backend with OCR Levels                        ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    # Get input file from command line or use latest
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        # Find latest tradingview_levels_*.json file
        files = glob.glob('tradingview_levels_*.json')
        if not files:
            print("❌ No tradingview_levels_*.json files found")
            print("   Run: python ocr_chart_analyzer.py first")
            return
        input_file = max(files, key=os.path.getctime)
        print(f"📂 Using latest file: {input_file}")
    
    if not os.path.exists(input_file):
        print(f"❌ File not found: {input_file}")
        return
    
    # Load data
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    successful_data = [d for d in data if d.get('success')]
    
    print(f"📂 Loaded {len(data)} entries ({len(successful_data)} with data)")
    
    # Show summary
    print("\n📋 Will update:")
    for entry in successful_data:
        print(f"   • {entry['symbol']}: {len(entry['support_levels'])} supports, {len(entry['resistance_levels'])} resistances")
    
    print(f"\n🎯 Backend: {BACKEND_URL}")
    
    # Confirm
    confirm = input("\nProceed with update? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ Cancelled")
        return
    
    # Update backend
    print("\n🚀 Updating backend...")
    success = update_backend(data)
    
    if success:
        print("\n✅ BACKEND UPDATE COMPLETE")
        print("\n💡 Check your frontend to see the updated levels!")
    else:
        print("\n❌ Update failed. Check backend logs.")

if __name__ == "__main__":
    import os
    main()
