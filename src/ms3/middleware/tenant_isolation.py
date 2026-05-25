import json

from agentscope.middleware import MiddlewareBase

from ms3.middleware.tenant_context import set_current_tenant_id, get_current_tenant_id


class TenantIsolationMiddleware(MiddlewareBase):
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id

    async def on_reply(self, agent, messages, next_fn):
        set_current_tenant_id(self.tenant_id)
        return await next_fn(messages)

    async def on_acting(self, agent, tool_call, next_fn):
        args = {}
        if hasattr(tool_call, "arguments"):
            args = tool_call.arguments or {}
        elif isinstance(tool_call, dict):
            args = tool_call.get("arguments", {})

        if isinstance(args, str):
            try:
                args = json.loads(args)
            except (json.JSONDecodeError, TypeError):
                args = {}

        resource_tenant_id = args.get("tenant_id")
        if resource_tenant_id and resource_tenant_id != self.tenant_id:
            raise PermissionError(
                f"Resource tenant mismatch: expected {self.tenant_id}, "
                f"got {resource_tenant_id}"
            )

        return await next_fn(tool_call)
