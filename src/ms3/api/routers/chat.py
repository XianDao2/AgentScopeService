from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List, AsyncGenerator
import json
import time
import uuid

from src.ms3.database.connection import get_db
from src.ms3.auth.dependencies import get_current_user
from src.ms3.models.sys import SysUser
from src.ms3.models.chat import ChatSession, ChatMessage
from src.ms3.models.platform import AgentDefinition
from src.ms3.auth.jwt_auth import get_current_tenant_id, get_current_user_id

router = APIRouter(prefix="/api/v2/chat", tags=["聊天"])


class ChatRequest(BaseModel):
    message: str = Field(..., description="用户消息")
    session_id: Optional[str] = Field(None, description="会话ID，不传则创建新会话")
    agent_id: Optional[str] = Field(None, description="智能体ID")
    stream: bool = Field(True, description="是否流式响应")


@router.post("/sessions")
async def create_session(
    agent_id: Optional[str] = None,
    title: Optional[str] = "新对话",
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tenant_id = get_current_tenant_id()
    session = ChatSession(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        user_id=current_user.id,
        agent_id=agent_id,
        title=title or "新对话",
        status="0"
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/sessions")
async def list_sessions(
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sessions = db.query(ChatSession).filter(
        ChatSession.tenant_id == get_current_tenant_id(),
        ChatSession.user_id == current_user.id,
        ChatSession.del_flag == "0"
    ).order_by(ChatSession.updated_at.desc()).all()
    return sessions


@router.get("/sessions/{session_id}/messages")
async def list_messages(
    session_id: str,
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.tenant_id == get_current_tenant_id(),
        ChatSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id,
        ChatMessage.del_flag == "0"
    ).order_by(ChatMessage.created_at.asc()).all()
    return messages


async def mock_chat_stream(message: str) -> AsyncGenerator[str, None]:
    yield f"data: {json.dumps({'type': 'reply_start', 'id': str(uuid.uuid4())})}\n\n"

    thinking_content = f"我正在思考关于：{message[:20]}..."
    for char in thinking_content:
        yield f"data: {json.dumps({'type': 'thinking_delta', 'content': char})}\n\n"
        time.sleep(0.03)

    yield f"data: {json.dumps({'type': 'thinking_end'})}\n\n"

    response = f"这是一个模拟的回复。您说：{message}"
    for char in response:
        yield f"data: {json.dumps({'type': 'text_delta', 'content': char})}\n\n"
        time.sleep(0.02)

    yield f"data: {json.dumps({'type': 'reply_end'})}\n\n"


@router.post("/")
async def chat(
    request: ChatRequest,
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tenant_id = get_current_tenant_id()
    user_id = current_user.id

    session_id = request.session_id
    if not session_id:
        session = ChatSession(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            user_id=user_id,
            agent_id=request.agent_id,
            title=request.message[:30] if len(request.message) > 30 else request.message,
            status="0"
        )
        db.add(session)
        db.commit()
        session_id = session.id
    else:
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.tenant_id == tenant_id,
            ChatSession.user_id == user_id
        ).first()
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")

    user_msg = ChatMessage(
        id=str(uuid.uuid4()),
        session_id=session_id,
        tenant_id=tenant_id,
        role="user",
        content=request.message,
        content_type="text"
    )
    db.add(user_msg)

    if request.stream:
        return StreamingResponse(
            mock_chat_stream(request.message),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )
    else:
        db.commit()
        return {
            "message": f"这是一个模拟的回复。您说：{request.message}",
            "session_id": session_id
        }
