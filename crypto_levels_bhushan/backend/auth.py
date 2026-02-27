"""
Authentication and User Management
"""
from datetime import datetime, timedelta
from typing import Optional
import bcrypt
import jwt
from bson import ObjectId

SECRET_KEY = "your-secret-key-change-in-production"  # Change this!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> Optional[dict]:
    """Decode JWT access token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None

def is_subscription_active(user: dict) -> bool:
    """Check if user's subscription is active"""
    if user.get('role') == 'admin':
        return True
    
    if not user.get('subscription_end'):
        return False
    
    subscription_end = user['subscription_end']
    if isinstance(subscription_end, str):
        subscription_end = datetime.fromisoformat(subscription_end.replace('Z', '+00:00'))
    
    return datetime.utcnow() < subscription_end and user.get('is_active', False)

def calculate_subscription_end(subscription_type: str, start_date: datetime = None) -> datetime:
    """Calculate subscription end date"""
    if start_date is None:
        start_date = datetime.utcnow()
    
    if subscription_type == 'monthly':
        return start_date + timedelta(days=30)
    elif subscription_type == 'quarterly':
        return start_date + timedelta(days=90)
    else:
        raise ValueError("Invalid subscription type")

def get_days_remaining(subscription_end: datetime) -> int:
    """Get days remaining in subscription"""
    if isinstance(subscription_end, str):
        subscription_end = datetime.fromisoformat(subscription_end.replace('Z', '+00:00'))
    
    delta = subscription_end - datetime.utcnow()
    return max(0, delta.days)

async def authenticate_user(db, login_id: str, password: str):
    """Authenticate user by email or mobile"""
    # Try to find user by email or mobile
    user = await db.users.find_one({
        "$or": [
            {"email": login_id},
            {"mobile": login_id}
        ]
    })
    
    if not user:
        return None
    
    if not verify_password(password, user['password']):
        return None
    
    return user

async def create_admin_if_not_exists(db):
    """Create admin user if doesn't exist"""
    admin = await db.users.find_one({"email": "Bhushan.stonks@gmail.com"})
    
    if not admin:
        admin_user = {
            "email": "Bhushan.stonks@gmail.com",
            "mobile": "9999999999",  # Update with actual mobile
            "password": hash_password("BePatient"),
            "role": "admin",
            "name": "Bhushan",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        await db.users.insert_one(admin_user)
        print("✅ Admin user created")
