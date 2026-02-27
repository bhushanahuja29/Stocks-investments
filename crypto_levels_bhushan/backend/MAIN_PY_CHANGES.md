# Changes Required for main.py to Add Authentication

## 1. Update Imports (Lines 1-20)

Replace:
```python
from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
```

With:
```python
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
from bson import ObjectId
from pydantic import EmailStr

# Import auth modules
from auth import (
    authenticate_user, create_access_token, hash_password,
    is_subscription_active, calculate_subscription_end, get_days_remaining,
    create_admin_if_not_exists, verify_password, decode_access_token
)
```

## 2. Replace MongoDB Client (Lines 45-55)

Replace:
```python
# MongoDB client
mongo_client = None
db = None
collection = None

def get_mongo_connection():
    global mongo_client, db, collection
    if mongo_client is None:
        mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        db = mongo_client[DB_NAME]
        collection = db[COLLECTION_NAME]
    return collection
```

With:
```python
# MongoDB client (async)
motor_client = None
motor_db = None

security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global motor_client, motor_db
    motor_client = AsyncIOMotorClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    motor_db = motor_client[DB_NAME]
    
    await create_admin_if_not_exists(motor_db)
    print("✅ Database connected and admin user initialized")
    
    yield
    
    motor_client.close()
    print("✅ Database connection closed")

async def get_db():
    return motor_db

async def get_current_user(credentials = Depends(security), db = Depends(get_db)):
    """Get current authenticated user"""
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
    
    if user.get('role') != 'admin' and not is_subscription_active(user):
        raise HTTPException(
            status_code=403,
            detail="Your subscription has expired. Please contact admin on WhatsApp to renew."
        )
    
    return user

async def require_admin(current_user: dict = Depends(get_current_user)):
    """Require admin role"""
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
```

## 3. Update FastAPI App Initialization

Replace:
```python
app = FastAPI(title="Crypto Levels API", version="1.0.0")
```

With:
```python
app = FastAPI(
    title="Crypto Levels API with Authentication",
    version="2.0.0",
    lifespan=lifespan
)
```

## 4. Add Pydantic Models for Auth (After app initialization)

```python
# Auth models
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
```

## 5. Add Authentication Routes (Before existing routes)

See `auth_routes.py` and `admin_routes.py` - copy all route handlers into main.py

## 6. Protect Existing Routes

Add authentication to these routes:

```python
@app.post("/api/zones/search")
async def search_zones(
    request: ZoneSearchRequest,
    current_user: dict = Depends(get_current_user)  # ADD THIS
):
    # ... existing code

@app.post("/api/zones/push")
async def push_zones(
    request: PushZonesRequest,
    current_user: dict = Depends(get_current_user)  # ADD THIS
):
    # ... existing code

@app.get("/api/scrips")
async def get_all_scrips(
    current_user: dict = Depends(get_current_user)  # ADD THIS
):
    # ... existing code

@app.get("/api/price/{symbol}")
async def get_mark_price(
    symbol: str,
    market_type: Optional[str] = "crypto",
    current_user: dict = Depends(get_current_user)  # ADD THIS
):
    # ... existing code

@app.put("/api/scrips/{symbol}/alert")
async def update_alert_status(
    symbol: str,
    request: UpdateAlertRequest,
    current_user: dict = Depends(get_current_user)  # ADD THIS
):
    # ... existing code

@app.delete("/api/scrips/{symbol}")
async def delete_scrip(
    symbol: str,
    current_user: dict = Depends(get_current_user)  # ADD THIS
):
    # ... existing code
```

## 7. Update MongoDB Operations to Async

Replace all:
- `coll = get_mongo_connection()` with `db = await get_db()`
- `coll.find_one()` with `await db.monitored_scrips.find_one()`
- `coll.find()` with `await db.monitored_scrips.find().to_list(length=None)`
- `coll.update_one()` with `await db.monitored_scrips.update_one()`
- `coll.insert_one()` with `await db.monitored_scrips.insert_one()`
- `coll.delete_one()` with `await db.monitored_scrips.delete_one()`

And make all these functions `async def`

## Quick Integration Option

Instead of manual changes, you can:

1. Keep your current `main_backup.py` as reference
2. Copy the complete integrated version from `AUTHENTICATION_IMPLEMENTATION.md`
3. Merge your custom logic (forex, indian stocks) into the new version

## Testing

1. Start backend: `python main.py`
2. Test health: `http://localhost:8000/api/health`
3. Test login: POST to `http://localhost:8000/api/auth/login`
   ```json
   {
     "login_id": "Bhushan.stonks@gmail.com",
     "password": "BePatient"
   }
   ```
4. Use returned token in Authorization header: `Bearer <token>`
