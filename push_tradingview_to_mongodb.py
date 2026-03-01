"""
Push TradingView Levels to MongoDB
Automatically uploads scraped levels to the database
"""
import json
import os
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv('crypto_levels_bhushan/backend/.env')

# MongoDB Configuration
MONGODB_URI = os.getenv('MONGODB_URI')
DB_NAME = os.getenv('DB_NAME', 'delta_tracker')
COLLECTION_NAME = os.getenv('COLLECTION_NAME', 'monitored_scrips')


def connect_to_mongodb():
    """Connect to MongoDB"""
    try:
        client = MongoClient(MONGODB_URI, tls=True, tlsAllowInvalidCertificates=True)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        
        # Test connection
        client.server_info()
        print(f"✅ Connected to MongoDB: {DB_NAME}.{COLLECTION_NAME}")
        return collection
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return None


def load_tradingview_data(filename='tradingview_levels_20260301_203813.json'):
    """Load TradingView JSON data"""
    if not os.path.exists(filename):
        print(f"❌ File not found: {filename}")
        return None
    
    with open(filename, 'r') as f:
        data = json.load(f)
    
    print(f"✅ Loaded {len(data)} stocks from {filename}")
    return data


def convert_to_mongodb_format(stock_data):
    """Convert TradingView data to MongoDB document format"""
    symbol = stock_data.get('symbol')
    support_levels = stock_data.get('support_levels', [])
    resistance_levels = stock_data.get('resistance_levels', [])
    
    # Combine support and resistance levels
    all_levels = support_levels + resistance_levels
    
    if not all_levels:
        return None
    
    # Create trigger_levels array
    trigger_levels = []
    for idx, level in enumerate(all_levels):
        trigger_level = {
            'trigger_price': level,
            'bottom': level,
            'rally_end_high': level,
            'small_red_time': None,
            'rally_length': 0,
            'total_move_pct': 0,
            'zone_index': idx,
            'triggered': False,
            'alert_disabled': False,
            'last_checked': None,
            'timeframe': '1W'
        }
        trigger_levels.append(trigger_level)
    
    # Create MongoDB document
    timestamp = stock_data.get('timestamp', datetime.now().isoformat())
    
    document = {
        'symbol': symbol,
        'timeframe': '1W',
        'interval': '60',
        'device_id': 'web_app',
        'active': True,
        'last_updated': timestamp,
        'source': 'tradingview_weekly_ocr',
        'monitoring_type': 'multi_level',
        'market_type': 'indian_stock',
        'exchange': stock_data.get('exchange', 'NSE'),
        'trigger_levels': trigger_levels
    }
    
    return document


def push_to_mongodb(collection, tv_data):
    """Push all stocks to MongoDB"""
    results = {
        'inserted': 0,
        'updated': 0,
        'failed': 0,
        'skipped': 0
    }
    
    for stock_data in tv_data:
        symbol = stock_data.get('symbol')
        
        # Convert to MongoDB format
        document = convert_to_mongodb_format(stock_data)
        
        if not document:
            print(f"⚠️  {symbol}: No levels found, skipping")
            results['skipped'] += 1
            continue
        
        try:
            # Check if document already exists
            existing = collection.find_one({
                'symbol': symbol,
                'market_type': 'indian_stock',
                'timeframe': '1W'
            })
            
            if existing:
                # Update existing document
                result = collection.update_one(
                    {'_id': existing['_id']},
                    {'$set': document}
                )
                
                if result.modified_count > 0:
                    print(f"✅ {symbol}: Updated {len(document['trigger_levels'])} levels")
                    results['updated'] += 1
                else:
                    print(f"ℹ️  {symbol}: No changes needed")
                    results['skipped'] += 1
            else:
                # Insert new document
                collection.insert_one(document)
                print(f"✅ {symbol}: Inserted {len(document['trigger_levels'])} levels")
                results['inserted'] += 1
                
        except Exception as e:
            print(f"❌ {symbol}: Failed - {e}")
            results['failed'] += 1
    
    return results


def verify_data(collection):
    """Verify the pushed data"""
    print("\n" + "="*60)
    print("🔍 Verifying Data in MongoDB")
    print("="*60)
    
    # Count Indian stock documents
    count = collection.count_documents({'market_type': 'indian_stock'})
    print(f"\nTotal Indian Stock documents: {count}")
    
    # Show sample documents
    print("\nSample documents:")
    for doc in collection.find({'market_type': 'indian_stock'}).limit(3):
        print(f"\n{doc['symbol']}:")
        print(f"  Timeframe: {doc['timeframe']}")
        print(f"  Levels: {len(doc['trigger_levels'])}")
        print(f"  Source: {doc['source']}")
        print(f"  Last Updated: {doc['last_updated']}")
        
        # Show first 3 levels
        if doc['trigger_levels']:
            print(f"  Sample Levels:")
            for level in doc['trigger_levels'][:3]:
                print(f"    - {level['trigger_price']}")


def main():
    """Main execution"""
    print("""
╔══════════════════════════════════════════════════════════╗
║   Push TradingView Levels to MongoDB                     ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    # Connect to MongoDB
    collection = connect_to_mongodb()
    if collection is None:
        return
    
    # Load TradingView data
    tv_data = load_tradingview_data()
    if tv_data is None:
        return
    
    print("\n" + "="*60)
    print("📤 Pushing Data to MongoDB")
    print("="*60 + "\n")
    
    # Push to MongoDB
    results = push_to_mongodb(collection, tv_data)
    
    # Print summary
    print("\n" + "="*60)
    print("📊 Push Summary")
    print("="*60)
    print(f"✅ Inserted: {results['inserted']}")
    print(f"🔄 Updated: {results['updated']}")
    print(f"⚠️  Skipped: {results['skipped']}")
    print(f"❌ Failed: {results['failed']}")
    print(f"📈 Total Processed: {sum(results.values())}")
    
    # Verify data
    verify_data(collection)
    
    print("\n" + "="*60)
    print("✅ Push Complete!")
    print("="*60)
    print("""
Next Steps:
1. Open frontend: http://localhost:3000
2. Go to Monitor page
3. Select "Indian Stocks" from market type dropdown
4. Click "All" tab to see all stocks
5. Verify levels are visible for:
   - BHARTIARTL
   - HDFCBANK
   - ICICIBANK
   - RELIANCE
   - SBIN
    """)


if __name__ == "__main__":
    main()
