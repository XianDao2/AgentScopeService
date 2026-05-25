from contextvars import ContextVar

from ms3.auth.jwt_auth import decode_token

_current_tenant_id: ContextVar[str | None] = ContextVar("tenant_id", default=None)


def set_current_tenant_id(tenant_id: str) -> None:
    _current_tenant_id.set(tenant_id)


def get_current_tenant_id() -> str | None:
    return _current_tenant_id.get()


class TenantContextMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] in ("http", "websocket"):
            authorization = None
            for name, value in scope.get("headers", []):
                if name == b"authorization":
                    authorization = value.decode("latin-1")
                    break

            if authorization and authorization.startswith("Bearer "):
                token = authorization[7:]
                try:
                    payload = decode_token(token)
                    tenant_id = payload.get("tenant_id")
                    if tenant_id:
                        set_current_tenant_id(tenant_id)
                except Exception:
                    pass

        await self.app(scope, receive, send)
