import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from src.ms3.common.config import get_settings
from src.ms3.database.redis_connection import get_redis
from src.ms3.database.connection import get_db_session
from src.ms3.models.platform import ExecutionTrace

logger = logging.getLogger(__name__)
settings = get_settings()


class AgentStateCoordinator:
    """
    AgentState 持久化协调器，在 Redis 和 MySQL 间同步
    """

    def __init__(self):
        self.redis_prefix = "agentscope:session"
        self.state_ttl = timedelta(hours=24)

    def _get_redis_key(self, session_id: str) -> str:
        """
        获取 Redis 键

        Args:
            session_id: 会话 ID

        Returns:
            Redis 键
        """
        return f"{self.redis_prefix}:{session_id}:state"

    async def save_state(
        self,
        session_id: str,
        tenant_id: str,
        agent_id: str,
        state: Dict[str, Any],
    ) -> None:
        """
        保存状态

        Args:
            session_id: 会话 ID
            tenant_id: 租户 ID
            agent_id: Agent ID
            state: 状态数据
        """
        try:
            redis = await get_redis()
            key = self._get_redis_key(session_id)

            # 保存到 Redis
            state_data = {
                "session_id": session_id,
                "tenant_id": tenant_id,
                "agent_id": agent_id,
                "state": state,
                "updated_at": datetime.utcnow().isoformat(),
            }

            await redis.setex(
                name=key,
                time=self.state_ttl,
                value=json.dumps(state_data, ensure_ascii=False),
            )

            logger.debug(f"Saved state to Redis for session: {session_id}")

            # TODO: 异步保存到 MySQL
            # await self._save_state_to_mysql(session_id, tenant_id, agent_id, state)

        except Exception as e:
            logger.error(f"Failed to save state: {str(e)}")
            raise

    async def load_state(
        self,
        session_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        加载状态

        Args:
            session_id: 会话 ID

        Returns:
            状态数据或 None
        """
        try:
            redis = await get_redis()
            key = self._get_redis_key(session_id)

            # 从 Redis 加载
            data = await redis.get(key)
            if not data:
                # 尝试从 MySQL 恢复
                # state = await self._load_state_from_mysql(session_id)
                # if state:
                #     await self.save_state(session_id, state["tenant_id"], state["agent_id"], state["state"])
                #     return state["state"]
                return None

            state_data = json.loads(data)
            logger.debug(f"Loaded state from Redis for session: {session_id}")
            return state_data.get("state")

        except Exception as e:
            logger.error(f"Failed to load state: {str(e)}")
            return None

    async def delete_state(self, session_id: str) -> None:
        """
        删除状态

        Args:
            session_id: 会话 ID
        """
        try:
            redis = await get_redis()
            key = self._get_redis_key(session_id)
            await redis.delete(key)
            logger.info(f"Deleted state for session: {session_id}")
        except Exception as e:
            logger.error(f"Failed to delete state: {str(e)}")
            raise

    async def save_execution_trace(
        self,
        tenant_id: str,
        session_id: str,
        agent_id: str,
        reply_id: str,
        stage: str,
        event_type: str,
        tool_name: Optional[str] = None,
        status: str = "completed",
        duration_ms: Optional[int] = None,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        保存执行追踪

        Args:
            tenant_id: 租户 ID
            session_id: 会话 ID
            agent_id: Agent ID
            reply_id: 回复 ID
            stage: 阶段
            event_type: 事件类型
            tool_name: 工具名称
            status: 状态
            duration_ms: 耗时（毫秒）
            input_tokens: 输入 token 数
            output_tokens: 输出 token 数
            payload: 负载数据
        """
        try:
            async with get_db_session() as db:
                trace = ExecutionTrace(
                    tenant_id=tenant_id,
                    session_id=session_id,
                    agent_id=agent_id,
                    reply_id=reply_id,
                    stage=stage,
                    event_type=event_type,
                    tool_name=tool_name,
                    status=status,
                    duration_ms=duration_ms,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    payload_json=payload,
                    created_at=datetime.utcnow(),
                )
                db.add(trace)
                await db.commit()
                logger.debug(f"Saved execution trace for session: {session_id}")

        except Exception as e:
            logger.error(f"Failed to save execution trace: {str(e)}")
            # 不抛出异常，避免影响主流程

    async def get_execution_traces(
        self,
        session_id: str,
        limit: int = 100,
    ) -> list[Dict[str, Any]]:
        """
        获取执行追踪

        Args:
            session_id: 会话 ID
            limit: 限制数量

        Returns:
            执行追踪列表
        """
        try:
            async with get_db_session() as db:
                from sqlalchemy import select, desc

                result = await db.execute(
                    select(ExecutionTrace)
                    .where(ExecutionTrace.session_id == session_id)
                    .order_by(desc(ExecutionTrace.created_at))
                    .limit(limit)
                )
                traces = result.scalars().all()

                return [
                    {
                        "id": trace.id,
                        "tenant_id": trace.tenant_id,
                        "session_id": trace.session_id,
                        "agent_id": trace.agent_id,
                        "reply_id": trace.reply_id,
                        "stage": trace.stage,
                        "event_type": trace.event_type,
                        "tool_name": trace.tool_name,
                        "status": trace.status,
                        "duration_ms": trace.duration_ms,
                        "input_tokens": trace.input_tokens,
                        "output_tokens": trace.output_tokens,
                        "payload_json": trace.payload_json,
                        "created_at": trace.created_at.isoformat(),
                    }
                    for trace in traces
                ]

        except Exception as e:
            logger.error(f"Failed to get execution traces: {str(e)}")
            return []

    async def cleanup_old_states(self, days: int = 7) -> int:
        """
        清理旧状态

        Args:
            days: 天数阈值

        Returns:
            清理数量
        """
        # TODO: 实现清理逻辑
        logger.warning(f"Cleanup old states not implemented (threshold: {days} days)")
        return 0
