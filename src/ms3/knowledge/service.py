import time
import logging
from typing import Any

from ms3.common.config import settings

logger = logging.getLogger(__name__)

_CACHE_TTL = 600

_knowledge_cache: dict[str, tuple[float, Any]] = {}


def _create_qdrant_store(collection_name: str, qdrant_url: str | None = None):
    try:
        from agentscope.rag import QdrantStore

        return QdrantStore(
            collection_name=collection_name,
            url=qdrant_url or settings.qdrant_url,
        )
    except Exception as e:
        logger.error("Failed to create QdrantStore: %s", e)
        raise


def _create_embedding_model(api_key: str | None = None, model_name: str | None = None):
    try:
        from agentscope.embedding import DashScopeTextEmbedding

        return DashScopeTextEmbedding(
            model_name=model_name or "text-embedding-v4",
            api_key=api_key or settings.dashscope_api_key,
        )
    except Exception as e:
        logger.error("Failed to create DashScopeTextEmbedding: %s", e)
        raise


class PlatformKnowledgeService:
    def __init__(self):
        self._cache: dict[str, tuple[float, Any]] = _knowledge_cache

    def create_knowledge(self, kb: Any) -> Any:
        try:
            from agentscope.rag import SimpleKnowledge

            collection_name = kb.qdrant_collection or f"kb_{kb.id}"
            qdrant_url = kb.qdrant_url or settings.qdrant_url
            store = _create_qdrant_store(collection_name, qdrant_url)
            embedding = _create_embedding_model(
                api_key=kb.embedding_api_key,
                model_name=kb.embedding_model,
            )
            knowledge = SimpleKnowledge(
                knowledge_id=kb.id,
                store=store,
                embedding_model=embedding,
            )
            self._cache[kb.id] = (time.time(), knowledge)
            return knowledge
        except Exception as e:
            logger.error("Failed to create SimpleKnowledge for kb %s: %s", kb.id, e)
            raise

    def _get_or_create(self, kb_id: str, kb: Any | None = None) -> Any:
        now = time.time()
        if kb_id in self._cache:
            cached_time, cached_knowledge = self._cache[kb_id]
            if now - cached_time < _CACHE_TTL:
                return cached_knowledge

        if kb is None:
            raise ValueError(f"Knowledge base {kb_id} not cached and no kb object provided for creation")

        return self.create_knowledge(kb)

    async def get_stats(self, kb_id: str) -> dict:
        from ms3.database.connection import async_session_factory
        from ms3.database.dal import KnowledgeDocumentDAL, KnowledgeChunkDAL

        try:
            async with async_session_factory() as session:
                doc_dal = KnowledgeDocumentDAL(session=session, tenant_id=None)
                chunk_dal = KnowledgeChunkDAL(session=session, tenant_id=None)

                doc_count = await doc_dal.count(kb_id=kb_id)
                chunk_count = await chunk_dal.count(kb_id=kb_id)

                completed_docs = await doc_dal.count(kb_id=kb_id, parse_status="completed")
                failed_docs = await doc_dal.count(kb_id=kb_id, parse_status="failed")
                pending_docs = await doc_dal.count(kb_id=kb_id, parse_status="pending")

                if kb_id in self._cache:
                    index_status = "ready"
                else:
                    index_status = "not_loaded"

                return {
                    "doc_count": doc_count,
                    "chunk_count": chunk_count,
                    "index_status": index_status,
                    "completed_docs": completed_docs,
                    "failed_docs": failed_docs,
                    "pending_docs": pending_docs,
                    "last_update": None,
                }
        except Exception as e:
            logger.error("Failed to get stats for kb %s: %s", kb_id, e)
            return {
                "doc_count": 0,
                "chunk_count": 0,
                "index_status": "error",
                "completed_docs": 0,
                "failed_docs": 0,
                "pending_docs": 0,
                "last_update": None,
            }

    async def list_knowledge_bases(self, tenant_id: str) -> list[dict]:
        from ms3.database.connection import async_session_factory
        from ms3.database.dal import KnowledgeBaseDAL

        try:
            async with async_session_factory() as session:
                dal = KnowledgeBaseDAL(session=session, tenant_id=tenant_id)
                items = await dal.list_all()
                return [
                    {
                        "id": item.id,
                        "name": item.name,
                        "description": item.description,
                        "embedding_model": item.embedding_model,
                        "dimensions": item.dimensions,
                        "status": item.status,
                        "created_at": item.created_at.isoformat() if item.created_at else None,
                        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
                    }
                    for item in items
                ]
        except Exception as e:
            logger.error("Failed to list knowledge bases for tenant %s: %s", tenant_id, e)
            return []

    def invalidate_cache(self, kb_id: str) -> None:
        self._cache.pop(kb_id, None)


knowledge_service = PlatformKnowledgeService()
