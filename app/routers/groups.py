import uuid
import logging

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas.group import GroupCreate, GroupMemberOut, GroupOut, SetGroupLeader
from app.services import group_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/groups", tags=["Groups"])


@router.get("", response_model=list[GroupOut])
async def list_groups(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List all groups."""
    return await group_service.list_groups(db, skip=skip, limit=limit)


@router.get("/{group_id}", response_model=GroupOut)
async def get_group(
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific group by ID."""
    return await group_service.get_group(db, group_id)


@router.post("", response_model=GroupOut, status_code=status.HTTP_201_CREATED)
async def create_group(
    payload: GroupCreate,
    user_id: uuid.UUID | None = Query(None, description="User creating the group"),
    db: AsyncSession = Depends(get_db),
):
    """Create a new group."""
    return await group_service.create_group(db, payload, created_by=user_id)


@router.post("/{group_id}/join", response_model=GroupMemberOut, status_code=status.HTTP_201_CREATED)
async def join_group(
    group_id: uuid.UUID,
    user_id: uuid.UUID = Query(..., description="User joining the group"),
    db: AsyncSession = Depends(get_db),
):
    """Join a group."""
    return await group_service.join_group(db, group_id, user_id)


@router.get("/{group_id}/members", response_model=list[GroupMemberOut])
async def list_group_members(
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """List all members of a group."""
    return await group_service.list_group_members(db, group_id)


@router.patch("/{group_id}/leader", response_model=GroupOut)
async def set_group_leader(
    group_id: uuid.UUID,
    payload: SetGroupLeader,
    db: AsyncSession = Depends(get_db),
):
    """Set the group leader for a group."""
    logger.info(f"PATCH /groups/{group_id}/leader endpoint called with payload: {payload}")
    result = await group_service.set_group_leader(db, group_id, payload.user_id)
    logger.info(f"Leader set successfully, returning result")
    return result
