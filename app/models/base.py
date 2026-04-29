from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime, timezone

from sqlalchemy import DateTime

def _now() -> datetime:
    return datetime.now(timezone.utc)

class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )
