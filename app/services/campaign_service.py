import uuid
from typing import Sequence

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.campaign import Campaign, CampaignSession
from app.schemas.campaign import CampaignCreate, CampaignSessionCreate, CampaignUpdate


# ---------- Campaigns ----------

async def list_campaigns(db: AsyncSession, skip: int = 0, limit: int = 50) -> Sequence[Campaign]:
    result = await db.execute(
        select(Campaign)
        .options(
            selectinload(Campaign.sessions).selectinload(CampaignSession.group)
        )
        .offset(skip)
        .limit(limit)
        .order_by(Campaign.created_at.desc())
    )
    return result.scalars().all()


async def get_campaign(db: AsyncSession, campaign_id: uuid.UUID) -> Campaign:
    result = await db.execute(
        select(Campaign)
        .options(
            selectinload(Campaign.sessions).selectinload(CampaignSession.group)
        )
        .where(Campaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return campaign


async def create_campaign(
    db: AsyncSession, payload: CampaignCreate
) -> Campaign:
    if payload.end_date <= payload.start_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="end_date must be after start_date",
        )
    campaign = Campaign(
        title=payload.title,
        objective=payload.objective,
        start_date=payload.start_date,
        end_date=payload.end_date,
        banner_url=payload.banner_url
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    # Re-fetch with proper eager loading
    return await get_campaign(db, campaign.id)


async def update_campaign(
    db: AsyncSession, campaign_id: uuid.UUID, payload: CampaignUpdate
) -> Campaign:
    campaign = await get_campaign(db, campaign_id)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(campaign, field, value)
    await db.commit()
    # Re-fetch with proper eager loading
    return await get_campaign(db, campaign_id)


# ---------- Campaign Sessions ----------

async def list_sessions(db: AsyncSession, campaign_id: uuid.UUID):
    from app.models.campaign import CampaignSession
    
    await get_campaign(db, campaign_id)
    result = await db.execute(
        select(CampaignSession).where(CampaignSession.campaign_id == campaign_id)
    )
    return result.scalars().all()


async def list_all_sessions(db: AsyncSession):
    from app.models.campaign import CampaignSession
    
    result = await db.execute(select(CampaignSession))
    return result.scalars().all()


async def create_session(
    db: AsyncSession, campaign_id: uuid.UUID, payload: CampaignSessionCreate
):
    from app.models.campaign import CampaignSession
    
    await get_campaign(db, campaign_id)
    
    if payload.session_end_date <= payload.session_start_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="session_end_date must be after session_start_date",
        )
    
    session = CampaignSession(
        title=payload.title,
        campaign_id=campaign_id,
        group_id=payload.group_id,
        session_start_date=payload.session_start_date,
        session_end_date=payload.session_end_date,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session



