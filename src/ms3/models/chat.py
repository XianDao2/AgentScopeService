import uuid
from datetime import datetime

from sqlalchemy import CHAR, DateTime, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ms3.models.sys import Base


class ChatSession(Base):
    __tablename__ = "chat_session"
    __table_args__ = (
        Index("idx_tenant_id", "tenant_id"),
        Index("idx_user_id", "user_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    title: Mapped[str | None] = mapped_column(String(200), default=None)
    active_skill_names: Mapped[dict | None] = mapped_column(JSON, default=None)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, default=None)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    del_flag: Mapped[str | None] = mapped_column(CHAR(1), default="0")


class ChatMessage(Base):
    __tablename__ = "chat_message"
    __table_args__ = (Index("idx_session_id", "session_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    session_id: Mapped[str] = mapped_column(String(36), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, default=None)
    skill_name: Mapped[str | None] = mapped_column(String(100), default=None)
    total_tokens: Mapped[int | None] = mapped_column(default=None)
    model_name: Mapped[str | None] = mapped_column(String(100), default=None)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, default=None)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
