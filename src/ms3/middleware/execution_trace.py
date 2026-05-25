import logging
from typing import Any
from datetime import datetime
import uuid
import time

from sqlalchemy.orm import Session

from src.ms3.database.connection import db_session
from src.ms3.models.platform import ExecutionTrace
from src.ms3.middleware.tenant_isolation import get_trace_tenant

logger = logging.getLogger(__name__)


class ExecutionTraceMiddleware:
    def __init__(self, session_id: str = None, agent_id: str = None):
        self.session_id = session_id
        self.agent_id = agent_id
        self._trace_stack = []
        self._event_timings = {}

    async def on_reply(self, agent: Any, inputs: Any, next_handler: Any) -> Any:
        tenant_id = get_trace_tenant()
        trace_id = self._start_trace("reply", "ReplyStartEvent", tenant_id)

        try:
            result = await next_handler(agent, inputs)
            self._end_trace(trace_id, "success")
            return result
        except Exception as e:
            self._end_trace(trace_id, "failed", str(e))
            raise

    async def on_reasoning(self, agent: Any, inputs: Any, next_handler: Any) -> Any:
        tenant_id = get_trace_tenant()
        trace_id = self._start_trace("reasoning", "ReasoningStartEvent", tenant_id)

        try:
            result = await next_handler(agent, inputs)
            self._end_trace(trace_id, "success")
            return result
        except Exception as e:
            self._end_trace(trace_id, "failed", str(e))
            raise

    async def on_acting(self, agent: Any, tool_calls: Any, next_handler: Any) -> Any:
        tenant_id = get_trace_tenant()

        if hasattr(tool_calls, "__iter__") and not isinstance(tool_calls, (str, bytes)):
            for tool_call in tool_calls:
                tool_name = getattr(tool_call, "name", "unknown")
                self._start_trace("acting", "ToolCallStartEvent", tenant_id, tool_name=tool_name)

        try:
            result = await next_handler(agent, tool_calls)

            for _ in range(len(self._trace_stack)):
                trace = self._trace_stack.pop()
                if trace.get("stage") == "acting":
                    self._end_trace(trace["trace_id"], "success")

            return result
        except Exception as e:
            for _ in range(len(self._trace_stack)):
                trace = self._trace_stack.pop()
                if trace.get("stage") == "acting":
                    self._end_trace(trace["trace_id"], "failed", str(e))
            raise

    async def on_model_call(self, agent: Any, messages: Any, next_handler: Any) -> Any:
        tenant_id = get_trace_tenant()
        trace_id = self._start_trace("model_call", "ModelCallStartEvent", tenant_id)

        try:
            result = await next_handler(agent, messages)
            self._end_trace(trace_id, "success")
            return result
        except Exception as e:
            self._end_trace(trace_id, "failed", str(e))
            raise

    async def on_system_prompt(self, agent: Any, system_prompt: str, next_handler: Any) -> Any:
        tenant_id = get_trace_tenant()
        trace_id = self._start_trace("knowledge_retrieval", "KnowledgeRetrievalStartEvent", tenant_id)

        try:
            result = await next_handler(agent, system_prompt)
            self._end_trace(trace_id, "success")
            return result
        except Exception as e:
            self._end_trace(trace_id, "failed", str(e))
            raise

    def _start_trace(self, stage: str, event_type: str, tenant_id: str, tool_name: str = None) -> str:
        trace_id = str(uuid.uuid4())
        self._event_timings[trace_id] = time.monotonic()

        trace_info = {
            "trace_id": trace_id,
            "stage": stage,
            "event_type": event_type,
            "tenant_id": tenant_id,
            "tool_name": tool_name
        }
        self._trace_stack.append(trace_info)

        self._write_trace(
            trace_id=trace_id,
            tenant_id=tenant_id,
            stage=stage,
            event_type=event_type,
            tool_name=tool_name,
            status="started"
        )

        return trace_id

    def _end_trace(self, trace_id: str, status: str, error: str = None) -> None:
        start_time = self._event_timings.pop(trace_id, None)
        duration_ms = None
        if start_time is not None:
            duration_ms = int((time.monotonic() - start_time) * 1000)

        trace_info = None
        for trace in self._trace_stack:
            if trace["trace_id"] == trace_id:
                trace_info = trace
                break

        if trace_info:
            payload = None
            if error:
                payload = {"error": error}

            self._write_trace(
                trace_id=trace_id,
                tenant_id=trace_info["tenant_id"],
                stage=trace_info["stage"],
                event_type=trace_info["event_type"].replace("Start", "End"),
                tool_name=trace_info.get("tool_name"),
                status=status,
                duration_ms=duration_ms,
                payload_json=payload
            )

    def _write_trace(
        self,
        trace_id: str,
        tenant_id: str,
        stage: str,
        event_type: str,
        tool_name: str = None,
        status: str = "started",
        duration_ms: int = None,
        input_tokens: int = None,
        output_tokens: int = None,
        payload_json: dict = None
    ) -> None:
        try:
            with db_session() as db:
                trace = ExecutionTrace(
                    id=trace_id,
                    tenant_id=tenant_id,
                    session_id=self.session_id,
                    agent_id=self.agent_id,
                    reply_id=None,
                    stage=stage,
                    event_type=event_type,
                    tool_name=tool_name,
                    status=status,
                    duration_ms=duration_ms,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    payload_json=payload_json,
                    created_at=datetime.utcnow()
                )
                db.add(trace)
                db.commit()
                logger.debug(f"ExecutionTraceMiddleware: Trace written - {trace_id} - {stage} - {status}")
        except Exception as e:
            logger.error(f"ExecutionTraceMiddleware: Failed to write trace - {e}")
