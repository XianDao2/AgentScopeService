import uuid
from datetime import datetime

from sqlalchemy import CHAR, DateTime, Float, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ms3.models.sys import Base


class AgentDefinition(Base):
    __tablename__ = "agent_definition"
    __table_args__ = (Index("idx_tenant_id", "tenant_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    agent_type: Mapped[str] = mapped_column(String(20), nullable=False, default="react")
    sys_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    model_id: Mapped[str | None] = mapped_column(String(36), default=None)
    credential_id: Mapped[str | None] = mapped_column(String(36), default=None)
    tool_group_config: Mapped[dict | None] = mapped_column(JSON, default=None)
    kb_binding_config: Mapped[dict | None] = mapped_column(JSON, default=None)
    context_config: Mapped[dict | None] = mapped_column(JSON, default=None)
    react_config: Mapped[dict | None] = mapped_column(JSON, default=None)
    memory_policy: Mapped[str] = mapped_column(String(20), nullable=False, default="session")
    workspace_type: Mapped[str] = mapped_column(String(20), nullable=False, default="local")
    status: Mapped[str] = mapped_column(CHAR(1), nullable=False, default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    del_flag: Mapped[str] = mapped_column(CHAR(1), nullable=False, default="0")


class ToolGroupDefinition(Base):
    __tablename__ = "tool_group_definition"
    __table_args__ = (Index("idx_tenant_id", "tenant_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    group_code: Mapped[str] = mapped_column(String(50), nullable=False)
    group_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), default=None)
    instructions: Mapped[str | None] = mapped_column(Text, default=None)
    is_active: Mapped[int] = mapped_column(nullable=False, default=1)
    status: Mapped[str] = mapped_column(CHAR(1), nullable=False, default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    del_flag: Mapped[str] = mapped_column(CHAR(1), nullable=False, default="0")


class ToolDefinition(Base):
    __tablename__ = "tool_definition"
    __table_args__ = (
        Index("idx_tenant_id", "tenant_id"),
        Index("idx_group_id", "group_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    group_id: Mapped[str | None] = mapped_column(String(36), default=None)
    tool_code: Mapped[str] = mapped_column(String(100), nullable=False)
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), default=None)
    runtime_type: Mapped[str] = mapped_column(String(20), nullable=False)
    entrypoint: Mapped[str | None] = mapped_column(Text, default=None)
    schema_json: Mapped[dict | None] = mapped_column(JSON, default=None)
    is_concurrency_safe: Mapped[int] = mapped_column(nullable=False, default=1)
    is_read_only: Mapped[int] = mapped_column(nullable=False, default=0)
    permission_behavior: Mapped[str] = mapped_column(String(10), nullable=False, default="ask")
    status: Mapped[str] = mapped_column(CHAR(1), nullable=False, default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    del_flag: Mapped[str] = mapped_column(CHAR(1), nullable=False, default="0")


class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"
    __table_args__ = (Index("idx_tenant_id", "tenant_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), default=None)
    embedding_model: Mapped[str] = mapped_column(String(100), nullable=False, default="text-embedding-v4")
    embedding_api_key: Mapped[str | None] = mapped_column(String(255), default=None)
    dimensions: Mapped[int] = mapped_column(nullable=False, default=1024)
    qdrant_url: Mapped[str | None] = mapped_column(String(255), default=None)
    qdrant_collection: Mapped[str | None] = mapped_column(String(100), default=None)
    retrieval_strategy: Mapped[str] = mapped_column(String(20), nullable=False, default="auto")
    chunk_size: Mapped[int] = mapped_column(nullable=False, default=512)
    top_k: Mapped[int] = mapped_column(nullable=False, default=5)
    score_threshold: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    visibility: Mapped[str] = mapped_column(String(20), nullable=False, default="tenant")
    allowed_roles: Mapped[dict | None] = mapped_column(JSON, default=None)
    status: Mapped[str] = mapped_column(CHAR(1), nullable=False, default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    del_flag: Mapped[str] = mapped_column(CHAR(1), nullable=False, default="0")


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_document"
    __table_args__ = (
        Index("idx_kb_id", "kb_id"),
        Index("idx_tenant_id", "tenant_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    kb_id: Mapped[str] = mapped_column(String(36), nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(100), default=None)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int | None] = mapped_column(default=None)
    parse_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    chunk_count: Mapped[int] = mapped_column(nullable=False, default=0)
    version: Mapped[int] = mapped_column(nullable=False, default=1)
    error_message: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunk"
    __table_args__ = (
        Index("idx_document_id", "document_id"),
        Index("idx_kb_id", "kb_id"),
        Index("idx_tenant_id", "tenant_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    document_id: Mapped[str] = mapped_column(String(36), nullable=False)
    kb_id: Mapped[str] = mapped_column(String(36), nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    chunk_index: Mapped[int] = mapped_column(nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, default=None)
    vector_id: Mapped[str | None] = mapped_column(String(100), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class ExecutionTrace(Base):
    __tablename__ = "execution_trace"
    __table_args__ = (
        Index("idx_tenant_id", "tenant_id"),
        Index("idx_session_id", "session_id"),
        Index("idx_agent_id", "agent_id"),
        Index("idx_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    session_id: Mapped[str] = mapped_column(String(36), nullable=False)
    agent_id: Mapped[str | None] = mapped_column(String(36), default=None)
    reply_id: Mapped[str | None] = mapped_column(String(36), default=None)
    stage: Mapped[str] = mapped_column(String(30), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    tool_name: Mapped[str | None] = mapped_column(String(100), default=None)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    duration_ms: Mapped[int | None] = mapped_column(default=None)
    input_tokens: Mapped[int | None] = mapped_column(default=None)
    output_tokens: Mapped[int | None] = mapped_column(default=None)
    payload_json: Mapped[dict | None] = mapped_column(JSON, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
