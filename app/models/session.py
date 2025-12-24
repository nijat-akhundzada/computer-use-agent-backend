import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    status: Mapped[str] = mapped_column(String(32), default="creating", index=True)

    # VM/container connection metadata (filled later)
    vm_container_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    novnc_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    vnc_host: Mapped[str | None] = mapped_column(String(255), nullable=True)
    vnc_port: Mapped[int | None] = mapped_column(nullable=True)

    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )
