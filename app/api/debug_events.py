from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session as OrmSession

from app.core.config import settings
from app.core.db import get_db
from app.core.events import publish_event

router = APIRouter(prefix="/v1/debug", tags=["debug"])


class EmitReq(BaseModel):
    type: str
    payload: dict


@router.post("/sessions/{session_id}/emit")
def emit(session_id: UUID, body: EmitReq, db: OrmSession = Depends(get_db)):
    if settings.ENV != "dev":
        raise HTTPException(404, "Not found")

    publish_event(
        db=db, session_id=session_id, event_type=body.type, payload=body.payload
    )
    return {"ok": True}
