import asyncio
import time
from typing import Any

from ms3.common.exceptions import RateLimitException
from ms3.database.redis_connection import get_redis

GLOBAL_MAX_CONCURRENT = 300
LLM_MAX_CONCURRENT = 200
TENANT_RATE_WINDOW = 60
TENANT_RATE_KEY_PREFIX = "ratelimit:tenant:"
GLOBAL_SEMAPHORE_KEY = "ratelimit:global:semaphore"
LLM_SEMAPHORE_KEY = "ratelimit:llm:semaphore"


class TenantRateLimiter:
    async def check(self, tenant_id: str) -> None:
        redis = get_redis()
        max_concurrent = await self._get_tenant_max_concurrent(tenant_id)
        key = f"{TENANT_RATE_KEY_PREFIX}{tenant_id}"

        now = time.time()
        window_start = now - TENANT_RATE_WINDOW

        pipe = redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        results = await pipe.execute()

        current_count = results[1]

        if current_count >= max_concurrent:
            oldest = await redis.zrange(key, 0, 0, withscores=True)
            if oldest:
                oldest_score = oldest[0][1]
                retry_after = int(oldest_score + TENANT_RATE_WINDOW - now) + 1
                retry_after = max(retry_after, 1)
            else:
                retry_after = TENANT_RATE_WINDOW
            raise RateLimitException(
                message=f"Tenant {tenant_id} rate limit exceeded: {current_count}/{max_concurrent}",
                retry_after=retry_after,
            )

        await redis.zadd(key, {str(now): now})
        await redis.expire(key, TENANT_RATE_WINDOW * 2)

    async def release(self, tenant_id: str) -> None:
        redis = get_redis()
        key = f"{TENANT_RATE_KEY_PREFIX}{tenant_id}"
        now = time.time()
        window_start = now - TENANT_RATE_WINDOW
        await redis.zremrangebyscore(key, 0, window_start)

    async def _get_tenant_max_concurrent(self, tenant_id: str) -> int:
        redis = get_redis()
        cached = await redis.get(f"tenant:max_concurrent:{tenant_id}")
        if cached is not None:
            return int(cached)

        try:
            from ms3.database.connection import async_session_factory
            from ms3.database.dal import SysTenantDAL

            async with async_session_factory() as session:
                dal = SysTenantDAL(session)
                tenant = await dal.get_or_none(tenant_id)
                if tenant and tenant.max_concurrent_executions:
                    max_val = tenant.max_concurrent_executions
                    await redis.set(
                        f"tenant:max_concurrent:{tenant_id}",
                        max_val,
                        ex=300,
                    )
                    return max_val
        except Exception:
            pass

        return 50

    async def get_current_count(self, tenant_id: str) -> int:
        redis = get_redis()
        key = f"{TENANT_RATE_KEY_PREFIX}{tenant_id}"
        now = time.time()
        window_start = now - TENANT_RATE_WINDOW
        await redis.zremrangebyscore(key, 0, window_start)
        return await redis.zcard(key)


class GlobalRateLimiter:
    async def acquire(self) -> bool:
        redis = get_redis()
        current = await self._get_current()
        if current >= GLOBAL_MAX_CONCURRENT:
            return False
        await redis.incr(GLOBAL_SEMAPHORE_KEY)
        return True

    async def release(self) -> None:
        redis = get_redis()
        current = await redis.get(GLOBAL_SEMAPHORE_KEY)
        if current and int(current) > 0:
            await redis.decr(GLOBAL_SEMAPHORE_KEY)

    async def _get_current(self) -> int:
        redis = get_redis()
        val = await redis.get(GLOBAL_SEMAPHORE_KEY)
        return int(val) if val else 0

    async def get_current(self) -> int:
        return await self._get_current()

    async def wait_and_acquire(self, timeout: float = 30.0) -> bool:
        deadline = time.time() + timeout
        while time.time() < deadline:
            if await self.acquire():
                return True
            await asyncio.sleep(0.5)
        return False


class LLMRateLimiter:
    def __init__(self):
        self._local_semaphore = asyncio.Semaphore(LLM_MAX_CONCURRENT)
        self._timeout = 30.0
        self._cache: dict[str, Any] = {}

    async def acquire(self) -> bool:
        try:
            await asyncio.wait_for(
                self._local_semaphore.acquire(),
                timeout=self._timeout,
            )
        except asyncio.TimeoutError:
            return False
        return True

    async def release(self) -> None:
        self._local_semaphore.release()

    def set_cache_response(self, key: str, response: Any) -> None:
        self._cache[key] = {
            "response": response,
            "timestamp": time.time(),
        }

    def get_cache_response(self, key: str, max_age: float = 300.0) -> Any | None:
        entry = self._cache.get(key)
        if entry is None:
            return None
        if time.time() - entry["timestamp"] > max_age:
            del self._cache[key]
            return None
        return entry["response"]

    async def get_current(self) -> int:
        redis = get_redis()
        val = await redis.get(LLM_SEMAPHORE_KEY)
        return int(val) if val else 0


tenant_rate_limiter = TenantRateLimiter()
global_rate_limiter = GlobalRateLimiter()
llm_rate_limiter = LLMRateLimiter()
