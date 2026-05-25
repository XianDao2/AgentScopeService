import logging
import uuid
from typing import AsyncGenerator, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.ms3.common.config import get_settings
from src.ms3.models.platform import AgentDefinition
from src.ms3.models.chat import ChatSession, ChatMessage
from .agent_builder import PlatformAgentBuilder
from .toolkit_assembler import PlatformToolkitAssembler
from .credential_adapter import CredentialAdapter
from .state_coordinator import AgentStateCoordinator

logger = logging.getLogger(__name__)
settings = get_settings()


class ChatHandler:
    """
    聊天处理核心流程，接收 POST /chat，处理 SSE 流式响应
    """

    def __init__(
        self,
        agent_builder: PlatformAgentBuilder,
        toolkit_assembler: PlatformToolkitAssembler,
        credential_adapter: CredentialAdapter,
        state_coordinator: AgentStateCoordinator,
    ):
        self.agent_builder = agent_builder
        self.toolkit_assembler = toolkit_assembler
        self.credential_adapter = credential_adapter
        self.state_coordinator = state_coordinator

    async def handle_chat(
        self,
        tenant_id: str,
        user_id: str,
        agent_id: str,
        message: str,
        session_id: Optional[str] = None,
        db_session: Optional[AsyncSession] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        处理聊天请求

        Args:
            tenant_id: 租户 ID
            user_id: 用户 ID
            agent_id: Agent ID
            message: 用户消息
            session_id: 可选的会话 ID
            db_session: 数据库会话

        Yields:
            SSE 事件
        """
        reply_id = str(uuid.uuid4())
        start_time = datetime.utcnow()

        try:
            logger.info(f"Starting chat: tenant={tenant_id}, user={user_id}, agent={agent_id}")

            # 1. 获取或创建会话
            session = await self._get_or_create_session(
                tenant_id=tenant_id,
                user_id=user_id,
                agent_id=agent_id,
                session_id=session_id,
                db_session=db_session,
            )

            # 2. 保存用户消息
            await self._save_message(
                session_id=session.id,
                role="user",
                content=message,
                db_session=db_session,
            )

            # 3. 加载 Agent 状态
            agent_state = await self.state_coordinator.load_state(session.id)

            # 4. 获取 Agent 定义
            agent_def = await self._get_agent_definition(
                tenant_id=tenant_id,
                agent_id=agent_id,
                db_session=db_session,
            )

            # 5. 构建 Agent
            agent = await self.agent_builder.build(
                agent_def=agent_def,
                db_session=db_session,
                agent_state=agent_state,
            )

            # 6. 执行流式回复
            async for event in self._stream_reply(
                agent=agent,
                message=message,
                tenant_id=tenant_id,
                session_id=session.id,
                agent_id=agent_id,
                reply_id=reply_id,
            ):
                yield event

            # 7. 保存最终状态
            # TODO: 从 Agent 获取最终状态
            # await self.state_coordinator.save_state(
            #     session_id=session.id,
            #     tenant_id=tenant_id,
            #     agent_id=agent_id,
            #     state=agent.state,
            # )

            # 8. 记录执行追踪
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            await self.state_coordinator.save_execution_trace(
                tenant_id=tenant_id,
                session_id=session.id,
                agent_id=agent_id,
                reply_id=reply_id,
                stage="reply",
                event_type="reply_end",
                status="completed",
                duration_ms=duration_ms,
            )

        except Exception as e:
            logger.error(f"Chat handling failed: {str(e)}", exc_info=True)
            yield {
                "type": "error",
                "data": {"message": str(e)},
            }

            # 记录错误追踪
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            await self.state_coordinator.save_execution_trace(
                tenant_id=tenant_id,
                session_id=session_id or "unknown",
                agent_id=agent_id,
                reply_id=reply_id,
                stage="reply",
                event_type="error",
                status="failed",
                duration_ms=duration_ms,
                payload={"error": str(e)},
            )

    async def _get_or_create_session(
        self,
        tenant_id: str,
        user_id: str,
        agent_id: str,
        session_id: Optional[str],
        db_session: Optional[AsyncSession],
    ) -> ChatSession:
        """
        获取或创建会话

        Args:
            tenant_id: 租户 ID
            user_id: 用户 ID
            agent_id: Agent ID
            session_id: 会话 ID
            db_session: 数据库会话

        Returns:
            会话
        """
        if not db_session:
            raise ValueError("Database session is required")

        if session_id:
            result = await db_session.execute(
                select(ChatSession).where(
                    ChatSession.id == session_id,
                    ChatSession.tenant_id == tenant_id,
                    ChatSession.del_flag == "0",
                )
            )
            session = result.scalar_one_or_none()
            if session:
                return session

        # 创建新会话
        session = ChatSession(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            user_id=user_id,
            title="新会话",
            active_skill_names=[],
            metadata={"agent_id": agent_id},
            del_flag="0",
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        logger.info(f"Created new session: {session.id}")
        return session

    async def _save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        db_session: Optional[AsyncSession],
        agent_id: Optional[str] = None,
        total_tokens: Optional[int] = None,
        model_name: Optional[str] = None,
    ) -> ChatMessage:
        """
        保存消息

        Args:
            session_id: 会话 ID
            role: 角色
            content: 内容
            db_session: 数据库会话
            agent_id: Agent ID
            total_tokens: 总 token 数
            model_name: 模型名称

        Returns:
            消息
        """
        if not db_session:
            raise ValueError("Database session is required")

        message = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role=role,
            content=content,
            skill_name=agent_id,
            total_tokens=total_tokens,
            model_name=model_name,
            metadata={},
        )
        db_session.add(message)
        await db_session.commit()
        await db_session.refresh(message)

        return message

    async def _get_agent_definition(
        self,
        tenant_id: str,
        agent_id: str,
        db_session: Optional[AsyncSession],
    ) -> AgentDefinition:
        """
        获取 Agent 定义

        Args:
            tenant_id: 租户 ID
            agent_id: Agent ID
            db_session: 数据库会话

        Returns:
            Agent 定义
        """
        if not db_session:
            raise ValueError("Database session is required")

        result = await db_session.execute(
            select(AgentDefinition).where(
                AgentDefinition.id == agent_id,
                AgentDefinition.tenant_id == tenant_id,
                AgentDefinition.del_flag == "0",
            )
        )
        agent_def = result.scalar_one_or_none()

        if not agent_def:
            raise ValueError(f"Agent definition not found: {agent_id}")

        return agent_def

    async def _stream_reply(
        self,
        agent: Any,
        message: str,
        tenant_id: str,
        session_id: str,
        agent_id: str,
        reply_id: str,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式回复

        Args:
            agent: Agent 实例
            message: 用户消息
            tenant_id: 租户 ID
            session_id: 会话 ID
            agent_id: Agent ID
            reply_id: 回复 ID

        Yields:
            SSE 事件
        """
        try:
            # 尝试使用 AgentScope 的流式回复
            from agentscope.message import UserMsg

            user_msg = UserMsg(content=message)

            # 发送开始事件
            yield {
                "type": "reply_start",
                "data": {"reply_id": reply_id, "agent_id": agent_id},
            }

            # 保存执行追踪
            await self.state_coordinator.save_execution_trace(
                tenant_id=tenant_id,
                session_id=session_id,
                agent_id=agent_id,
                reply_id=reply_id,
                stage="reply",
                event_type="reply_start",
                status="started",
            )

            # 模拟流式回复（因为没有实际的 AgentScope）
            # 实际项目中应该使用 agent.reply_stream(user_msg)
            full_response = f"这是对消息 '{message}' 的模拟回复。"
            chunk_size = 5

            for i in range(0, len(full_response), chunk_size):
                chunk = full_response[i:i + chunk_size]
                yield {
                    "type": "text_delta",
                    "data": {"delta": chunk, "reply_id": reply_id},
                }
                import asyncio
                await asyncio.sleep(0.05)

            # 发送结束事件
            yield {
                "type": "reply_end",
                "data": {"reply_id": reply_id, "content": full_response},
            }

        except ImportError:
            # AgentScope 不可用时的回退方案
            logger.warning("AgentScope not available, using fallback streaming")

            yield {
                "type": "reply_start",
                "data": {"reply_id": reply_id, "agent_id": agent_id},
            }

            fallback_response = f"AgentScope 未安装，这是模拟回复：{message}"
            for char in fallback_response:
                yield {
                    "type": "text_delta",
                    "data": {"delta": char, "reply_id": reply_id},
                }
                import asyncio
                await asyncio.sleep(0.02)

            yield {
                "type": "reply_end",
                "data": {"reply_id": reply_id, "content": fallback_response},
            }
