"""
Create admin user in MongoDB
Run this once to create the admin account
"""
from pymongo import MongoClient
from datetime import datetime
import os

# Import auth functions
from auth import hash_password

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://bhushanstonks_db_user:61qQn4sCqnosMmuB@deltapricetracker.zzpfett.mongodb.net/?appName=DeltaPriceTracker")
DB_NAME = os.getenv("DB_NAME", "delta_tracker")

print("="*70)
print("Creating Admin User")
print("="*70)

try:
    # Connect to MongoDB
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    db = client[DB_NAME]
    
    # Check if admin already exists
    existing_admin = db.users.find_one({"email": "Bhushan.stonks@gmail.com"})
    
    if existing_admin:
        print("\n⚠️ Admin user already exists!")
        print(f"   Email: {existing_admin['email']}")
        print(f"   Role: {existing_admin.get('role', 'N/A')}")
        print("\nIf you want to reset the password, delete the user first.")
    else:
        # Create admin user
        admin_user = {
            "email": "Bhushan.stonks@gmail.com",
            "mobile": "9999999999",  # Update with actual mobile if needed
            "password": hash_password("BePatient"),
            "name": "Bhushan",
            "role": "admin",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = db.users.insert_one(admin_user)
        
        print("\n✅ Admin user created successfully!")
        print(f"   User ID: {result.inserted_id}")
        print(f"   Email: Bhushan.stonks@gmail.com")
        print(f"   Password: BePatient")
        print(f"   Role: admin")
        print("\n🔐 You can now login with these credentials")
    
    client.close()
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nPlease check:")
    print("1. MongoDB connection string is correct")
    print("2. Network connection is available")
    print("3. auth.py file exists in the same directory")

print("\n" + "="*70)
