import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, validate_ms_token
from app.dependencies import get_db
from app.models.group import Group, GroupMember
from app.schemas.user import (
    LoginRequest,
    SSORequest,
    TokenOut,
    UserCreate,
    UserOut,
    UserRegisterResponse,
    UserUpdate,
)
from app.services import user_service

router = APIRouter(prefix="/auth", tags=["Auth"])
users_router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    """Traditional email/password registration (deprecated - use /users/register with Entra ID)."""
    existing = await user_service.get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    return await user_service.create_user(db, payload)


@router.post("/login", response_model=TokenOut)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Accepts JSON body: { "email": "...", "password": "..." }"""
    user = await user_service.authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(subject=user.id)
    return TokenOut(access_token=token)


@router.post("/sso", response_model=TokenOut)
async def sso_login(payload: SSORequest, db: AsyncSession = Depends(get_db)):
    """Exchange a Microsoft access token for a backend JWT."""
    ms_profile = await validate_ms_token(payload.ms_access_token)
    user = await user_service.find_or_create_by_email(
        db, email=ms_profile["email"], full_name=ms_profile["display_name"]
    )
    token = create_access_token(subject=user.id)
    return TokenOut(access_token=token)


# ---------- User registration (Entra ID SSO) ----------

@users_router.post("/register", response_model=UserRegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_with_entra(
    payload: SSORequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Register/login user with Entra ID (Microsoft Azure AD).
    
    Flow:
    1. Frontend authenticates user with Entra ID
    2. Frontend sends the Microsoft access token to this endpoint
    3. Backend validates the token with Microsoft Graph API
    4. Backend creates user if new, or finds existing user
    5. Backend returns user profile + JWT token for API access
    """
    # Validate Microsoft token and extract user profile
    ms_profile = await validate_ms_token(payload.ms_access_token)
    
    # Find or create user
    user = await user_service.find_or_create_by_email(
        db, 
        email=ms_profile["email"], 
        full_name=ms_profile["display_name"]
    )
    
    # Generate backend JWT token
    token = create_access_token(subject=user.id)
    
    # Check if user is a group leader
    result = await db.execute(select(Group).where(Group.group_leader_id == user.id))
    leader_group = result.scalar_one_or_none()
    is_leader = leader_group is not None

    # Get user's group_id (from group_members)
    membership = await db.execute(
        select(GroupMember.group_id).where(GroupMember.user_id == user.id).limit(1)
    )
    group_id = membership.scalar_one_or_none()

    user_out = UserOut.model_validate(user).model_copy(
        update={"is_group_leader": is_leader, "group_id": group_id}
    )
    
    return UserRegisterResponse(
        user=user_out,
        access_token=token,
    )