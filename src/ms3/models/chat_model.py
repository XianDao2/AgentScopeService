import uuid
from datetime import datetime

from sqlalchemy import CHAR, DateTime, Index, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from ms3.models.sys import Base


class ChatProvider(Base):
    __tablename__ = "chat_provider"
    __table_args__ = (Index("idx_tenant_id", "tenant_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    provider_code: Mapped[str] = mapped_column(String(50), nullable=False)
    provider_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), default=None)
    api_base: Mapped[str | None] = mapped_column(String(255), default=None)
    status: Mapped[str | None] = mapped_column(CHAR(1), default="0")
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    del_flag: Mapped[str | None] = mapped_column(CHAR(1), default="0")
    credential_schema: Mapped[dict | None] = mapped_column(JSON, default=None)


class ChatModel(Base):
    __tablename__ = "chat_model"
    __table_args__ = (Index("idx_tenant_id", "tenant_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    provider_id: Mapped[str | None] = mapped_column(String(36), default=None)
    model_code: Mapped[str] = mapped_column(String(100), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), default=None)
    api_key: Mapped[str | None] = mapped_column(String(255), default=None)
    api_base: Mapped[str | None] = mapped_column(String(255), default=None)
    is_default: Mapped[int | None] = mapped_column(default=0)
    status: Mapped[str | None] = mapped_column(CHAR(1), default="0")
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    del_flag: Mapped[str | None] = mapped_column(CHAR(1), default="0")
    credential_type: Mapped[str | None] = mapped_column(String(50), default=None)
    context_size: Mapped[int | None] = mapped_column(default=None)
    output_size: Mapped[int | None] = mapped_column(default=None)
    input_types: Mapped[dict | None] = mapped_column(JSON, default=None)
    output_types: Mapped[dict | None] = mapped_column(JSON, default=None)
