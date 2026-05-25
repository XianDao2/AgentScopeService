from datetime import datetime, timedelta, timezone

from jose import jwt

from ms3.common.config import settings
from ms3.database.redis_connection import get_redis


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_REFRESH_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])


async def add_to_blacklist(token: str) -> None:
    redis = get_redis()
    payload = decode_token(token)
    exp = payload.get("exp")
    if exp is not None:
        now = int(datetime.now(timezone.utc).timestamp())
        ttl = exp - now
        if ttl > 0:
            await redis.set(f"token_blacklist:{token}", "1", ex=ttl)


async def is_blacklisted(token: str) -> bool:
    redis = get_redis()
    return bool(await redis.exists(f"token_blacklist:{token}"))
