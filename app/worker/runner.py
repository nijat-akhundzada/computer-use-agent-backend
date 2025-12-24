import time

from sqlalchemy.orm import Session as OrmSession

from app.agent_engine.mock_agent import run_mock_turn
from app.core.config import settings
from app.core.db import SessionLocal
from app.core.events import publish_event
from app.core.locks import acquire_session_lock, release_session_lock
from app.core.queue import dequeue_blocking
from app.models.message import Message as MessageModel
from app.models.session import Session as SessionModel


def _handle_job(job: dict):
    session_id = job["session_id"]
    message_id = job["message_id"]

    lock = acquire_session_lock(session_id, ttl_seconds=180)
    if not lock:
        # Another run is in progress; re-enqueue for later
        # (simple backoff to avoid tight loops)
        time.sleep(1)
        from app.core.queue import enqueue

        enqueue(job)
        return

    db: OrmSession = SessionLocal()
    try:
        s = db.get(SessionModel, session_id)
        if not s or s.status in ("stopped", "failed"):
            return

        # mark running
        s.status = "running"
        db.commit()
        user_msg = db.get(MessageModel, message_id)
        user_text = user_msg.content if user_msg else ""

        if settings.AGENT_MODE == "mock":
            run_mock_turn(
                db=db,
                session_id=s.id,
                user_text=user_text,
            )
        else:
            import os

            from app.agent_engine import run_computer_use_turn

            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise RuntimeError("ANTHROPIC_API_KEY missing")

            run_computer_use_turn(
                db=db,
                session_id=s.id,
                user_text=user_text,
                vm=run_computer_use_turn.VmInfo(
                    vnc_host=s.vnc_host,
                    vnc_port=s.vnc_port,
                    novnc_url=s.novnc_url or "",
                ),
                model=os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest"),
                anthropic_api_key=api_key,
            )

        publish_event(
            db=db, session_id=s.id, event_type="status", payload={"status": "running"}
        )

        # simulate progress streaming (replace with real agent loop later)
        publish_event(
            db=db,
            session_id=s.id,
            event_type="log",
            payload={"msg": "Starting agent turn"},
        )
        time.sleep(0.5)
        publish_event(
            db=db, session_id=s.id, event_type="token", payload={"delta": "Thinking..."}
        )
        time.sleep(0.8)
        publish_event(
            db=db,
            session_id=s.id,
            event_type="log",
            payload={"msg": f"Processed message_id={message_id}"},
        )

        # write assistant message
        assistant_text = (
            "Stub response: worker processed your request. "
            "Next step will integrate computer-use agent."
        )
        am = MessageModel(session_id=s.id, role="assistant", content=assistant_text)
        db.add(am)
        db.commit()

        publish_event(
            db=db,
            session_id=s.id,
            event_type="message",
            payload={"role": "assistant", "content": assistant_text},
        )

        # back to idle
        s.status = "idle"
        db.commit()
        publish_event(
            db=db, session_id=s.id, event_type="status", payload={"status": "idle"}
        )
    finally:
        db.close()
        release_session_lock(lock)


def run_forever():
    print("worker: starting job loop")
    while True:
        job = dequeue_blocking(timeout_seconds=5)
        if not job:
            continue
        try:
            _handle_job(job)
        except Exception as e:
            # avoid crashing the worker
            print("worker: job failed:", e)


if __name__ == "__main__":
    run_forever()
