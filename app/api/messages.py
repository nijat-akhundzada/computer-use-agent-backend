from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as OrmSession

from app.api.schemas import MessageIn, MessageOut
from app.core.auth import require_api_key
from app.core.db import get_db
from app.core.events import publish_event
from app.core.queue import enqueue
from app.models.message import Message as MessageModel
from app.models.session import Session as SessionModel

router = APIRouter(prefix="/v1/sessions", tags=["messages"])


@router.post("/{session_id}/messages", response_model=MessageOut)
def post_message(
    session_id: UUID,
    body: MessageIn,
    db: OrmSession = Depends(get_db),
    _=Depends(require_api_key),
):
    s = db.get(SessionModel, session_id)
    if not s:
        raise HTTPException(404, "Session not found")
    if s.status in ("stopped", "failed"):
        raise HTTPException(409, f"Session is {s.status}")

    # persist user message
    m = MessageModel(session_id=session_id, role="user", content=body.content)
    db.add(m)
    db.commit()
    db.refresh(m)

    # enqueue job
    enqueue({"session_id": str(session_id), "message_id": str(m.id)})

    # emit queued event
    publish_event(
        db=db,
        session_id=session_id,
        event_type="status",
        payload={"status": "queued", "message_id": str(m.id)},
    )

    return m
