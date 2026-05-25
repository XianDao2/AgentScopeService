import time
from datetime import datetime, timezone

from agentscope.middleware import MiddlewareBase

from ms3.database.mongo_connection import get_mongo_db


class AuditLoggingMiddleware(MiddlewareBase):
    async def on_model_call(self, agent, messages, next_fn):
        start_time = time.monotonic()
        start_dt = datetime.now(timezone.utc)

        result = await next_fn(messages)

        duration_ms = int((time.monotonic() - start_time) * 1000)

        model_name = None
        model_config = getattr(agent, "model_config", None)
        if model_config is not None:
            model_name = getattr(model_config, "model_name", None) or str(
                model_config
            )

        usage = getattr(result, "usage", None) if result is not None else None
        input_tokens = getattr(usage, "prompt_tokens", None) if usage else None
        output_tokens = (
            getattr(usage, "completion_tokens", None) if usage else None
        )

        db = get_mongo_db()
        await db.llm_audit_logs.insert_one(
            {
                "model_name": model_name,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "duration_ms": duration_ms,
                "timestamp": start_dt,
                "agent_name": getattr(agent, "name", None),
            }
        )

        return result
