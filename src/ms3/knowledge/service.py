import logging
import json
from typing import Optional
from functools import lru_cache

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from src.ms3.common.config import get_settings
from src.ms3.database.redis_connection import get_redis_client
from src.ms3.models.platform import KnowledgeBase

settings = get_settings()
logger = logging.getLogger(__name__)

KNOWLEDGE_CACHE_TTL = 600  # 10 minutes
CACHE_KEY_PREFIX = "agentscope:kb:"


class CachedKnowledge:
    def __init__(self, knowledge_base: KnowledgeBase):
        self.knowledge_base = knowledge_base
        self.embedding_model = knowledge_base.embedding_model
        self.embedding_api_key = knowledge_base.embedding_api_key or settings.dashscope_api_key
        self.dimensions = knowledge_base.dimensions
        self.qdrant_url = knowledge_base.qdrant_url or settings.qdrant_url
        self.qdrant_collection = (
            knowledge_base.qdrant_collection
            or f"tenant_{knowledge_base.tenant_id}_kb_{knowledge_base.id}"
        )


class PlatformKnowledgeService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_knowledge_base(self, kb_id: str) -> Optional[KnowledgeBase]:
        result = await self.db_session.execute(
            sa.select(KnowledgeBase).where(
                KnowledgeBase.id == kb_id, KnowledgeBase.del_flag == "0"
            )
        )
        return result.scalar_one_or_none()

    async def create_knowledge(self, kb_id: str) -> Optional[CachedKnowledge]:
        knowledge_base = await self.get_knowledge_base(kb_id)
        if not knowledge_base:
            logger.warning(f"Knowledge base {kb_id} not found")
            return None

        cached_knowledge = CachedKnowledge(knowledge_base)
        await self._cache_knowledge(cached_knowledge)
        return cached_knowledge

    async def get_or_create_knowledge(self, kb_id: str) -> Optional[CachedKnowledge]:
        cached = await self._get_cached_knowledge(kb_id)
        if cached:
            return cached
        
        return await self.create_knowledge(kb_id)

    async def _get_cached_knowledge(self, kb_id: str) -> Optional[CachedKnowledge]:
        try:
            redis_client = await get_redis_client()
            cache_key = f"{CACHE_KEY_PREFIX}{kb_id}:knowledge"
            data = await redis_client.get(cache_key)
            
            if data:
                kb_data = json.loads(data)
                knowledge_base = KnowledgeBase(**kb_data)
                return CachedKnowledge(knowledge_base)
        except Exception as e:
            logger.error(f"Failed to get cached knowledge: {e}")
        
        return None

    async def _cache_knowledge(self, cached_knowledge: CachedKnowledge):
        try:
            redis_client = await get_redis_client()
            cache_key = f"{CACHE_KEY_PREFIX}{cached_knowledge.knowledge_base.id}:knowledge"
            
            kb_data = {
                "id": cached_knowledge.knowledge_base.id,
                "tenant_id": cached_knowledge.knowledge_base.tenant_id,
                "name": cached_knowledge.knowledge_base.name,
                "embedding_model": cached_knowledge.knowledge_base.embedding_model,
                "embedding_api_key": cached_knowledge.knowledge_base.embedding_api_key,
                "dimensions": cached_knowledge.knowledge_base.dimensions,
                "qdrant_url": cached_knowledge.knowledge_base.qdrant_url,
                "qdrant_collection": cached_knowledge.knowledge_base.qdrant_collection,
                "chunk_size": cached_knowledge.knowledge_base.chunk_size,
                "top_k": cached_knowledge.knowledge_base.top_k,
                "score_threshold": cached_knowledge.knowledge_base.score_threshold,
            }
            
            await redis_client.setex(
                cache_key,
                KNOWLEDGE_CACHE_TTL,
                json.dumps(kb_data, ensure_ascii=False)
            )
        except Exception as e:
            logger.error(f"Failed to cache knowledge: {e}")

    async def invalidate_knowledge_cache(self, kb_id: str):
        try:
            redis_client = await get_redis_client()
            cache_key = f"{CACHE_KEY_PREFIX}{kb_id}:knowledge"
            await redis_client.delete(cache_key)
        except Exception as e:
            logger.error(f"Failed to invalidate cache for kb {kb_id}: {e}")
