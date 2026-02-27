"""
Script to integrate authentication into main.py
This will add authentication routes and protect existing endpoints
"""

# Read the original main.py
with open('main_backup.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update imports at the top
new_imports = """from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import os
import sys
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
import requests
from pathlib import Path
from bson import ObjectId

# Add parent directory to path to import v3
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Import v3 functions
from v3 import compute_zones_for_symbol, ts_str, fnum, is_green, is_red, body_size, START_YEAR_TS

# Import auth modules
from auth import (
    authenticate_user, create_access_token, hash_password,
    is_subscription_active, calculate_subscription_end, get_days_remaining,
    create_admin_if_not_exists, verify_password, decode_access_token
)
"""

# Replace old imports
old_imports_end = content.find('# Twelve Data API Configuration')
content = new_imports + '\n' + content[old_imports_end:]

# 2. Replace MongoDB client with Motor (async)
old_mongo = """# MongoDB client
mongo_client = None
db = None
collection = None

def get_mongo_connection():
    global mongo_client, db, collection
    if mongo_client is None:
        mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        db = mongo_client[DB_NAME]
        collection = db[COLLECTION_NAME]
    return collection"""

new_mongo = """# MongoDB client (async)
motor_client = None
motor_db = None

security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    \"\"\"Startup and shutdown events\"\"\"
    # Startup
    global motor_client, motor_db
    motor_client = AsyncIOMotorClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    motor_db = motor_client[DB_NAME]
    
    # Create admin user if doesn't exist
    await create_admin_if_not_exists(motor_db)
    
    print("✅ Database connected and admin user initialized")
    
    yield
    
    # Shutdown
    motor_client.close()
    print("✅ Database connection closed")

# Dependency to get database
async def get_db():
    return motor_db

# Middleware for authentication
async def get_current_user(credentials = Depends(security), db = Depends(get_db)):
    \"\"\"Get current authenticated user\"\"\"
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Check subscription for non-admin users
    if user.get('role') != 'admin' and not is_subscription_active(user):
        raise HTTPException(
            status_code=403,
            detail="Your subscription has expired. Please contact admin on WhatsApp to renew."
        )
    
    return user

async def require_admin(current_user: dict = Depends(get_current_user)):
    \"\"\"Require admin role\"\"\"
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user"""

content = content.replace(old_mongo, new_mongo)

# 3. Update FastAPI app initialization
old_app = 'app = FastAPI(title="Crypto Levels API", version="1.0.0")'
new_app = '''app = FastAPI(
    title="Crypto Levels API with Authentication",
    version="2.0.0",
    lifespan=lifespan
)'''

content = content.replace(old_app, new_app)

# 4. Add auth routes before existing routes
auth_routes_section = '''
# ====== AUTHENTICATION ROUTES ======

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
async def login(request: LoginRequest, db = Depends(get_db)):
    """Login with email or mobile number"""
    user = await authenticate_user(db, request.login_id, request.password)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if user.get('role') != 'admin' and not is_subscription_active(user):
        raise HTTPException(
            status_code=403,
            detail="Your subscription has expired. Please contact admin on WhatsApp to renew."
        )
    
    token = create_access_token({"user_id": str(user['_id']), "role": user.get('role', 'user')})
    
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

@app.get("/api/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info"""
    user_data = {
        "id": str(current_user['_id']),
        "email": current_user['email'],
        "mobile": current_user.get('mobile'),
        "name": current_user.get('name'),
        "role": current_user.get('role', 'user'),
        "subscription_type": current_user.get('subscription_type'),
        "subscription_end": current_user.get('subscription_end').isoformat() if current_user.get('subscription_end') else None,
        "is_active": current_user.get('is_active', False)
    }
    
    if current_user.get('role') != 'admin' and current_user.get('subscription_end'):
        user_data['days_remaining'] = get_days_remaining(current_user['subscription_end'])
    
    return {"success": True, "user": user_data}

@app.post("/api/auth/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Change own password"""
    if not verify_password(request.old_password, current_user['password']):
        raise HTTPException(status_code=400, detail="Incorrect old password")
    
    new_hashed = hash_password(request.new_password)
    await db.users.update_one(
        {"_id": current_user['_id']},
        {"$set": {"password": new_hashed, "updated_at": datetime.utcnow()}}
    )
    
    return {"success": True, "message": "Password changed successfully"}

@app.post("/api/auth/logout")
async def logout():
    """Logout"""
    return {"success": True, "message": "Logged out successfully"}

# ====== ADMIN ROUTES ======

@app.get("/api/admin/users")
async def get_all_users(current_user: dict = Depends(require_admin), db = Depends(get_db)):
    """Get all users (admin only)"""
    users = await db.users.find({"role": {"$ne": "admin"}}).to_list(length=None)
    
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

@app.post("/api/admin/users")
async def create_user(
    request: CreateUserRequest,
    current_user: dict = Depends(require_admin),
    db = Depends(get_db)
):
    """Create new user (admin only)"""
    existing = await db.users.find_one({"$or": [{"email": request.email}, {"mobile": request.mobile}]})
    
    if existing:
        raise HTTPException(status_code=400, detail="User with this email or mobile already exists")
    
    if request.subscription_type not in ['monthly', 'quarterly']:
        raise HTTPException(status_code=400, detail="Subscription type must be 'monthly' or 'quarterly'")
    
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
    
    result = await db.users.insert_one(user_data)
    
    return {
        "success": True,
        "message": f"User {request.email} created successfully",
        "user_id": str(result.inserted_id),
        "subscription_end": subscription_end.isoformat(),
        "days": 30 if request.subscription_type == 'monthly' else 90
    }

@app.put("/api/admin/users/{user_id}/renew")
async def renew_subscription(
    user_id: str,
    request: RenewSubscriptionRequest,
    current_user: dict = Depends(require_admin),
    db = Depends(get_db)
):
    """Renew user subscription (admin only)"""
    if request.subscription_type not in ['monthly', 'quarterly']:
        raise HTTPException(status_code=400, detail="Subscription type must be 'monthly' or 'quarterly'")
    
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    subscription_start = datetime.utcnow()
    subscription_end = calculate_subscription_end(request.subscription_type, subscription_start)
    
    await db.users.update_one(
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

@app.put("/api/admin/users/{user_id}/password")
async def change_user_password(
    user_id: str,
    request: ChangeUserPasswordRequest,
    current_user: dict = Depends(require_admin),
    db = Depends(get_db)
):
    """Change user password (admin only)"""
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_hashed = hash_password(request.new_password)
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"password": new_hashed, "updated_at": datetime.utcnow()}}
    )
    
    return {"success": True, "message": f"Password changed for {user['email']}"}

@app.delete("/api/admin/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(require_admin),
    db = Depends(get_db)
):
    """Delete user (admin only)"""
    result = await db.users.delete_one({"_id": ObjectId(user_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"success": True, "message": "User deleted successfully"}

# ====== END AUTHENTICATION ROUTES ======

'''

# Insert auth routes before the first @app route
first_route_pos = content.find('@app.get("/")')
content = content[:first_route_pos] + auth_routes_section + '\n' + content[first_route_pos:]

# 5. Protect existing routes by adding authentication
# Add current_user: dict = Depends(get_current_user) to protected routes
routes_to_protect = [
    '@app.post("/api/zones/search")',
    '@app.post("/api/zones/push")',
    '@app.get("/api/scrips")',
    '@app.get("/api/price/{symbol}")',
    '@app.put("/api/scrips/{symbol}/alert")',
    '@app.delete("/api/scrips/{symbol}")'
]

for route in routes_to_protect:
    if route in content:
        # Find the function definition
        route_pos = content.find(route)
        func_start = content.find('def ', route_pos)
        func_end = content.find('):', func_start)
        
        # Check if already has authentication
        func_def = content[func_start:func_end]
        if 'current_user' not in func_def:
            # Add authentication parameter
            content = content[:func_end] + ', current_user: dict = Depends(get_current_user)' + content[func_end:]

# Write the new main.py
with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Authentication integrated into main.py")
print("✅ Original file backed up as main_backup.py")
print("\nNext steps:")
print("1. Review the changes in main.py")
print("2. Start the backend: python main.py")
print("3. Test admin login: Bhushan.stonks@gmail.com / BePatient")
