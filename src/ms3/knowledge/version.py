import logging
from typing import Optional, List

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from src.ms3.common.config import get_settings
from src.ms3.models.platform import (
    KnowledgeBase,
    KnowledgeDocument,
    KnowledgeChunk,
)
from src.ms3.knowledge.service import PlatformKnowledgeService

settings = get_settings()
logger = logging.getLogger(__name__)


class KnowledgeVersionManager:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.knowledge_service = PlatformKnowledgeService(db_session)

    async def rebuild_index(self, kb_id: str) -> bool:
        try:
            logger.info(f"Starting index rebuild for knowledge base {kb_id}")
            
            knowledge_base = await self.knowledge_service.get_knowledge_base(kb_id)
            if not knowledge_base:
                logger.warning(f"Knowledge base {kb_id} not found")
                return False

            await self._clear_chunks_for_kb(kb_id)

            documents = await self._get_documents_for_kb(kb_id)
            logger.info(f"Found {len(documents)} documents to reindex")

            for doc in documents:
                await self._increment_document_version(doc)
                await self._reset_document_status(doc)

            await self.knowledge_service.invalidate_knowledge_cache(kb_id)
            
            logger.info(f"Successfully rebuilt index for knowledge base {kb_id}")
            return True

        except Exception as e:
            logger.exception(f"Failed to rebuild index for knowledge base {kb_id}: {e}")
            await self.db_session.rollback()
            return False

    async def rebuild_document_index(self, document_id: str) -> bool:
        try:
            logger.info(f"Starting index rebuild for document {document_id}")
            
            document = await self._get_document(document_id)
            if not document:
                logger.warning(f"Document {document_id} not found")
                return False

            await self._clear_chunks_for_document(document_id)
            await self._increment_document_version(document)
            await self._reset_document_status(document)

            await self.knowledge_service.invalidate_knowledge_cache(document.kb_id)
            
            logger.info(f"Successfully rebuilt index for document {document_id}")
            return True

        except Exception as e:
            logger.exception(f"Failed to rebuild index for document {document_id}: {e}")
            await self.db_session.rollback()
            return False

    async def clear_vector_store(self, kb_id: str) -> bool:
        try:
            logger.info(f"Clearing vector store for knowledge base {kb_id}")
            
            cached_knowledge = await self.knowledge_service.get_or_create_knowledge(kb_id)
            if not cached_knowledge:
                logger.warning(f"Knowledge base {kb_id} not found")
                return False

            await self._clear_chunks_for_kb(kb_id)
            logger.info(f"Successfully cleared vector store for knowledge base {kb_id}")
            return True

        except Exception as e:
            logger.exception(f"Failed to clear vector store for knowledge base {kb_id}: {e}")
            return False

    async def get_document_version(self, document_id: str) -> Optional[int]:
        document = await self._get_document(document_id)
        return document.version if document else None

    async def _get_document(self, document_id: str) -> Optional[KnowledgeDocument]:
        result = await self.db_session.execute(
            sa.select(KnowledgeDocument).where(KnowledgeDocument.id == document_id)
        )
        return result.scalar_one_or_none()

    async def _get_documents_for_kb(self, kb_id: str) -> List[KnowledgeDocument]:
        result = await self.db_session.execute(
            sa.select(KnowledgeDocument).where(KnowledgeDocument.kb_id == kb_id)
        )
        return list(result.scalars().all())

    async def _clear_chunks_for_kb(self, kb_id: str):
        await self.db_session.execute(
            sa.delete(KnowledgeChunk).where(KnowledgeChunk.kb_id == kb_id)
        )
        await self.db_session.commit()

    async def _clear_chunks_for_document(self, document_id: str):
        await self.db_session.execute(
            sa.delete(KnowledgeChunk).where(KnowledgeChunk.document_id == document_id)
        )
        await self.db_session.commit()

    async def _increment_document_version(self, document: KnowledgeDocument):
        document.version += 1
        await self.db_session.commit()

    async def _reset_document_status(self, document: KnowledgeDocument):
        document.parse_status = "pending"
        document.chunk_count = 0
        document.error_message = None
        await self.db_session.commit()

    async def list_document_versions(
        self,
        kb_id: str,
    ) -> List[dict]:
        try:
            result = await self.db_session.execute(
                sa.select(KnowledgeDocument)
                .where(KnowledgeDocument.kb_id == kb_id)
                .order_by(KnowledgeDocument.updated_at.desc())
            )
            documents = result.scalars().all()
            
            return [
                {
                    "document_id": doc.id,
                    "filename": doc.filename,
                    "version": doc.version,
                    "status": doc.parse_status,
                    "chunk_count": doc.chunk_count,
                    "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
                }
                for doc in documents
            ]
        except Exception as e:
            logger.exception(f"Failed to list document versions: {e}")
            return []
