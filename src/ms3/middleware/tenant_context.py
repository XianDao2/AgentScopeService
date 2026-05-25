from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Optional
import logging

from src.ms3.auth.jwt_auth import decode_token, set_current_context
from src.ms3.database.redis_connection import get_redis_client

logger = logging.getLogger(__name__)


class TenantContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        auth_header = request.headers.get("Authorization")
        tenant_id = None
        user_id = None

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            payload = decode_token(token)
            if payload:
                tenant_id = payload.get("tenant_id")
                user_id = payload.get("sub")
                set_current_context(tenant_id=tenant_id, user_id=user_id)

        request.state.tenant_id = tenant_id
        request.state.user_id = user_id

        response = await call_next(request)
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        auth_header = request.headers.get("Authorization")
        tenant_id = None

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            payload = decode_token(token)
            if payload:
                tenant_id = payload.get("tenant_id")

        if tenant_id:
            try:
                redis = await get_redis_client()
                key = f"rate_limit:tenant:{tenant_id}"

                current = await redis.incr(key)
                if current == 1:
                    await redis.expire(key, 60)

                if current > 1000:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Too many requests"
                    )
            except Exception as e:
                logger.warning(f"Rate limit check failed: {e}")

        response = await call_next(request)
        return response
