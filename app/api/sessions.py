from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from app.api.schemas import SessionOut
from app.core.auth import require_api_key
from app.core.db import get_db
from app.models.session import Session as SessionModel
from app.session_runner.docker_manager import DockerSessionManager

mgr = DockerSessionManager()

router = APIRouter(prefix="/v1/sessions", tags=["sessions"])


@router.post("", response_model=SessionOut)
def create_session(db: OrmSession = Depends(get_db), _=Depends(require_api_key)):
    s = SessionModel(status="creating")
    db.add(s)
    db.commit()
    db.refresh(s)

    try:
        vm = mgr.start(session_id=str(s.id))
        s.vm_container_id = vm.container_id
        s.novnc_url = vm.novnc_url
        s.vnc_host = vm.vnc_host
        s.vnc_port = vm.vnc_port
        s.status = "idle"
        db.commit()
        db.refresh(s)
        return s
    except Exception as e:
        s.status = "failed"
        s.last_error = str(e)
        db.commit()
        raise HTTPException(500, f"Failed to start session VM: {e}") from e


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
def stop_session(
    session_id: UUID, db: OrmSession = Depends(get_db), _=Depends(require_api_key)
):
    s = db.get(SessionModel, session_id)
    if not s:
        raise HTTPException(404, "Session not found")

    if s.vm_container_id:
        try:
            mgr.stop(s.vm_container_id)
        except Exception as e:
            # keep going; we still mark session stopped
            s.last_error = f"Failed stopping container: {e}"

    s.status = "stopped"
    db.commit()
    db.refresh(s)
    return s
