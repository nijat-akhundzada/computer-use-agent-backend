from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from app.core.db import get_db
from app.models.message import Message as MessageModel
from app.models.session import Session as SessionModel

router = APIRouter(prefix="/v1/sessions", tags=["history"])


@router.get("/{session_id}/history")
def history(session_id: UUID, db: OrmSession = Depends(get_db)):
    s = db.get(SessionModel, session_id)
    if not s:
        raise HTTPException(404, "Session not found")

    msgs = (
        db.execute(
            select(MessageModel)
            .where(MessageModel.session_id == session_id)
            .order_by(MessageModel.created_at.asc())
        )
        .scalars()
        .all()
    )
    return [
        {
            "id": str(m.id),
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.isoformat(),
        }
        for m in msgs
    ]
