import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.user import UserOut


class GroupCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    group_leader_id: uuid.UUID | None = None


class GroupUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    group_leader_id: uuid.UUID | None = None


class SetGroupLeader(BaseModel):
    user_id: uuid.UUID


class GroupOut(BaseModel):
    id: uuid.UUID
    name: str
    group_leader_id: uuid.UUID | None
    group_leader: UserOut | None = None
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GroupMemberCreate(BaseModel):
    group_id: uuid.UUID
    user_id: uuid.UUID


class GroupMemberOut(BaseModel):
    id: uuid.UUID
    group_id: uuid.UUID
    user_id: uuid.UUID
    joined_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
    exercise_session_id: uuid.UUID | None = None