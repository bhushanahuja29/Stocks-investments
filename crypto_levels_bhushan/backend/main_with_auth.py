"""
FastAPI Backend for Crypto Levels Bhushan - WITH AUTHENTICATION
Provides APIs for support zone finding and monitoring
"""
from fastapi import FastAPI, HTTPException, Depends
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

# Twelve Data API Configuration
TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY", "b455fff947db40efb714b37b4873b135")

# API call tracking
api_call_count = 0
last_api_reset = datetime.now(timezone.utc).date()
forex_price_cache = {}
FOREX_PRICE_CACHE_DURATION = 180

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://bhushanstonks_db_user:61qQn4sCqnosMmuB@deltapricetracker.zzpfett.mongodb.net/?appName=DeltaPriceTracker")
DB_NAME = os.getenv("DB_NAME", "delta_tracker")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "monitored_scrips")

# MongoDB client (async)
motor_client = None
motor_db = None

security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
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

app = FastAPI(
    title="Crypto Levels API with Authentication",
    version="2.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get database
async def get_db():
    return motor_db

# Middleware for authentication
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
    
    # Check subscription for non-admin users
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

# ====== API CALL TRACKING ======

def increment_api_calls(count=1):
    global api_call_count, last_api_reset
    today = datetime.now(timezone.utc).date()
    if today > last_api_reset:
        api_call_count = 0
        last_api_reset = today
    api_call_count += count
    print(f"[API USAGE] {api_call_count}/800 calls today")
    return api_call_count

def get_api_usage():
    global api_call_count, last_api_reset
    today = datetime.now(timezone.utc).date()
    if today > last_api_reset:
        api_call_count = 0
        last_api_reset = today
    return {
        "used": api_call_count,
        "limit": 800,
        "remaining": 800 - api_call_count,
        "reset_date": last_api_reset.isoformat()
    }

def get_cached_forex_price(symbol: str):
    if symbol in forex_price_cache:
        cached = forex_price_cache[symbol]
        age = (datetime.now(timezone.utc) - cached["timestamp"]).total_seconds()
        if age < FOREX_PRICE_CACHE_DURATION:
            print(f"[CACHE HIT] {symbol}: ${cached['price']:.2f} (age: {age:.0f}s)")
            return cached["price"]
    return None

def cache_forex_price(symbol: str, price: float):
    forex_price_cache[symbol] = {
        "price": price,
        "timestamp": datetime.now(timezone.utc)
    }
    print(f"[CACHE SET] {symbol}: ${price:.2f}")

# ====== TWELVE DATA FUNCTIONS ======
# (Keep all existing functions: fetch_twelve_data, week_start_ts, resample functions, etc.)
