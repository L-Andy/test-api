"""
Contributions: ingest per-user metric records and broadcast live.
"""
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.campaign import CampaignSession
from app.models.group import GroupMember
from app.models.metrics import Metricrecord
from app.models.user import User
from app.routers.ws import manager
from app.schemas.metrics import MetricrecordCreate, MetricrecordOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/contributions", tags=["Contributions"])


async def _user_in_campaign(
    db: AsyncSession, user_id: uuid.UUID, campaign_id: uuid.UUID
) -> bool:
    """A user can contribute to a campaign if it has at least one session that
    is either open to everyone (group_id IS NULL) or tied to a group the user
    belongs to."""
    user_groups_subq = (
        select(GroupMember.group_id).where(GroupMember.user_id == user_id).subquery()
    )
    stmt = (
        select(CampaignSession.id)
        .where(
            CampaignSession.campaign_id == campaign_id,
            or_(
                CampaignSession.group_id.is_(None),
                CampaignSession.group_id.in_(select(user_groups_subq.c.group_id)),
            ),
        )
        .limit(1)
    )
    result = (await db.execute(stmt)).scalar_one_or_none()
    logger.info(
        "membership check user=%s campaign=%s -> session_id=%s",
        user_id, campaign_id, result,
    )
    return result is not None


@router.post("", response_model=MetricrecordOut, status_code=status.HTTP_201_CREATED)
async def create_contribution(
    payload: MetricrecordCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Record a metric contribution and broadcast it to live viewers.

    Clients should send DELTAS (e.g. steps in the last 10s window), not the
    cumulative sensor reading, so leaderboards can SUM(value) safely.
    Supplying an idempotency_key makes retries safe.
    """
    logger.info(
        "contribution: user=%s campaign=%s metric=%s value=%s key=%s",
        current_user.id,
        payload.campaign_id,
        payload.metric_type.value,
        payload.value,
        payload.idempotency_key,
    )

    if not await _user_in_campaign(db, current_user.id, payload.campaign_id):
        logger.warning(
            "contribution rejected: user %s not in campaign %s",
            current_user.id, payload.campaign_id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of this campaign",
        )

    record = Metricrecord(
        user_id=current_user.id,
        campaign_id=payload.campaign_id,
        metric_type=payload.metric_type,
        value=payload.value,
        start_time=payload.start_time,
        end_time=payload.end_time,
        idempotency_key=payload.idempotency_key,
    )
    db.add(record)
    try:
        await db.commit()
    except IntegrityError:
        # Duplicate idempotency_key — return the existing row instead of failing.
        await db.rollback()
        existing = await db.execute(
            select(Metricrecord).where(
                Metricrecord.user_id == current_user.id,
                Metricrecord.campaign_id == payload.campaign_id,
                Metricrecord.idempotency_key == payload.idempotency_key,
            )
        )
        record = existing.scalar_one()
    else:
        await db.refresh(record)
        # Fire-and-forget broadcast. Failure must not affect the HTTP response.
        await manager.broadcast(
            payload.campaign_id,
            {
                "type": "contribution",
                "user_id": str(current_user.id),
                "full_name": current_user.full_name,
                "metric_type": payload.metric_type.value,
                "metric_value": float(payload.value),
                "record_date": payload.end_time.isoformat(),
            },
        )

    return record
