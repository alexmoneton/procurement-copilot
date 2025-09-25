"""API endpoints for saved filters management."""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.logging import logger
from ....db.crud import SavedFilterCRUD, UserCRUD
from ....db.schemas import SavedFilter, SavedFilterCreate, SavedFilterUpdate
from ....db.session import get_db

router = APIRouter()


async def get_current_user_email(
    x_user_email: Optional[str] = Header(None, alias="X-User-Email")
) -> str:
    """Get current user email from header and ensure user exists."""
    if not x_user_email:
        raise HTTPException(status_code=401, detail="X-User-Email header required")

    return x_user_email


async def ensure_user_exists(db: AsyncSession, email: str) -> uuid.UUID:
    """Ensure user exists in database, create if not."""
    user = await UserCRUD.get_by_email(db, email)
    if not user:
        from ...db.schemas import UserCreate

        user = await UserCRUD.create(db, UserCreate(email=email))
        logger.info(f"Created new user: {email}")

    return user.id


@router.get("/", response_model=List[SavedFilter])
async def get_saved_filters(
    db: AsyncSession = Depends(get_db),
    user_email: str = Depends(get_current_user_email),
):
    """Get all saved filters for the current user."""
    user_id = await ensure_user_exists(db, user_email)
    filters = await SavedFilterCRUD.get_by_user(db, user_id)
    return filters


@router.post("/", response_model=SavedFilter)
async def create_saved_filter(
    filter_data: SavedFilterCreate,
    db: AsyncSession = Depends(get_db),
    user_email: str = Depends(get_current_user_email),
):
    """Create a new saved filter for the current user."""
    user_id = await ensure_user_exists(db, user_email)

    # Check if user already has a filter with this name
    existing_filters = await SavedFilterCRUD.get_by_user(db, user_id)
    if any(f.name == filter_data.name for f in existing_filters):
        raise HTTPException(
            status_code=400,
            detail=f"Filter with name '{filter_data.name}' already exists",
        )

    saved_filter = await SavedFilterCRUD.create(db, filter_data, user_id)
    logger.info(f"Created filter '{filter_data.name}' for user {user_email}")
    return saved_filter


@router.get("/{filter_id}", response_model=SavedFilter)
async def get_saved_filter(
    filter_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_email: str = Depends(get_current_user_email),
):
    """Get a specific saved filter by ID."""
    user_id = await ensure_user_exists(db, user_email)
    saved_filter = await SavedFilterCRUD.get_by_id(db, filter_id)

    if not saved_filter:
        raise HTTPException(status_code=404, detail="Filter not found")

    if saved_filter.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return saved_filter


@router.patch("/{filter_id}", response_model=SavedFilter)
async def update_saved_filter(
    filter_id: uuid.UUID,
    filter_data: SavedFilterUpdate,
    db: AsyncSession = Depends(get_db),
    user_email: str = Depends(get_current_user_email),
):
    """Update a saved filter."""
    user_id = await ensure_user_exists(db, user_email)
    saved_filter = await SavedFilterCRUD.get_by_id(db, filter_id)

    if not saved_filter:
        raise HTTPException(status_code=404, detail="Filter not found")

    if saved_filter.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Check name uniqueness if name is being updated
    if filter_data.name and filter_data.name != saved_filter.name:
        existing_filters = await SavedFilterCRUD.get_by_user(db, user_id)
        if any(
            f.name == filter_data.name and f.id != filter_id for f in existing_filters
        ):
            raise HTTPException(
                status_code=400,
                detail=f"Filter with name '{filter_data.name}' already exists",
            )

    updated_filter = await SavedFilterCRUD.update(db, filter_id, filter_data)
    logger.info(f"Updated filter '{updated_filter.name}' for user {user_email}")
    return updated_filter


@router.delete("/{filter_id}")
async def delete_saved_filter(
    filter_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_email: str = Depends(get_current_user_email),
):
    """Delete a saved filter."""
    user_id = await ensure_user_exists(db, user_email)
    saved_filter = await SavedFilterCRUD.get_by_id(db, filter_id)

    if not saved_filter:
        raise HTTPException(status_code=404, detail="Filter not found")

    if saved_filter.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    success = await SavedFilterCRUD.delete(db, filter_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete filter")

    logger.info(f"Deleted filter '{saved_filter.name}' for user {user_email}")
    return {"message": "Filter deleted successfully"}
