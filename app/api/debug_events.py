from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session as OrmSession

from app.core.db import get_db
from app.core.events import publish_event

router = APIRouter(prefix="/v1/debug", tags=["debug"])


class EmitReq(BaseModel):
    type: str
    payload: dict


@router.post("/sessions/{session_id}/emit")
def emit(session_id: UUID, body: EmitReq, db: OrmSession = Depends(get_db)):
    publish_event(
        db=db, session_id=session_id, event_type=body.type, payload=body.payload
    )
    return {"ok": True}
