import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas.campaign import (
    CampaignCreate,
    CampaignOut,
    CampaignSessionCreate,
    CampaignSessionOut,
    CampaignUpdate,
)
from app.services import campaign_service

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])
sessions_router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.get("", response_model=list[CampaignOut])
async def list_campaigns(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    return await campaign_service.list_campaigns(db, skip=skip, limit=limit)


@router.get("/{campaign_id}", response_model=CampaignOut)
async def get_campaign(
    campaign_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    return await campaign_service.get_campaign(db, campaign_id)


@router.post("", response_model=CampaignOut, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    payload: CampaignCreate,
    db: AsyncSession = Depends(get_db),
):
    return await campaign_service.create_campaign(db, payload)


@router.patch("/{campaign_id}", response_model=CampaignOut)
async def update_campaign(
    campaign_id: uuid.UUID,
    payload: CampaignUpdate,
    db: AsyncSession = Depends(get_db),
):
    return await campaign_service.update_campaign(db, campaign_id, payload)


# ---------- Campaign Sessions ----------

@router.get("/{campaign_id}/sessions", response_model=list[CampaignSessionOut])
async def list_sessions(
    campaign_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    return await campaign_service.list_sessions(db, campaign_id)


@router.post("/{campaign_id}/sessions", response_model=CampaignSessionOut, status_code=status.HTTP_201_CREATED)
async def create_session(
    campaign_id: uuid.UUID,
    payload: CampaignSessionCreate,
    db: AsyncSession = Depends(get_db),
):
    return await campaign_service.create_session(db, campaign_id, payload)


@sessions_router.get("", response_model=list[CampaignSessionOut])
async def list_all_sessions(
    db: AsyncSession = Depends(get_db),
):
    """List all campaign sessions across all campaigns."""
    return await campaign_service.list_all_sessions(db)