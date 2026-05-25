import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from src.ms3.common.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

_mongo_client: Optional[AsyncIOMotorClient] = None
_mongo_db: Optional[AsyncIOMotorDatabase] = None


async def get_mongo_client() -> AsyncIOMotorClient:
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = AsyncIOMotorClient(settings.mongo_dsn)
    return _mongo_client


async def get_mongo_db() -> AsyncIOMotorDatabase:
    global _mongo_db
    if _mongo_db is None:
        client = await get_mongo_client()
        _mongo_db = client[settings.mongo_db]
    return _mongo_db


async def get_mongo_collection(collection_name: str):
    db = await get_mongo_db()
    return db[collection_name]


async def check_mongo_connection() -> bool:
    try:
        client = await get_mongo_client()
        await client.admin.command("ping")
        return True
    except Exception as e:
        logger.error(f"MongoDB connection check failed: {e}")
        return False


async def close_mongo():
    global _mongo_client, _mongo_db
    if _mongo_client:
        _mongo_client.close()
        _mongo_client = None
        _mongo_db = None
