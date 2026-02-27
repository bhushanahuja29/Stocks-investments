"""
Migrate MongoDB data from old cluster to new cluster
"""
from pymongo import MongoClient
from datetime import datetime

# Old MongoDB URI
OLD_URI = "mongodb+srv://bhushanstonks_db_user:61qQn4sCqnosMmuB@deltapricetracker.zzpfett.mongodb.net/?appName=DeltaPriceTracker"

# New MongoDB URI
NEW_URI = "mongodb+srv://bhushanstonks_db_user:61qQn4sCqnosMmuB@deltapricetracker.zzpfett.mongodb.net/?appName=DeltaPriceTracker"

DB_NAME = "delta_tracker"

print("="*70)
print("MongoDB Data Migration")
print("="*70)

try:
    # Connect to old database
    print("\n1. Connecting to OLD database...")
    old_client = MongoClient(OLD_URI, serverSelectionTimeoutMS=5000)
    old_db = old_client[DB_NAME]
    print("   ✅ Connected to old database")
    
    # Connect to new database
    print("\n2. Connecting to NEW database...")
    new_client = MongoClient(NEW_URI, serverSelectionTimeoutMS=5000)
    new_db = new_client[DB_NAME]
    print("   ✅ Connected to new database")
    
    # Get all collections from old database
    print("\n3. Getting collections from old database...")
    collections = old_db.list_collection_names()
    print(f"   Found {len(collections)} collections: {collections}")
    
    # Migrate each collection
    print("\n4. Migrating data...")
    for collection_name in collections:
        print(f"\n   📦 Migrating collection: {collection_name}")
        
        # Get all documents from old collection
        old_collection = old_db[collection_name]
        documents = list(old_collection.find())
        
        if not documents:
            print(f"      ⚠️ No documents found in {collection_name}")
            continue
        
        print(f"      Found {len(documents)} documents")
        
        # Insert into new collection
        new_collection = new_db[collection_name]
        
        # Clear existing data in new collection (optional)
        existing_count = new_collection.count_documents({})
        if existing_count > 0:
            print(f"      ⚠️ New collection already has {existing_count} documents")
            response = input(f"      Delete existing data in {collection_name}? (yes/no): ")
            if response.lower() == 'yes':
                new_collection.delete_many({})
                print(f"      🗑️ Deleted {existing_count} existing documents")
        
        # Insert documents
        if documents:
            result = new_collection.insert_many(documents)
            print(f"      ✅ Inserted {len(result.inserted_ids)} documents")
    
    # Verify migration
    print("\n5. Verifying migration...")
    for collection_name in collections:
        old_count = old_db[collection_name].count_documents({})
        new_count = new_db[collection_name].count_documents({})
        
        status = "✅" if old_count == new_count else "⚠️"
        print(f"   {status} {collection_name}: {old_count} (old) -> {new_count} (new)")
    
    # Close connections
    old_client.close()
    new_client.close()
    
    print("\n" + "="*70)
    print("✅ Migration Complete!")
    print("="*70)
    print("\nNext steps:")
    print("1. Update .env file with new MongoDB URI")
    print("2. Update main.py with new MongoDB URI")
    print("3. Restart backend")
    print("\n" + "="*70)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
