from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from ms3.common.config import settings

_client: AsyncIOMotorClient | None = None


def _get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(
            host=settings.mongo_host,
            port=settings.mongo_port,
            username=settings.mongo_user,
            password=settings.mongo_password,
        )
    return _client


def get_mongo_db() -> AsyncIOMotorDatabase:
    return _get_client()["ms3"]


def get_execution_traces_collection():
    return get_mongo_db()["execution_traces"]


def get_audit_logs_collection():
    return get_mongo_db()["audit_logs"]


def get_agent_events_collection():
    return get_mongo_db()["agent_events"]


async def check_mongo_health() -> bool:
    try:
        client = _get_client()
        result = await client.admin.command("ping")
        return result.get("ok") == 1.0
    except Exception:
        return False


async def close_mongo() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None
