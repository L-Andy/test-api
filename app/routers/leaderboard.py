import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.metrics import MetricType
from app.services import leaderboard_service

router = APIRouter(prefix="/leaderboard", tags=["Leaderboard"])


@router.get("/campaigns/{campaign_id}/individual")
async def individual_leaderboard(
    campaign_id: uuid.UUID,
    metric_type: MetricType = Query(MetricType.steps),
    session_id: uuid.UUID | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    return await leaderboard_service.get_individual_leaderboard(
        db, campaign_id, metric_type=metric_type, limit=limit, session_id=session_id
    )


@router.get("/campaigns/{campaign_id}/groups")
async def group_leaderboard(
    campaign_id: uuid.UUID,
    metric_type: MetricType = Query(MetricType.steps),
    session_id: uuid.UUID | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    return await leaderboard_service.get_group_leaderboard(
        db, campaign_id, metric_type=metric_type, limit=limit, session_id=session_id
    )
