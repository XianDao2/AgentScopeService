import logging
import asyncio
from typing import Any
from collections import defaultdict
from contextlib import asynccontextmanager
import time

from src.ms3.common.config import get_settings
from src.ms3.database.redis_connection import get_redis_client
from src.ms3.middleware.tenant_isolation import get_trace_tenant

settings = get_settings()
logger = logging.getLogger(__name__)


class RateLimitExceededError(Exception):
    def __init__(self, message: str, retry_after: float = None):
        super().__init__(message)
        self.retry_after = retry_after


class RateLimiterMiddleware:
    def __init__(
        self,
        tenant_max_concurrent: int = None,
        global_max_concurrent: int = None,
        llm_max_concurrent: int = None
    ):
        self.tenant_max = tenant_max_concurrent or settings.tenant_max_concurrent_default
        self.global_max = global_max_concurrent or settings.global_max_concurrent
        self.llm_max = llm_max_concurrent or settings.llm_global_max_concurrency

        self._tenant_semaphores = defaultdict(lambda: asyncio.Semaphore(self.tenant_max))
        self._global_semaphore = asyncio.Semaphore(self.global_max)
        self._llm_semaphore = asyncio.Semaphore(self.llm_max)

    async def on_reply(self, agent: Any, inputs: Any, next_handler: Any) -> Any:
        tenant_id = get_trace_tenant()

        async with self._acquire_all(tenant_id):
            return await next_handler(agent, inputs)

    async def on_model_call(self, agent: Any, messages: Any, next_handler: Any) -> Any:
        tenant_id = get_trace_tenant()

        async with self._acquire_llm_only(tenant_id):
            return await next_handler(agent, messages)

    @asynccontextmanager
    async def _acquire_all(self, tenant_id: str):
        acquired = []
        try:
            if not await self._try_acquire_redis_rate_limit(tenant_id):
                raise RateLimitExceededError(f"Tenant {tenant_id} rate limit exceeded", retry_after=60)

            await self._acquire_semaphore(self._tenant_semaphores[tenant_id], "tenant", tenant_id)
            acquired.append(("tenant", self._tenant_semaphores[tenant_id]))

            await self._acquire_semaphore(self._global_semaphore, "global")
            acquired.append(("global", self._global_semaphore))

            await self._acquire_semaphore(self._llm_semaphore, "llm")
            acquired.append(("llm", self._llm_semaphore))

            yield
        finally:
            for name, semaphore in reversed(acquired):
                semaphore.release()
                logger.debug(f"RateLimiterMiddleware: Released {name} semaphore")

    @asynccontextmanager
    async def _acquire_llm_only(self, tenant_id: str):
        try:
            await self._acquire_semaphore(self._llm_semaphore, "llm")
            yield
        finally:
            self._llm_semaphore.release()
            logger.debug(f"RateLimiterMiddleware: Released llm semaphore")

    async def _acquire_semaphore(self, semaphore: asyncio.Semaphore, level: str, tenant_id: str = None):
        acquired = False
        retry_count = 0
        max_retries = 5
        retry_delay = 0.1

        while retry_count < max_retries and not acquired:
            try:
                await asyncio.wait_for(semaphore.acquire(), timeout=30.0)
                acquired = True
                logger.debug(f"RateLimiterMiddleware: Acquired {level} semaphore" + (f" for tenant {tenant_id}" if tenant_id else ""))
            except asyncio.TimeoutError:
                retry_count += 1
                if retry_count < max_retries:
                    await asyncio.sleep(retry_delay * retry_count)
                else:
                    raise RateLimitExceededError(
                        f"Failed to acquire {level} semaphore after {max_retries} retries",
                        retry_after=5.0
                    )

    async def _try_acquire_redis_rate_limit(self, tenant_id: str) -> bool:
        try:
            redis = await get_redis_client()
            key = f"agentscope:rate:{tenant_id}"

            current = await redis.incr(key)
            if current == 1:
                await redis.expire(key, 60)

            if current > self.tenant_max * 2:
                logger.warning(f"RateLimiterMiddleware: Redis rate limit exceeded for tenant {tenant_id}: {current}")
                return False

            return True
        except Exception as e:
            logger.error(f"RateLimiterMiddleware: Redis rate limit check failed - {e}")
            return True

    def get_current_stats(self, tenant_id: str) -> dict:
        return {
            "tenant": {
                "used": self.tenant_max - self._tenant_semaphores[tenant_id]._value,
                "max": self.tenant_max
            },
            "global": {
                "used": self.global_max - self._global_semaphore._value,
                "max": self.global_max
            },
            "llm": {
                "used": self.llm_max - self._llm_semaphore._value,
                "max": self.llm_max
            }
        }
