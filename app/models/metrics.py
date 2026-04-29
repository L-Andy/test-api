import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.campaign import Campaign
    from app.models.user import User


# Add other metric types when integrate with health connect data
class MetricType(enum.Enum):
    steps = "steps"
    distance = "distance"

class Metricrecord(Base):
    __tablename__ = "metric_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    metric_type: Mapped[MetricType] = mapped_column(Enum(MetricType), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # Client-supplied key to make POSTs safely retriable. Scope = (user, campaign).
    idempotency_key: Mapped[str | None] = mapped_column(String(64), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "user_id", "campaign_id", "idempotency_key",
            name="uq_metric_record_idem",
        ),
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="metric_records")
    campaign: Mapped["Campaign"] = relationship(back_populates="metric_records")