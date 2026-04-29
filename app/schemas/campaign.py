import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CampaignCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    objective: str | None = None
    start_date: datetime
    end_date: datetime
    banner_url: str | None = None


class CampaignUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    objective: str | None = None
    end_date: datetime | None = None
    banner_url: str | None = None
    is_active: bool | None = None


class CampaignSessionCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    campaign_id: uuid.UUID
    group_id: uuid.UUID | None = None
    session_start_date: datetime
    session_end_date: datetime


# Nested schemas for related data
class GroupInSession(BaseModel):
    id: uuid.UUID
    name: str
    group_leader_id: uuid.UUID | None

    model_config = {"from_attributes": True}


class CampaignSessionOut(BaseModel):
    id: uuid.UUID
    title: str
    campaign_id: uuid.UUID
    group_id: uuid.UUID | None
    session_start_date: datetime
    session_end_date: datetime
    created_at: datetime
    updated_at: datetime
    group: GroupInSession | None = None

    model_config = {"from_attributes": True}


class CampaignOut(BaseModel):
    id: uuid.UUID
    title: str
    objective: str | None
    start_date: datetime
    end_date: datetime
    is_active: bool
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    sessions: list[CampaignSessionOut] = []

    model_config = {"from_attributes": True}




