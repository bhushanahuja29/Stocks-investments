"""
Authentication Routes
"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from datetime import datetime
from bson import ObjectId
from typing import Optional
from .auth import (
    authenticate_user, create_access_token, hash_password,
    is_subscription_active, calculate_subscription_end, get_days_remaining,
    create_admin_if_not_exists
)
from .middleware import get_current_user, require_admin

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    login_id: str  # Email or mobile
    password: str

class LoginResponse(BaseModel):
    success: bool
    token: str
    user: dict

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db=None):
    """Login with email or mobile number"""
    user = await authenticate_user(db, request.login_id, request.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Check subscription for non-admin users
    if user.get('role') != 'admin' and not is_subscription_active(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your subscription has expired. Please contact admin on WhatsApp to renew."
        )
    
    # Create access token
    token = create_access_token({"user_id": str(user['_id']), "role": user.get('role', 'user')})
    
    # Prepare user data (remove password)
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
    
    return {
        "success": True,
        "token": token,
        "user": user_data
    }

@router.get("/me")
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
    
    return {
        "success": True,
        "user": user_data
    }

@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    db=None
):
    """Change own password"""
    from .auth import verify_password
    
    # Verify old password
    if not verify_password(request.old_password, current_user['password']):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password"
        )
    
    # Update password
    new_hashed = hash_password(request.new_password)
    await db.users.update_one(
        {"_id": current_user['_id']},
        {"$set": {"password": new_hashed, "updated_at": datetime.utcnow()}}
    )
    
    return {
        "success": True,
        "message": "Password changed successfully"
    }

@router.post("/logout")
async def logout():
    """Logout (client should delete token)"""
    return {
        "success": True,
        "message": "Logged out successfully"
    }
