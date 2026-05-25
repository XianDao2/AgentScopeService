import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from src.ms3.common.config import get_settings
from src.ms3.models.platform import (
    KnowledgeBase,
    KnowledgeChunk,
    KnowledgeDocument,
)
from src.ms3.knowledge.service import PlatformKnowledgeService

settings = get_settings()
logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    chunk_id: str
    document_id: str
    document_name: str
    content: str
    metadata: Dict[str, Any]
    score: float
    chunk_index: int


class KnowledgeRetriever:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.knowledge_service = PlatformKnowledgeService(db_session)

    async def retrieve(
        self,
        kb_id: str,
        query: str,
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None,
    ) -> List[RetrievalResult]:
        try:
            cached_knowledge = await self.knowledge_service.get_or_create_knowledge(kb_id)
            if not cached_knowledge:
                logger.warning(f"Knowledge base {kb_id} not found")
                return []

            effective_top_k = top_k or cached_knowledge.knowledge_base.top_k
            effective_threshold = (
                score_threshold or cached_knowledge.knowledge_base.score_threshold
            )

            chunks = await self._search_chunks_from_db(
                kb_id, query, effective_top_k
            )

            results = await self._enrich_chunks_with_documents(chunks)

            results_with_scores = self._add_simulated_scores(results, effective_threshold)

            logger.info(f"Retrieved {len(results_with_scores)} chunks from knowledge base {kb_id}")
            return results_with_scores

        except Exception as e:
            logger.exception(f"Failed to retrieve from knowledge base {kb_id}: {e}")
            return []

    async def retrieve_by_document(
        self,
        document_id: str,
    ) -> List[RetrievalResult]:
        try:
            chunks = await self._get_chunks_by_document(document_id)
            results = await self._enrich_chunks_with_documents(chunks)
            return [
                RetrievalResult(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    document_name=result.get("document_name", "unknown"),
                    content=chunk.content,
                    metadata=chunk.metadata_json or {},
                    score=1.0,
                    chunk_index=chunk.chunk_index,
                )
                for chunk, result in zip(chunks, results)
            ]
        except Exception as e:
            logger.exception(f"Failed to retrieve chunks for document {document_id}: {e}")
            return []

    async def _search_chunks_from_db(
        self,
        kb_id: str,
        query: str,
        top_k: int,
    ) -> List[KnowledgeChunk]:
        result = await self.db_session.execute(
            sa.select(KnowledgeChunk)
            .where(KnowledgeChunk.kb_id == kb_id)
            .order_by(KnowledgeChunk.chunk_index)
            .limit(top_k)
        )
        return list(result.scalars().all())

    async def _get_chunks_by_document(
        self,
        document_id: str,
    ) -> List[KnowledgeChunk]:
        result = await self.db_session.execute(
            sa.select(KnowledgeChunk)
            .where(KnowledgeChunk.document_id == document_id)
            .order_by(KnowledgeChunk.chunk_index)
        )
        return list(result.scalars().all())

    async def _enrich_chunks_with_documents(
        self,
        chunks: List[KnowledgeChunk],
    ) -> List[Dict[str, Any]]:
        if not chunks:
            return []

        document_ids = list({chunk.document_id for chunk in chunks})
        result = await self.db_session.execute(
            sa.select(KnowledgeDocument).where(
                KnowledgeDocument.id.in_(document_ids)
            )
        )
        documents = {doc.id: doc for doc in result.scalars().all()}

        enriched_results = []
        for chunk in chunks:
            doc = documents.get(chunk.document_id)
            enriched_results.append({
                "chunk": chunk,
                "document_name": doc.filename if doc else "unknown",
            })

        return enriched_results

    def _add_simulated_scores(
        self,
        results: List[Dict[str, Any]],
        threshold: float,
    ) -> List[RetrievalResult]:
        scored_results = []
        for idx, result in enumerate(results):
            chunk = result["chunk"]
            score = 1.0 - (idx * 0.1)
            if score >= threshold:
                scored_results.append(
                    RetrievalResult(
                        chunk_id=chunk.id,
                        document_id=chunk.document_id,
                        document_name=result["document_name"],
                        content=chunk.content,
                        metadata=chunk.metadata_json or {},
                        score=score,
                        chunk_index=chunk.chunk_index,
                    )
                )
        return scored_results

    async def get_document(
        self,
        document_id: str,
    ) -> Optional[KnowledgeDocument]:
        result = await self.db_session.execute(
            sa.select(KnowledgeDocument).where(KnowledgeDocument.id == document_id)
        )
        return result.scalar_one_or_none()
