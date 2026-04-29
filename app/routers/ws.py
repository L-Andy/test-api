"""
WebSocket endpoint for live campaign tracking.

Single-pod fan-out only. For multi-pod (HPA) deployments, replace
ConnectionManager with a Redis Pub/Sub backed implementation so that a
contribution posted to pod A is broadcast to clients connected to pod B.
"""
import asyncio
import uuid
from collections import defaultdict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import func, or_, select

from app.core.database import AsyncSessionLocal
from app.core.security import decode_access_token
from app.models.campaign import CampaignSession
from app.models.group import GroupMember
from app.models.metrics import Metricrecord
from app.models.user import User

router = APIRouter(prefix="/ws", tags=["WebSocket"])

HEARTBEAT_INTERVAL_SECONDS = 25


class ConnectionManager:
    """Manages per-campaign WebSocket connections (in-process only)."""

    def __init__(self) -> None:
        self._connections: dict[uuid.UUID, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def add(self, campaign_id: uuid.UUID, ws: WebSocket) -> None:
        async with self._lock:
            self._connections[campaign_id].add(ws)

    async def remove(self, campaign_id: uuid.UUID, ws: WebSocket) -> None:
        async with self._lock:
            self._connections[campaign_id].discard(ws)
            if not self._connections[campaign_id]:
                self._connections.pop(campaign_id, None)

    async def broadcast(self, campaign_id: uuid.UUID, message: dict) -> None:
        """Send a JSON message to all clients watching a campaign.

        Sends concurrently so a slow client cannot block others.
        """
        async with self._lock:
            sockets = list(self._connections.get(campaign_id, ()))

        if not sockets:
            return

        async def _send(ws: WebSocket) -> WebSocket | None:
            try:
                await ws.send_json(message)
                return None
            except Exception:
                return ws

        results = await asyncio.gather(*(_send(ws) for ws in sockets))
        dead = [ws for ws in results if ws is not None]
        if dead:
            async with self._lock:
                bucket = self._connections.get(campaign_id)
                if bucket is not None:
                    for ws in dead:
                        bucket.discard(ws)
                    if not bucket:
                        self._connections.pop(campaign_id, None)


manager = ConnectionManager()


# ---------- AuthZ + snapshot helpers ----------

async def _user_can_view_campaign(
    db, user_id: uuid.UUID, campaign_id: uuid.UUID
) -> bool:
    """User may view live tracking if the campaign has at least one session
    that's open (group_id IS NULL) or tied to a group the user belongs to.
    """
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
    return (await db.execute(stmt)).scalar_one_or_none() is not None


async def _initial_snapshot(db, campaign_id: uuid.UUID) -> list[dict]:
    """Per-user totals so the client UI starts populated, not empty."""
    stmt = (
        select(
            Metricrecord.user_id,
            User.full_name,
            Metricrecord.metric_type,
            func.sum(Metricrecord.value).label("total"),
        )
        .join(User, User.id == Metricrecord.user_id)
        .where(Metricrecord.campaign_id == campaign_id)
        .group_by(Metricrecord.user_id, User.full_name, Metricrecord.metric_type)
    )
    rows = (await db.execute(stmt)).all()
    return [
        {
            "user_id": str(row.user_id),
            "full_name": row.full_name,
            "metric_type": row.metric_type.value,
            "total_value": float(row.total),
        }
        for row in rows
    ]


# ---------- Endpoint ----------

@router.websocket("/campaigns/{campaign_id}/live")
async def live_tracking(
    websocket: WebSocket,
    campaign_id: uuid.UUID,
    token: str = "",
):
    # NOTE: token is read from the query string for now. Reverse proxies log
    # query strings, so before production move auth to a subprotocol handshake
    # (Sec-WebSocket-Protocol: bearer,<jwt>).
    subject = decode_access_token(token)
    if not subject:
        await websocket.close(code=4001, reason="Invalid token")
        return
    try:
        user_id = uuid.UUID(subject)
    except ValueError:
        await websocket.close(code=4001, reason="Invalid token subject")
        return

    async with AsyncSessionLocal() as db:
        if not await _user_can_view_campaign(db, user_id, campaign_id):
            await websocket.close(code=4403, reason="Not a campaign member")
            return
        snapshot = await _initial_snapshot(db, campaign_id)

    await websocket.accept()
    await websocket.send_json({"type": "snapshot", "entries": snapshot})
    await manager.add(campaign_id, websocket)

    async def _heartbeat() -> None:
        try:
            while True:
                await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)
                await websocket.send_json({"type": "ping"})
        except Exception:
            return

    hb = asyncio.create_task(_heartbeat())
    try:
        while True:
            # Drain client messages (pongs etc.). Raises WebSocketDisconnect
            # when the peer goes away.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        hb.cancel()
        await manager.remove(campaign_id, websocket)
