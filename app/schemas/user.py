import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)


class UserUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=255)
    avatar_url: str | None = None


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    is_admin: bool
    is_group_leader: bool = False
    group_id: uuid.UUID | None = None
    assigned_team: bool
    avatar_url: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SSORequest(BaseModel):
    ms_access_token: str = Field(..., min_length=1)


class UserRegisterResponse(BaseModel):
    """Response from Entra ID registration - returns user + JWT token."""
    user: UserOut
    access_token: str
    token_type: str = "bearer"
