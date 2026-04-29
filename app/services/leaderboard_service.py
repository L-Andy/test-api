"""Leaderboard queries.

Minimal implementation backed only by `metric_records` + `group_members`.
Supports filtering by an optional CampaignSession (so the leaderboard can be
scoped to a single session via its time window + group).
"""
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import CampaignSession
from app.models.group import Group, GroupMember
from app.models.metrics import Metricrecord, MetricType
from app.models.user import User


async def _resolve_session(
    db: AsyncSession, session_id: uuid.UUID | None
) -> CampaignSession | None:
    if not session_id:
        return None
    return (
        await db.execute(select(CampaignSession).where(CampaignSession.id == session_id))
    ).scalar_one_or_none()


def _apply_session_window(query, session: CampaignSession | None):
    if session is None:
        return query
    return query.where(
        Metricrecord.start_time >= session.session_start_date,
        Metricrecord.end_time <= session.session_end_date,
    )


async def get_individual_leaderboard(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    metric_type: MetricType = MetricType.steps,
    limit: int = 50,
    session_id: uuid.UUID | None = None,
) -> list[dict]:
    """Top users for a campaign by total `metric_type`.

    If `session_id` is given, restricts to records inside that session's window
    AND, when the session is group-scoped, to members of that group.
    """
    session = await _resolve_session(db, session_id)

    user_filter = None
    if session and session.group_id:
        members_subq = select(GroupMember.user_id).where(
            GroupMember.group_id == session.group_id
        )
        user_filter = Metricrecord.user_id.in_(members_subq)

    member_group_subq = (
        select(
            GroupMember.user_id,
            Group.id.label("group_id"),
            Group.name.label("group_name"),
        )
        .join(Group, Group.id == GroupMember.group_id)
        .subquery()
    )

    query = (
        select(
            Metricrecord.user_id,
            User.full_name,
            func.sum(Metricrecord.value).label("total_value"),
            member_group_subq.c.group_id,
            member_group_subq.c.group_name,
        )
        .join(User, User.id == Metricrecord.user_id)
        .outerjoin(
            member_group_subq, member_group_subq.c.user_id == Metricrecord.user_id
        )
        .where(
            Metricrecord.campaign_id == campaign_id,
            Metricrecord.metric_type == metric_type,
        )
    )
    query = _apply_session_window(query, session)
    if user_filter is not None:
        query = query.where(user_filter)

    query = (
        query.group_by(
            Metricrecord.user_id,
            User.full_name,
            member_group_subq.c.group_id,
            member_group_subq.c.group_name,
        )
        .order_by(func.sum(Metricrecord.value).desc())
        .limit(limit)
    )

    rows = (await db.execute(query)).all()
    return [
        {
            "rank": idx + 1,
            "user_id": str(row.user_id),
            "full_name": row.full_name,
            "total_value": float(row.total_value or 0),
            "metric_type": metric_type.value,
            "group_id": str(row.group_id) if row.group_id else None,
            "group_name": row.group_name,
        }
        for idx, row in enumerate(rows)
    ]


async def get_group_leaderboard(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    metric_type: MetricType = MetricType.steps,
    limit: int = 50,
    session_id: uuid.UUID | None = None,
) -> list[dict]:
    """Aggregate member contributions per group for a campaign."""
    session = await _resolve_session(db, session_id)

    query = (
        select(
            Group.id.label("group_id"),
            Group.name.label("group_name"),
            func.sum(Metricrecord.value).label("total_value"),
            func.count(func.distinct(Metricrecord.user_id)).label("member_count"),
        )
        .join(GroupMember, GroupMember.group_id == Group.id)
        .join(Metricrecord, Metricrecord.user_id == GroupMember.user_id)
        .where(
            Metricrecord.campaign_id == campaign_id,
            Metricrecord.metric_type == metric_type,
        )
    )
    query = _apply_session_window(query, session)
    if session and session.group_id:
        query = query.where(Group.id == session.group_id)

    query = (
        query.group_by(Group.id, Group.name)
        .order_by(func.sum(Metricrecord.value).desc())
        .limit(limit)
    )

    rows = (await db.execute(query)).all()
    return [
        {
            "rank": idx + 1,
            "group_id": str(row.group_id),
            "group_name": row.group_name,
            "total_value": float(row.total_value or 0),
            "member_count": int(row.member_count or 0),
            "metric_type": metric_type.value,
        }
        for idx, row in enumerate(rows)
    ]
