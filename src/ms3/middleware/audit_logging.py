import time
import logging
from typing import Any
from datetime import datetime
import uuid

from src.ms3.database.mongo_connection import get_mongo_collection
from src.ms3.middleware.tenant_isolation import get_trace_tenant

logger = logging.getLogger(__name__)


class AuditLoggingMiddleware:
    async def on_model_call(self, agent: Any, messages: Any, next_handler: Any) -> Any:
        start_time = time.monotonic()
        tenant_id = get_trace_tenant()

        try:
            result = await next_handler(agent, messages)
            duration_ms = int((time.monotonic() - start_time) * 1000)

            await self._log_model_call(
                agent=agent,
                messages=messages,
                result=result,
                duration_ms=duration_ms,
                tenant_id=tenant_id,
                status="success"
            )

            return result
        except Exception as e:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            await self._log_model_call(
                agent=agent,
                messages=messages,
                result=None,
                duration_ms=duration_ms,
                tenant_id=tenant_id,
                status="error",
                error=str(e)
            )
            raise

    async def _log_model_call(
        self,
        agent: Any,
        messages: Any,
        result: Any,
        duration_ms: int,
        tenant_id: str,
        status: str,
        error: str = None
    ) -> None:
        try:
            collection = await get_mongo_collection("llm_call_logs")

            log_entry = {
                "_id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "agent_name": getattr(agent, "name", "unknown"),
                "model_name": getattr(getattr(agent, "model", None), "model_name", "unknown"),
                "timestamp": datetime.utcnow(),
                "duration_ms": duration_ms,
                "status": status,
                "error": error,
                "input_messages": self._serialize_messages(messages),
                "output": self._serialize_result(result),
                "input_tokens": self._extract_tokens(result, "input"),
                "output_tokens": self._extract_tokens(result, "output"),
                "total_tokens": self._extract_tokens(result, "total")
            }

            await collection.insert_one(log_entry)
            logger.debug(f"AuditLoggingMiddleware: Model call logged - {tenant_id} - {duration_ms}ms")
        except Exception as e:
            logger.error(f"AuditLoggingMiddleware: Failed to log model call - {e}")

    def _serialize_messages(self, messages: Any) -> list:
        if hasattr(messages, "__iter__") and not isinstance(messages, (str, bytes)):
            serialized = []
            for msg in messages:
                if hasattr(msg, "dict"):
                    serialized.append(msg.dict())
                elif hasattr(msg, "__dict__"):
                    serialized.append(dict(msg.__dict__))
                else:
                    serialized.append(str(msg))
            return serialized
        return []

    def _serialize_result(self, result: Any) -> Any:
        if result is None:
            return None
        if hasattr(result, "dict"):
            return result.dict()
        if hasattr(result, "__dict__"):
            return dict(result.__dict__)
        return str(result)

    def _extract_tokens(self, result: Any, token_type: str) -> int:
        if result is None:
            return 0
        usage = getattr(result, "usage", None)
        if usage is None:
            return 0
        if token_type == "input":
            return getattr(usage, "prompt_tokens", 0) or getattr(usage, "input_tokens", 0)
        elif token_type == "output":
            return getattr(usage, "completion_tokens", 0) or getattr(usage, "output_tokens", 0)
        elif token_type == "total":
            return getattr(usage, "total_tokens", 0)
        return 0
