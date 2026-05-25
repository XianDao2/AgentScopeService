from sqlalchemy import Column, String, Integer, Text, JSON, ForeignKey

from src.ms3.database.connection import Base
from src.ms3.models.base import BaseModel


class ChatProvider(Base, BaseModel):
    __tablename__ = "chat_provider"

    tenant_id = Column(String(36), nullable=False, index=True)
    provider_name = Column(String(100), nullable=False)
    provider_code = Column(String(50), nullable=False)
    api_base = Column(String(255), nullable=True)
    api_key = Column(String(255), nullable=True)
    config = Column(JSON, nullable=True)
    credential_schema = Column(JSON, nullable=True)
    status = Column(String(1), nullable=False, default="0")
    del_flag = Column(String(1), nullable=False, default="0")


class ChatModel(Base, BaseModel):
    __tablename__ = "chat_model"

    tenant_id = Column(String(36), nullable=False, index=True)
    provider_id = Column(String(36), ForeignKey("chat_provider.id"), nullable=False, index=True)
    model_name = Column(String(100), nullable=False)
    model_code = Column(String(100), nullable=False)
    model_type = Column(String(20), nullable=False, default="chat")
    credential_type = Column(String(50), nullable=True)
    context_size = Column(Integer, nullable=True)
    output_size = Column(Integer, nullable=True)
    input_types = Column(JSON, nullable=True)
    output_types = Column(JSON, nullable=True)
    price_per_1k_input = Column(Integer, nullable=True)
    price_per_1k_output = Column(Integer, nullable=True)
    config = Column(JSON, nullable=True)
    status = Column(String(1), nullable=False, default="0")
    del_flag = Column(String(1), nullable=False, default="0")


class ChatSession(Base, BaseModel):
    __tablename__ = "chat_session"

    tenant_id = Column(String(36), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    agent_id = Column(String(36), nullable=True, index=True)
    title = Column(String(255), nullable=True)
    active_skill_names = Column(JSON, nullable=True)
    metadata = Column(JSON, nullable=True)
    status = Column(String(1), nullable=False, default="0")
    del_flag = Column(String(1), nullable=False, default="0")


class ChatMessage(Base, BaseModel):
    __tablename__ = "chat_message"

    session_id = Column(String(36), nullable=False, index=True)
    tenant_id = Column(String(36), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    content_type = Column(String(50), nullable=False, default="text")
    skill_name = Column(String(100), nullable=True)
    tool_call_id = Column(String(100), nullable=True)
    tool_name = Column(String(100), nullable=True)
    tool_args = Column(JSON, nullable=True)
    tool_result = Column(JSON, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    model_name = Column(String(100), nullable=True)
    metadata = Column(JSON, nullable=True)
    del_flag = Column(String(1), nullable=False, default="0")
