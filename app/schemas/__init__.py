"""
Schemas package - exports all Pydantic schemas.
"""
from app.schemas.campaign import (
    CampaignCreate,
    CampaignOut,
    CampaignSessionCreate,
    CampaignSessionOut,
    CampaignUpdate,
)
from app.schemas.group import (
    GroupCreate,
    GroupMemberCreate,
    GroupMemberOut,
    GroupOut,
    GroupUpdate,
)
from app.schemas.metrics import MetricrecordCreate, MetricrecordOut
from app.schemas.user import (
    LoginRequest,
    SSORequest,
    TokenOut,
    UserCreate,
    UserOut,
    UserRegisterResponse,
    UserUpdate,
)

__all__ = [
    # Campaign
    "CampaignCreate",
    "CampaignUpdate",
    "CampaignOut",
    "CampaignSessionCreate",
    "CampaignSessionOut",
    # Group
    "GroupCreate",
    "GroupUpdate",
    "GroupOut",
    "GroupMemberCreate",
    "GroupMemberOut",
    # Metrics
    "MetricrecordCreate",
    "MetricrecordOut",
    # User
    "UserCreate",
    "UserUpdate",
    "UserOut",
    "UserRegisterResponse",
    "LoginRequest",
    "SSORequest",
    "TokenOut",
]
