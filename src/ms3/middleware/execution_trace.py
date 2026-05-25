import uuid
from datetime import datetime, timezone

from sqlalchemy import text
from agentscope.middleware import MiddlewareBase
from agentscope.events import (
    ToolCallStartEvent,
    ToolResultEndEvent,
    ModelCallStartEvent,
    ModelCallEndEvent,
)

from ms3.database.connection import async_session_factory
from ms3.middleware.tenant_context import get_current_tenant_id


class ExecutionTraceMiddleware(MiddlewareBase):
    async def on_reply(self, agent, messages, next_fn):
        tenant_id = get_current_tenant_id()
        session_id = getattr(agent, "session_id", None) or str(uuid.uuid4())
        agent_id = getattr(agent, "agent_id", None) or getattr(agent, "name", None)

        stream = await next_fn(messages)

        async for event in stream:
            if isinstance(
                event,
                (
                    ToolCallStartEvent,
                    ToolResultEndEvent,
                    ModelCallStartEvent,
                    ModelCallEndEvent,
                ),
            ):
                await self._record_trace(tenant_id, session_id, agent_id, event)
            yield event

    async def _record_trace(self, tenant_id, session_id, agent_id, event):
        trace_data = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "session_id": session_id,
            "agent_id": agent_id,
            "reply_id": getattr(event, "reply_id", None),
            "stage": type(event).__name__,
            "event_type": type(event).__name__,
            "tool_name": getattr(event, "tool_name", None),
            "status": getattr(event, "status", "running"),
            "duration_ms": getattr(event, "duration_ms", None),
            "input_tokens": getattr(event, "input_tokens", None),
            "output_tokens": getattr(event, "output_tokens", None),
            "payload_json": None,
            "created_at": datetime.now(timezone.utc),
        }
        async with async_session_factory() as session:
            await session.execute(
                text(
                    """
                    INSERT INTO execution_trace
                    (id, tenant_id, session_id, agent_id, reply_id, stage,
                     event_type, tool_name, status, duration_ms, input_tokens,
                     output_tokens, payload_json, created_at)
                    VALUES
                    (:id, :tenant_id, :session_id, :agent_id, :reply_id, :stage,
                     :event_type, :tool_name, :status, :duration_ms, :input_tokens,
                     :output_tokens, :payload_json, :created_at)
                    """
                ),
                trace_data,
            )
            await session.commit()
