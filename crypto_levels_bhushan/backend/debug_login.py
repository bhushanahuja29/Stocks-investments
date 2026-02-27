"""
Debug login issue
"""
from pymongo import MongoClient
from auth import verify_password
import os

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://bhushanstonks_db_user:61qQn4sCqnosMmuB@deltapricetracker.zzpfett.mongodb.net/?appName=DeltaPriceTracker")
DB_NAME = os.getenv("DB_NAME", "delta_tracker")

print("="*70)
print("Debugging Login Issue")
print("="*70)

try:
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    db = client[DB_NAME]
    
    # Find admin user
    user = db.users.find_one({"email": "Bhushan.stonks@gmail.com"})
    
    if user:
        print("\n✅ User found in database:")
        print(f"   Email: {user['email']}")
        print(f"   Name: {user['name']}")
        print(f"   Role: {user['role']}")
        print(f"   Has password: {bool(user.get('password'))}")
        
        # Test password verification
        print("\n🔐 Testing password verification:")
        stored_password = user['password']
        test_password = "BePatient"
        
        print(f"   Stored password hash: {stored_password[:50]}...")
        print(f"   Testing with: '{test_password}'")
        
        try:
            is_valid = verify_password(test_password, stored_password)
            print(f"   Password verification result: {is_valid}")
            
            if is_valid:
                print("\n✅ Password is CORRECT!")
            else:
                print("\n❌ Password is INCORRECT!")
                print("\n   This means the password in database doesn't match 'BePatient'")
                print("   Let's reset it...")
                
                from auth import hash_password
                new_hash = hash_password("BePatient")
                db.users.update_one(
                    {"email": "Bhushan.stonks@gmail.com"},
                    {"$set": {"password": new_hash}}
                )
                print("   ✅ Password reset to 'BePatient'")
                print("   Try logging in again!")
                
        except Exception as e:
            print(f"   ❌ Error verifying password: {e}")
    else:
        print("\n❌ User not found!")
    
    client.close()
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
