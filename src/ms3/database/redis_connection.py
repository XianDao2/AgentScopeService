from redis.asyncio import ConnectionPool, Redis

from ms3.common.config import settings

_pool: ConnectionPool | None = None


def _get_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            host=settings.redis_host,
            port=settings.redis_port,
            decode_responses=True,
            max_connections=50,
        )
    return _pool


def get_redis() -> Redis:
    return Redis(connection_pool=_get_pool())


async def check_redis_health() -> bool:
    try:
        client = get_redis()
        return await client.ping()
    except Exception:
        return False


async def close_redis() -> None:
    global _pool
    if _pool is not None:
        await _pool.disconnect()
        _pool = None
