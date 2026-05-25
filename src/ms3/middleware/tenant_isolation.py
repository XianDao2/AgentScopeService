import logging
from typing import Any, List
from contextvars import ContextVar

logger = logging.getLogger(__name__)

_tenant_id_var: ContextVar[str] = ContextVar("tenant_id", default="")


def set_trace_tenant(tenant_id: str) -> None:
    _tenant_id_var.set(tenant_id)


def get_trace_tenant() -> str:
    return _tenant_id_var.get()


class TenantIsolationMiddleware:
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id

    async def on_reply(self, agent: Any, inputs: Any, next_handler: Any) -> Any:
        set_trace_tenant(self.tenant_id)
        logger.debug(f"TenantIsolationMiddleware: Tenant ID set to {self.tenant_id}")
        return await next_handler(agent, inputs)

    async def on_acting(self, agent: Any, tool_calls: List[Any], next_handler: Any) -> Any:
        for tool_call in tool_calls:
            self._check_tool_access(tool_call)
        return await next_handler(agent, tool_calls)

    def _check_tool_access(self, tool_call: Any) -> None:
        tool_name = getattr(tool_call, "name", "unknown")
        logger.debug(f"TenantIsolationMiddleware: Checking access to tool {tool_name} for tenant {self.tenant_id}")
