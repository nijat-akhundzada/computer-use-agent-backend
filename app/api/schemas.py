from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class SessionOut(BaseModel):
    id: UUID
    status: str
    novnc_url: str | None = None
    vnc_host: str | None = None
    vnc_port: int | None = None
    last_error: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageIn(BaseModel):
    content: str


class MessageOut(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str

    class Config:
        from_attributes = True
