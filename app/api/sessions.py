from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from app.api.schemas import SessionOut
from app.core.db import get_db
from app.models.session import Session as SessionModel

router = APIRouter(prefix="/v1/sessions", tags=["sessions"])


@router.post("", response_model=SessionOut)
def create_session(db: OrmSession = Depends(get_db)):
    s = SessionModel(status="creating")
    db.add(s)
    db.commit()
    db.refresh(s)
    # VM boot will be added in a later step
    s.status = "idle"
    db.commit()
    db.refresh(s)
    return s


@router.get("/{session_id}", response_model=SessionOut)
def get_session(session_id: UUID, db: OrmSession = Depends(get_db)):
    s = db.get(SessionModel, session_id)
    if not s:
        raise HTTPException(404, "Session not found")
    return s


@router.get("", response_model=list[SessionOut])
def list_sessions(db: OrmSession = Depends(get_db)):
    rows = (
        db.execute(select(SessionModel).order_by(SessionModel.created_at.desc()))
        .scalars()
        .all()
    )
    return rows


@router.post("/{session_id}/stop", response_model=SessionOut)
def stop_session(session_id: UUID, db: OrmSession = Depends(get_db)):
    s = db.get(SessionModel, session_id)
    if not s:
        raise HTTPException(404, "Session not found")
    s.status = "stopped"
    db.commit()
    db.refresh(s)
    return s
