import uuid
from typing import Sequence
import logging

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.group import Group, GroupMember
from app.models.user import User
from app.schemas.group import GroupCreate

logger = logging.getLogger(__name__)


async def list_groups(db: AsyncSession, skip: int = 0, limit: int = 50) -> Sequence[Group]:
    """List all groups with pagination."""
    result = await db.execute(
        select(Group)
        .options(selectinload(Group.group_leader))
        .offset(skip)
        .limit(limit)
        .order_by(Group.created_at.desc())
    )
    return result.scalars().all()


async def get_group(db: AsyncSession, group_id: uuid.UUID) -> Group:
    """Get a group by ID."""
    result = await db.execute(
        select(Group)
        .options(selectinload(Group.group_leader))
        .where(Group.id == group_id)
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    return group


async def create_group(
    db: AsyncSession, payload: GroupCreate, created_by: uuid.UUID | None = None
) -> Group:
    """Create a new group."""
    group = Group(
        name=payload.name,
        group_leader_id=payload.group_leader_id,
        created_by=created_by,
    )
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


async def join_group(
    db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID
) -> GroupMember:
    """Add a user to a group."""
    logger.info(f"join_group called with group_id={group_id}, user_id={user_id}")
    
    # Verify group exists
    await get_group(db, group_id)
    
    # Get user and check if already assigned to a team
    user_result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.assigned_team:
        logger.warning(f"User {user_id} already assigned to a team")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already assigned to a team"
        )
    
    # Check if already a member of this specific group
    existing = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this group"
        )
    
    # Add member and set assigned_team flag
    member = GroupMember(group_id=group_id, user_id=user_id)
    user.assigned_team = True
    db.add(member)
    await db.commit()
    await db.refresh(member)
    logger.info(f"User {user_id} successfully joined group {group_id}")
    return member


async def list_group_members(
    db: AsyncSession, group_id: uuid.UUID
) -> Sequence[GroupMember]:
    """List all members of a group."""
    # Verify group exists
    await get_group(db, group_id)
    
    result = await db.execute(
        select(GroupMember)
        .where(GroupMember.group_id == group_id)
        .order_by(GroupMember.joined_at)
    )
    return result.scalars().all()


async def set_group_leader(
    db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID
) -> Group:
    """Set the group leader for a group."""
    logger.info(f"set_group_leader called with group_id={group_id}, user_id={user_id}")
    
    # Verify group exists
    logger.info(f"Fetching group with id={group_id}")
    group = await get_group(db, group_id)
    logger.info(f"Group found: {group.name}")
    
    # Verify user exists
    logger.info(f"Fetching user with id={user_id}")
    user_result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = user_result.scalar_one_or_none()
    if not user:
        logger.error(f"User not found with id={user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    logger.info(f"User found: {user.full_name}")
    
    # Update group leader and grant admin privileges
    logger.info(f"Setting group leader_id to {user_id}")
    group.group_leader_id = user_id
    user.is_admin = True
    await db.commit()
    await db.refresh(group)
    logger.info(f"Group leader updated successfully, user {user_id} is now admin")
    return group
