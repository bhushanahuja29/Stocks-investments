"""Quick verification of Indian stocks in MongoDB"""
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv('crypto_levels_bhushan/backend/.env')

client = MongoClient(os.getenv('MONGODB_URI'), tls=True, tlsAllowInvalidCertificates=True)
db = client[os.getenv('DB_NAME')]
coll = db[os.getenv('COLLECTION_NAME')]

print("="*60)
print("Indian Stocks in MongoDB")
print("="*60)

stocks = list(coll.find({'market_type': 'indian_stock'}))
print(f"\nTotal: {len(stocks)} stocks\n")

for stock in stocks:
    print(f"✅ {stock['symbol']}")
    print(f"   Levels: {len(stock['trigger_levels'])}")
    print(f"   Timeframe: {stock['timeframe']}")
    print(f"   Active: {stock['active']}")
    print(f"   Source: {stock['source']}")
    print()

print("="*60)
print("All Market Types in DB:")
print("="*60)
all_scrips = list(coll.find({'active': True}))
market_types = {}
for scrip in all_scrips:
    mt = scrip.get('market_type', 'unknown')
    if mt not in market_types:
        market_types[mt] = []
    market_types[mt].append(scrip['symbol'])

for mt, symbols in market_types.items():
    print(f"\n{mt}: {len(symbols)} scrips")
    for sym in symbols:
        print(f"  - {sym}")
