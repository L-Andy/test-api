import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.metrics import MetricType

class MetricrecordCreate(BaseModel):
    campaign_id: uuid.UUID
    metric_type: MetricType
    value: float = Field(..., ge=0)
    start_time: datetime
    end_time: datetime
    # Optional client key. If supplied, two POSTs with the same key from the
    # same user for the same campaign collapse into one row (safe retries).
    idempotency_key: str | None = Field(default=None, max_length=64)


class MetricrecordOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    campaign_id: uuid.UUID
    metric_type: MetricType
    value: float
    start_time: datetime
    end_time: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
