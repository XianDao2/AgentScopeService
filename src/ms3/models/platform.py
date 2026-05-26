from sqlalchemy import Column, String, Integer, Text, JSON, ForeignKey, DateTime, Float

from src.ms3.database.connection import Base
from src.ms3.models.base import BaseModel


class AgentDefinition(Base, BaseModel):
    __tablename__ = "agent_definition"

    tenant_id = Column(String(36), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    agent_type = Column(String(20), nullable=False, default="react")
    description = Column(String(500), nullable=True)
    sys_prompt = Column(Text, nullable=False)
    model_id = Column(String(36), nullable=True, index=True)
    credential_id = Column(String(36), nullable=True)
    tool_group_config = Column(JSON, nullable=True)
    kb_binding_config = Column(JSON, nullable=True)
    context_config = Column(JSON, nullable=True)
    react_config = Column(JSON, nullable=True)
    memory_policy = Column(String(20), nullable=False, default="session")
    workspace_type = Column(String(20), nullable=False, default="local")
    avatar = Column(String(255), nullable=True)
    status = Column(String(1), nullable=False, default="0")
    del_flag = Column(String(1), nullable=False, default="0")


class ToolGroupDefinition(Base, BaseModel):
    __tablename__ = "tool_group_definition"

    tenant_id = Column(String(36), nullable=False, index=True)
    group_code = Column(String(50), nullable=False)
    group_name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    instructions = Column(Text, nullable=True)
    is_active = Column(Integer, nullable=False, default=1)
    status = Column(String(1), nullable=False, default="0")
    del_flag = Column(String(1), nullable=False, default="0")


class ToolDefinition(Base, BaseModel):
    __tablename__ = "tool_definition"

    tenant_id = Column(String(36), nullable=False, index=True)
    group_id = Column(String(36), nullable=True, index=True)
    tool_code = Column(String(100), nullable=False)
    tool_name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    runtime_type = Column(String(20), nullable=False)
    entrypoint = Column(Text, nullable=True)
    schema_json = Column(JSON, nullable=True)
    is_concurrency_safe = Column(Integer, nullable=False, default=1)
    is_read_only = Column(Integer, nullable=False, default=0)
    permission_behavior = Column(String(10), nullable=False, default="ask")
    config = Column(JSON, nullable=True)
    status = Column(String(1), nullable=False, default="0")
    del_flag = Column(String(1), nullable=False, default="0")


class KnowledgeBase(Base, BaseModel):
    __tablename__ = "knowledge_base"

    tenant_id = Column(String(36), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    embedding_model = Column(String(100), nullable=False, default="text-embedding-v4")
    embedding_api_key = Column(String(255), nullable=True)
    dimensions = Column(Integer, nullable=False, default=1024)
    qdrant_url = Column(String(255), nullable=True)
    qdrant_collection = Column(String(100), nullable=True)
    retrieval_strategy = Column(String(20), nullable=False, default="auto")
    chunk_size = Column(Integer, nullable=False, default=512)
    top_k = Column(Integer, nullable=False, default=5)
    score_threshold = Column(Float, nullable=False, default=0.5)
    visibility = Column(String(20), nullable=False, default="tenant")
    allowed_roles = Column(JSON, nullable=True)
    status = Column(String(1), nullable=False, default="0")
    del_flag = Column(String(1), nullable=False, default="0")


class KnowledgeDocument(Base, BaseModel):
    __tablename__ = "knowledge_document"

    kb_id = Column(String(36), nullable=False, index=True)
    tenant_id = Column(String(36), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=True)
    content_type = Column(String(100), nullable=True)
    storage_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    parse_status = Column(String(20), nullable=False, default="pending")
    chunk_count = Column(Integer, nullable=False, default=0)
    version = Column(Integer, nullable=False, default=1)
    error_message = Column(Text, nullable=True)
    document_metadata = Column(JSON, nullable=True)


class KnowledgeChunk(Base, BaseModel):
    __tablename__ = "knowledge_chunk"

    document_id = Column(String(36), nullable=False, index=True)
    kb_id = Column(String(36), nullable=False, index=True)
    tenant_id = Column(String(36), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    metadata_json = Column(JSON, nullable=True)
    vector_id = Column(String(100), nullable=True)


class ExecutionTrace(Base):
    __tablename__ = "execution_trace"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), nullable=False, index=True)
    session_id = Column(String(36), nullable=False, index=True)
    agent_id = Column(String(36), nullable=True, index=True)
    reply_id = Column(String(36), nullable=True)
    stage = Column(String(30), nullable=False)
    event_type = Column(String(50), nullable=False)
    tool_name = Column(String(100), nullable=True)
    status = Column(String(20), nullable=False)
    duration_ms = Column(Integer, nullable=True)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    payload_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, index=True)
