"""User profile endpoints."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession

from ....db.crud import UserCRUD, UserProfileCRUD
from ....db.schemas import UserProfile, UserProfileCreate, UserProfileUpdate
from ....db.session import get_db

router = APIRouter()


async def get_current_user_email(
    x_user_email: Optional[str] = Header(None, alias="X-User-Email")
) -> str:
    """Get current user email from header."""
    if not x_user_email:
        raise HTTPException(status_code=401, detail="User email required")
    return x_user_email


async def ensure_user_exists(db: AsyncSession, email: str) -> uuid.UUID:
    """Ensure user exists and return user ID."""
    user = await UserCRUD.get_by_email(db, email)
    if not user:
        # Create user if doesn't exist
        from ....db.schemas import UserCreate
        user = await UserCRUD.create(db, UserCreate(email=email))
    return user.id


@router.get("/profile", response_model=UserProfile)
async def get_user_profile(
    db: AsyncSession = Depends(get_db),
    user_email: str = Depends(get_current_user_email)
):
    """Get current user's profile."""
    user_id = await ensure_user_exists(db, user_email)
    profile = await UserProfileCRUD.get_by_user_id(db, user_id)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return profile


@router.post("/profile", response_model=UserProfile)
async def create_user_profile(
    profile_data: UserProfileCreate,
    db: AsyncSession = Depends(get_db),
    user_email: str = Depends(get_current_user_email)
):
    """Create or update user profile."""
    user_id = await ensure_user_exists(db, user_email)
    profile = await UserProfileCRUD.upsert(db, user_id, profile_data)
    return profile


@router.patch("/profile", response_model=UserProfile)
async def update_user_profile(
    profile_data: UserProfileUpdate,
    db: AsyncSession = Depends(get_db),
    user_email: str = Depends(get_current_user_email)
):
    """Update user profile."""
    user_id = await ensure_user_exists(db, user_email)
    profile = await UserProfileCRUD.update(db, user_id, profile_data)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return profile


@router.delete("/profile")
async def delete_user_profile(
    db: AsyncSession = Depends(get_db),
    user_email: str = Depends(get_current_user_email)
):
    """Delete user profile."""
    user_id = await ensure_user_exists(db, user_email)
    success = await UserProfileCRUD.delete(db, user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return {"message": "Profile deleted successfully"}
