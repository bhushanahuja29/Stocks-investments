"""
Admin User Management Routes
"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from datetime import datetime
from bson import ObjectId
from typing import Optional, List
from .auth import (
    hash_password, calculate_subscription_end, get_days_remaining
)
from .middleware import require_admin

router = APIRouter(prefix="/api/admin", tags=["Admin"])

class CreateUserRequest(BaseModel):
    email: EmailStr
    mobile: str
    password: str
    name: str
    subscription_type: str  # "monthly" or "quarterly"

class RenewSubscriptionRequest(BaseModel):
    subscription_type: str  # "monthly" or "quarterly"

class ChangeUserPasswordRequest(BaseModel):
    new_password: str

@router.get("/users")
async def get_all_users(current_user: dict = Depends(require_admin), db=None):
    """Get all users (admin only)"""
    users = await db.users.find({"role": {"$ne": "admin"}}).to_list(length=None)
    
    # Format user data
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
        
        # Calculate days remaining
        if user.get('subscription_end'):
            user_data['days_remaining'] = get_days_remaining(user['subscription_end'])
            user_data['subscription_status'] = 'active' if user_data['days_remaining'] > 0 else 'expired'
        else:
            user_data['days_remaining'] = 0
            user_data['subscription_status'] = 'inactive'
        
        user_list.append(user_data)
    
    return {
        "success": True,
        "users": user_list,
        "count": len(user_list)
    }

@router.post("/users")
async def create_user(
    request: CreateUserRequest,
    current_user: dict = Depends(require_admin),
    db=None
):
    """Create new user (admin only)"""
    # Check if user already exists
    existing = await db.users.find_one({
        "$or": [
            {"email": request.email},
            {"mobile": request.mobile}
        ]
    })
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or mobile already exists"
        )
    
    # Validate subscription type
    if request.subscription_type not in ['monthly', 'quarterly']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subscription type must be 'monthly' or 'quarterly'"
        )
    
    # Calculate subscription dates
    subscription_start = datetime.utcnow()
    subscription_end = calculate_subscription_end(request.subscription_type, subscription_start)
    
    # Create user
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

@router.put("/users/{user_id}/renew")
async def renew_subscription(
    user_id: str,
    request: RenewSubscriptionRequest,
    current_user: dict = Depends(require_admin),
    db=None
):
    """Renew user subscription (admin only)"""
    # Validate subscription type
    if request.subscription_type not in ['monthly', 'quarterly']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subscription type must be 'monthly' or 'quarterly'"
        )
    
    # Find user
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Calculate new subscription dates
    subscription_start = datetime.utcnow()
    subscription_end = calculate_subscription_end(request.subscription_type, subscription_start)
    
    # Update user
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

@router.put("/users/{user_id}/password")
async def change_user_password(
    user_id: str,
    request: ChangeUserPasswordRequest,
    current_user: dict = Depends(require_admin),
    db=None
):
    """Change user password (admin only)"""
    # Find user
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update password
    new_hashed = hash_password(request.new_password)
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"password": new_hashed, "updated_at": datetime.utcnow()}}
    )
    
    return {
        "success": True,
        "message": f"Password changed for {user['email']}"
    }

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(require_admin),
    db=None
):
    """Delete user (admin only)"""
    result = await db.users.delete_one({"_id": ObjectId(user_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "success": True,
        "message": "User deleted successfully"
    }
