import json
import uuid
from datetime import datetime, timezone

from agentscope.agent import ReActAgent

from ms3.database.connection import async_session_factory
from ms3.database.dal import ChatSessionDAL, ChatMessageDAL, AgentDefinitionDAL
from ms3.database.redis_connection import get_redis


_STATE_KEY_PREFIX = "ms3:agent_state:"
_SESSION_KEY_PREFIX = "ms3:session_info:"


class StateCoordinator:

    async def persist(
        self,
        agent: ReActAgent,
        agent_id: str,
        session_id: str,
        user_id: str,
        tenant_id: str,
    ) -> None:
        state_dict = agent.memory.state_dict()
        state_key = f"{_STATE_KEY_PREFIX}{tenant_id}:{agent_id}:{session_id}"

        redis = get_redis()
        await redis.set(
            state_key,
            json.dumps(state_dict, default=str),
        )

        session_info_key = f"{_SESSION_KEY_PREFIX}{session_id}"
        session_exists = await redis.exists(session_info_key)

        if not session_exists:
            await self._upsert_session(
                session_id=session_id,
                agent_id=agent_id,
                user_id=user_id,
                tenant_id=tenant_id,
            )
            session_info = {
                "tenant_id": tenant_id,
                "agent_id": agent_id,
                "user_id": user_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            await redis.set(session_info_key, json.dumps(session_info))

        await self._persist_messages(
            agent=agent,
            session_id=session_id,
            tenant_id=tenant_id,
        )

    async def load_state(
        self,
        agent_id: str,
        session_id: str,
        tenant_id: str,
    ) -> dict | None:
        state_key = f"{_STATE_KEY_PREFIX}{tenant_id}:{agent_id}:{session_id}"
        redis = get_redis()
        raw = await redis.get(state_key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return None

    async def clear_state(
        self,
        agent_id: str,
        session_id: str,
        tenant_id: str,
    ) -> None:
        state_key = f"{_STATE_KEY_PREFIX}{tenant_id}:{agent_id}:{session_id}"
        redis = get_redis()
        await redis.delete(state_key)

    async def _upsert_session(
        self,
        session_id: str,
        agent_id: str,
        user_id: str,
        tenant_id: str,
    ) -> None:
        async with async_session_factory() as session:
            try:
                session_dal = ChatSessionDAL(session, tenant_id=tenant_id)
                existing = await session_dal.get_or_none(session_id)
                if existing is None:
                    agent_dal = AgentDefinitionDAL(session, tenant_id=tenant_id)
                    agent_def = await agent_dal.get_or_none(agent_id)
                    title = agent_def.name if agent_def else "New Session"
                    await session_dal.create(
                        id=session_id,
                        tenant_id=tenant_id,
                        user_id=user_id,
                        title=title,
                    )
                    await session.commit()
            except Exception:
                await session.rollback()

    async def _persist_messages(
        self,
        agent: ReActAgent,
        session_id: str,
        tenant_id: str,
    ) -> None:
        memory = agent.memory
        messages = memory.get_memory()

        async with async_session_factory() as session:
            try:
                msg_dal = ChatMessageDAL(session)
                existing = await msg_dal.list_by_session(session_id)
                existing_count = len(existing)

                new_messages = messages[existing_count:]

                for msg in new_messages:
                    role = getattr(msg, "role", "assistant")
                    content = getattr(msg, "content", None)
                    if isinstance(content, list):
                        text_parts = []
                        for block in content:
                            if hasattr(block, "text"):
                                text_parts.append(block.text)
                            elif isinstance(block, str):
                                text_parts.append(block)
                        content = "\n".join(text_parts)

                    metadata = {}
                    if hasattr(msg, "metadata") and msg.metadata:
                        metadata = msg.metadata

                    model_name = getattr(agent, "model_config", None)
                    if model_name is not None:
                        model_name = getattr(model_name, "model_name", None)

                    await msg_dal.create(
                        id=uuid.uuid4().hex,
                        session_id=session_id,
                        role=role,
                        content=content,
                        model_name=model_name,
                        metadata_=metadata if metadata else None,
                    )

                await session.commit()
            except Exception:
                await session.rollback()
