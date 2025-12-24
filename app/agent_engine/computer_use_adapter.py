from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session as OrmSession

# IMPORTANT:
# This module expects you vendored upstream into vendor/computer_use_demo
# and that it exposes an agent loop function (often named sampling_loop or similar).
# If upstream changes, you only edit THIS adapter.
from vendor.computer_use_demo import loop as demo_loop  # type: ignore

from app.core.events import publish_event
from app.models.message import Message as MessageModel


@dataclass
class VmInfo:
    # Your session runner already stores these on Session model
    vnc_host: str
    vnc_port: int
    novnc_url: str


def _emit(db: OrmSession, session_id: UUID, event_type: str, payload: dict):
    publish_event(db=db, session_id=session_id, event_type=event_type, payload=payload)


def run_computer_use_turn(
    *,
    db: OrmSession,
    session_id: UUID,
    user_text: str,
    vm: VmInfo,
    model: str,
    anthropic_api_key: str,
) -> str:
    """
    Runs ONE user turn through the upstream agent loop and returns final assistant text.

    Adapter strategy:
    - translate upstream callbacks / yielded steps into publish_event(...)
    - persist assistant message at the end
    """

    _emit(db, session_id, "status", {"status": "running"})
    _emit(db, session_id, "log", {"msg": "Starting computer-use agent loop"})

    # ---- Hook points ----
    # Upstream loop typically needs:
    # - client / api key
    # - model
    # - tools (computer tool implementation)
    # - a way to stream intermediate steps
    #
    # Because upstream can change, keep all glue code here.

    def on_token(delta: str):
        _emit(db, session_id, "token", {"delta": delta})

    def on_tool_call(tool_name: str, tool_payload: dict[str, Any]):
        _emit(db, session_id, "tool_call", {"tool": tool_name, **tool_payload})

    def on_screenshot(image_b64: str | None = None, note: str | None = None):
        # You can later store screenshots to disk/S3 and emit URL instead.
        payload = {"note": note}
        if image_b64:
            payload["image_b64"] = image_b64
        _emit(db, session_id, "screenshot", payload)

    # ---- Call upstream loop ----
    # You will need to adapt this call to match the vendored loop signature.
    # The official demo has a dedicated agent loop file in computer_use_demo/loop.py.
    # :contentReference[oaicite:4]{index=4}
    result = (
        demo_loop.run_one_turn(  # <- YOU will map this to whatever upstream provides
            prompt=user_text,
            vnc_host=vm.vnc_host,
            vnc_port=vm.vnc_port,
            model=model,
            api_key=anthropic_api_key,
            on_token=on_token,
            on_tool_call=on_tool_call,
            on_screenshot=on_screenshot,
        )
    )

    final_text = result if isinstance(result, str) else str(result)

    # persist assistant message
    am = MessageModel(session_id=session_id, role="assistant", content=final_text)
    db.add(am)
    db.commit()

    _emit(db, session_id, "message", {"role": "assistant", "content": final_text})
    _emit(db, session_id, "status", {"status": "idle"})
    return final_text
