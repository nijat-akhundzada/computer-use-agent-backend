import json
from uuid import UUID

from sqlalchemy.orm import Session as OrmSession

from app.core.redis import get_redis
from app.models.event import Event as EventModel


def publish_event(
    *,
    db: OrmSession,
    session_id: UUID,
    event_type: str,
    payload: dict,
) -> None:
    # 1) persist to DB
    ev = EventModel(session_id=session_id, type=event_type, payload=payload)
    db.add(ev)
    db.commit()

    # 2) publish to Redis pubsub channel
    r = get_redis()
    channel = f"sessions:{session_id}:events"
    r.publish(channel, json.dumps({"type": event_type, "payload": payload}))
