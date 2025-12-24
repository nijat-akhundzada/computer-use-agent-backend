import time
from uuid import UUID

from sqlalchemy.orm import Session as OrmSession

from app.core.events import publish_event
from app.models.message import Message as MessageModel


def run_mock_turn(
    *,
    db: OrmSession,
    session_id: UUID,
    user_text: str,
) -> str:
    publish_event(
        db=db, session_id=session_id, event_type="status", payload={"status": "running"}
    )
    publish_event(
        db=db,
        session_id=session_id,
        event_type="log",
        payload={"msg": "Mock agent started"},
    )

    # simulate thinking
    for word in ["Analyzing", "your", "request", "..."]:
        publish_event(
            db=db,
            session_id=session_id,
            event_type="token",
            payload={"delta": word + " "},
        )
        time.sleep(0.4)

    # simulate tool usage
    publish_event(
        db=db,
        session_id=session_id,
        event_type="tool_call",
        payload={"tool": "computer", "action": "open_browser"},
    )
    time.sleep(0.6)

    publish_event(
        db=db,
        session_id=session_id,
        event_type="tool_call",
        payload={
            "tool": "computer",
            "action": "navigate",
            "url": "https://example.com",
        },
    )
    time.sleep(0.6)

    publish_event(
        db=db,
        session_id=session_id,
        event_type="screenshot",
        payload={"note": "Mock screenshot after navigation"},
    )

    final_text = (
        "🧪 Mock agent response.\n\n"
        f"I received your instruction:\n"
        f"“{user_text}”\n\n"
        "In real mode, the computer-use agent would now control the VM."
    )

    am = MessageModel(session_id=session_id, role="assistant", content=final_text)
    db.add(am)
    db.commit()

    publish_event(
        db=db,
        session_id=session_id,
        event_type="message",
        payload={"role": "assistant", "content": final_text},
    )

    publish_event(
        db=db, session_id=session_id, event_type="status", payload={"status": "idle"}
    )
    return final_text
