import json
import time
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session as OrmSession

from app.core.db import get_db
from app.core.redis import get_redis
from app.models.event import Event as EventModel

router = APIRouter(prefix="/v1/sessions", tags=["streaming"])


def _format_sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@router.get("/{session_id}/events")
def sse_events(session_id: UUID, db: OrmSession = Depends(get_db)):
    """
    SSE stream of live events. Also sends a small backlog from DB first.
    """
    r = get_redis()
    channel = f"sessions:{session_id}:events"

    def gen():
        # 1) Send backlog (last 50 events) so refresh doesn't lose context
        backlog = (
            db.query(EventModel)
            .filter(EventModel.session_id == session_id)
            .order_by(EventModel.created_at.desc())
            .limit(50)
            .all()
        )
        for ev in reversed(backlog):
            yield _format_sse(ev.type, ev.payload)

        # 2) Subscribe to Redis for real-time events
        pubsub = r.pubsub()
        pubsub.subscribe(channel)

        # 3) Heartbeat to keep proxies from closing connection
        last_ping = time.time()

        try:
            for msg in pubsub.listen():
                # redis sends subscribe messages too
                if msg["type"] == "message":
                    body = json.loads(msg["data"])
                    yield _format_sse(body["type"], body["payload"])

                # heartbeat every ~15s
                if time.time() - last_ping > 15:
                    yield ": ping\n\n"
                    last_ping = time.time()
        finally:
            try:
                pubsub.unsubscribe(channel)
                pubsub.close()
            except Exception:
                pass

    return StreamingResponse(gen(), media_type="text/event-stream")
