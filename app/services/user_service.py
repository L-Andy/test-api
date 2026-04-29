import secrets
import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    """Alias for get_user_by_id for consistency with other services."""
    return await get_user_by_id(db, user_id)


async def list_users(db: AsyncSession, skip: int = 0, limit: int = 50) -> Sequence[User]:
    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()


async def create_user(db: AsyncSession, payload: UserCreate) -> User:
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=get_password_hash(payload.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_user(db: AsyncSession, user: User, payload: UserUpdate) -> User:
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    user = await get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


async def find_or_create_by_email(db: AsyncSession, email: str, full_name: str) -> User:
    """Find existing user by email or create a new SSO user (no real password).
    If user exists, update their full_name in case it changed in Entra ID."""
    user = await get_user_by_email(db, email)
    if user:
        # Update full_name if it changed in Entra ID
        if user.full_name != full_name:
            user.full_name = full_name
            await db.commit()
            await db.refresh(user)
        return user
    # Create new SSO user
    user = User(
        email=email,
        full_name=full_name,
        hashed_password=get_password_hash(secrets.token_hex(32)),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
