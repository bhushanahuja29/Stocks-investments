"""
Script to add authentication routes to main.py
Run this to integrate authentication into your existing main.py
"""
import re

print("="*70)
print("Adding Authentication Routes to main.py")
print("="*70)

# Read current main.py
with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Check if already has auth routes
if '@app.post("/api/auth/login")' in content:
    print("\n⚠️ Authentication routes already exist in main.py")
    print("Skipping integration.")
    exit(0)

# Find where to insert auth routes (after the health check route)
health_check_pos = content.find('@app.get("/api/health")')
if health_check_pos == -1:
    print("\n❌ Could not find health check route in main.py")
    print("Please check your main.py file structure")
    exit(1)

# Find the end of health check function
next_route_pos = content.find('\n@app.', health_check_pos + 1)
if next_route_pos == -1:
    next_route_pos = content.find('\nif __name__', health_check_pos)

# Auth routes to insert
auth_routes = '''

# ====== AUTHENTICATION ROUTES ======

from pydantic import EmailStr
from bson import ObjectId
from auth import (
    authenticate_user, create_access_token, hash_password,
    is_subscription_active, calculate_subscription_end, get_days_remaining,
    verify_password
)

class LoginRequest(BaseModel):
    login_id: str
    password: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class CreateUserRequest(BaseModel):
    email: EmailStr
    mobile: str
    password: str
    name: str
    subscription_type: str

class RenewSubscriptionRequest(BaseModel):
    subscription_type: str

class ChangeUserPasswordRequest(BaseModel):
    new_password: str

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """Login with email or mobile number"""
    try:
        # Get MongoDB connection
        coll = get_mongo_connection()
        
        # Find user by email or mobile
        user = coll.find_one({
            "$or": [
                {"email": request.login_id},
                {"mobile": request.login_id}
            ]
        })
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Verify password
        from auth import verify_password
        if not verify_password(request.password, user['password']):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Check subscription for non-admin
        if user.get('role') != 'admin':
            from auth import is_subscription_active
            if not is_subscription_active(user):
                raise HTTPException(
                    status_code=403,
                    detail="Your subscription has expired. Please contact admin on WhatsApp to renew."
                )
        
        # Create token
        from auth import create_access_token
        token = create_access_token({"user_id": str(user['_id']), "role": user.get('role', 'user')})
        
        # Prepare user data
        from auth import get_days_remaining
        user_data = {
            "id": str(user['_id']),
            "email": user['email'],
            "mobile": user.get('mobile'),
            "name": user.get('name'),
            "role": user.get('role', 'user'),
            "subscription_type": user.get('subscription_type'),
            "subscription_end": user.get('subscription_end').isoformat() if user.get('subscription_end') else None,
            "is_active": user.get('is_active', False)
        }
        
        if user.get('role') != 'admin' and user.get('subscription_end'):
            user_data['days_remaining'] = get_days_remaining(user['subscription_end'])
        
        return {"success": True, "token": token, "user": user_data}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/users")
async def get_all_users():
    """Get all users (admin only) - TODO: Add auth middleware"""
    try:
        coll = get_mongo_connection()
        db = coll.database
        
        users = list(db.users.find({"role": {"$ne": "admin"}}))
        
        from auth import get_days_remaining
        user_list = []
        for user in users:
            user_data = {
                "id": str(user['_id']),
                "email": user['email'],
                "mobile": user.get('mobile'),
                "name": user.get('name'),
                "subscription_type": user.get('subscription_type'),
                "subscription_start": user.get('subscription_start').isoformat() if user.get('subscription_start') else None,
                "subscription_end": user.get('subscription_end').isoformat() if user.get('subscription_end') else None,
                "is_active": user.get('is_active', False),
                "created_at": user.get('created_at').isoformat() if user.get('created_at') else None
            }
            
            if user.get('subscription_end'):
                user_data['days_remaining'] = get_days_remaining(user['subscription_end'])
                user_data['subscription_status'] = 'active' if user_data['days_remaining'] > 0 else 'expired'
            else:
                user_data['days_remaining'] = 0
                user_data['subscription_status'] = 'inactive'
            
            user_list.append(user_data)
        
        return {"success": True, "users": user_list, "count": len(user_list)}
    except Exception as e:
        print(f"Get users error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/users")
async def create_user(request: CreateUserRequest):
    """Create new user (admin only) - TODO: Add auth middleware"""
    try:
        coll = get_mongo_connection()
        db = coll.database
        
        # Check if exists
        existing = db.users.find_one({"$or": [{"email": request.email}, {"mobile": request.mobile}]})
        if existing:
            raise HTTPException(status_code=400, detail="User with this email or mobile already exists")
        
        if request.subscription_type not in ['monthly', 'quarterly']:
            raise HTTPException(status_code=400, detail="Subscription type must be 'monthly' or 'quarterly'")
        
        from datetime import datetime
        from auth import hash_password, calculate_subscription_end
        
        subscription_start = datetime.utcnow()
        subscription_end = calculate_subscription_end(request.subscription_type, subscription_start)
        
        user_data = {
            "email": request.email,
            "mobile": request.mobile,
            "password": hash_password(request.password),
            "name": request.name,
            "role": "user",
            "subscription_type": request.subscription_type,
            "subscription_start": subscription_start,
            "subscription_end": subscription_end,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = db.users.insert_one(user_data)
        
        return {
            "success": True,
            "message": f"User {request.email} created successfully",
            "user_id": str(result.inserted_id),
            "subscription_end": subscription_end.isoformat(),
            "days": 30 if request.subscription_type == 'monthly' else 90
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Create user error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/admin/users/{user_id}/renew")
async def renew_subscription(user_id: str, request: RenewSubscriptionRequest):
    """Renew user subscription (admin only) - TODO: Add auth middleware"""
    try:
        if request.subscription_type not in ['monthly', 'quarterly']:
            raise HTTPException(status_code=400, detail="Subscription type must be 'monthly' or 'quarterly'")
        
        coll = get_mongo_connection()
        db = coll.database
        
        from bson import ObjectId
        user = db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        from datetime import datetime
        from auth import calculate_subscription_end
        
        subscription_start = datetime.utcnow()
        subscription_end = calculate_subscription_end(request.subscription_type, subscription_start)
        
        db.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "subscription_type": request.subscription_type,
                    "subscription_start": subscription_start,
                    "subscription_end": subscription_end,
                    "is_active": True,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return {
            "success": True,
            "message": f"Subscription renewed for {user['email']}",
            "subscription_type": request.subscription_type,
            "subscription_end": subscription_end.isoformat(),
            "days": 30 if request.subscription_type == 'monthly' else 90
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Renew subscription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/admin/users/{user_id}/password")
async def change_user_password(user_id: str, request: ChangeUserPasswordRequest):
    """Change user password (admin only) - TODO: Add auth middleware"""
    try:
        coll = get_mongo_connection()
        db = coll.database
        
        from bson import ObjectId
        user = db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        from datetime import datetime
        from auth import hash_password
        
        new_hashed = hash_password(request.new_password)
        db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"password": new_hashed, "updated_at": datetime.utcnow()}}
        )
        
        return {"success": True, "message": f"Password changed for {user['email']}"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Change password error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/admin/users/{user_id}")
async def delete_user(user_id: str):
    """Delete user (admin only) - TODO: Add auth middleware"""
    try:
        coll = get_mongo_connection()
        db = coll.database
        
        from bson import ObjectId
        result = db.users.delete_one({"_id": ObjectId(user_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"success": True, "message": "User deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Delete user error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ====== END AUTHENTICATION ROUTES ======

'''

# Insert auth routes
new_content = content[:next_route_pos] + auth_routes + content[next_route_pos:]

# Write back
with open('main.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("\n✅ Authentication routes added to main.py")
print("\n📝 Added routes:")
print("   - POST /api/auth/login")
print("   - GET /api/admin/users")
print("   - POST /api/admin/users")
print("   - PUT /api/admin/users/:id/renew")
print("   - PUT /api/admin/users/:id/password")
print("   - DELETE /api/admin/users/:id")
print("\n⚠️ Note: Admin routes don't have auth middleware yet")
print("   They will work but are not protected")
print("\n🔄 Restart your backend to apply changes:")
print("   python main.py")
print("\n✅ Done!")
