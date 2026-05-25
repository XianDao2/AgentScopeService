import logging
import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from src.ms3.common.config import get_settings
from src.ms3.models.platform import (
    KnowledgeBase,
    KnowledgeDocument,
    KnowledgeChunk,
)
from src.ms3.knowledge.service import PlatformKnowledgeService, CachedKnowledge

settings = get_settings()
logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    content: str
    metadata: Dict[str, Any]
    index: int


@dataclass
class ParsedDocument:
    chunks: List[DocumentChunk]
    metadata: Dict[str, Any]


class TextReader:
    def __init__(self, chunk_size: int = 512):
        self.chunk_size = chunk_size

    async def read(self, text: str, filename: Optional[str] = None) -> ParsedDocument:
        chunks = []
        paragraphs = text.split("\n\n")
        current_chunk = ""
        chunk_index = 0

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            if len(current_chunk) + len(paragraph) <= self.chunk_size:
                current_chunk += ("\n\n" if current_chunk else "") + paragraph
            else:
                if current_chunk:
                    chunks.append(
                        DocumentChunk(
                            content=current_chunk,
                            metadata={"source": filename or "unknown", "index": chunk_index},
                            index=chunk_index,
                        )
                    )
                    chunk_index += 1
                current_chunk = paragraph

        if current_chunk:
            chunks.append(
                DocumentChunk(
                    content=current_chunk,
                    metadata={"source": filename or "unknown", "index": chunk_index},
                    index=chunk_index,
                )
            )

        return ParsedDocument(chunks=chunks, metadata={"filename": filename, "chunk_count": len(chunks)})


class ImageReader:
    def __init__(self):
        pass

    async def read(self, image_path: str, filename: Optional[str] = None) -> ParsedDocument:
        return ParsedDocument(
            chunks=[
                DocumentChunk(
                    content=f"Image: {filename or 'unknown image'}",
                    metadata={"source": filename or "unknown", "type": "image", "index": 0},
                    index=0,
                )
            ],
            metadata={"filename": filename, "chunk_count": 1},
        )


class DocumentIngester:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.knowledge_service = PlatformKnowledgeService(db_session)

    async def ingest_document(
        self,
        kb_id: str,
        document_id: str,
        content: str,
        content_type: str = "text/plain",
    ) -> bool:
        try:
            document = await self._get_document(document_id)
            if not document:
                logger.warning(f"Document {document_id} not found")
                return False

            await self._update_document_status(document, "parsing")

            cached_knowledge = await self.knowledge_service.get_or_create_knowledge(kb_id)
            if not cached_knowledge:
                await self._update_document_status(
                    document, "failed", error="Failed to get knowledge base"
                )
                return False

            parsed_doc = await self._parse_document(
                content, document.filename, content_type, cached_knowledge
            )

            await self._update_document_status(document, "chunking")

            chunk_count = len(parsed_doc.chunks)
            await self._save_chunks(document, parsed_doc.chunks)

            await self._update_document_status(document, "embedding")

            await self._update_document_status(
                document, "completed", chunk_count=chunk_count)

            logger.info(
                f"Successfully ingested document {document_id} with {chunk_count} chunks"
            )
            return True

        except Exception as e:
            logger.exception(f"Failed to ingest document {document_id}: {e}")
            await self._update_document_status(
                document, "failed", error=str(e)
            )
            return False

    async def _parse_document(
        self,
        content: str,
        filename: str,
        content_type: str,
        cached_knowledge: CachedKnowledge,
    ) -> ParsedDocument:
        if content_type.startswith("image/"):
            reader = ImageReader()
        else:
            reader = TextReader(chunk_size=cached_knowledge.knowledge_base.chunk_size)
        
        return await reader.read(content, filename)

    async def _get_document(self, document_id: str) -> Optional[KnowledgeDocument]:
        result = await self.db_session.execute(
            sa.select(KnowledgeDocument).where(KnowledgeDocument.id == document_id)
        )
        return result.scalar_one_or_none()

    async def _save_chunks(
        self,
        document: KnowledgeDocument,
        chunks: List[DocumentChunk],
    ):
        for chunk in chunks:
            knowledge_chunk = KnowledgeChunk(
                id=str(uuid.uuid4()),
                document_id=document.id,
                kb_id=document.kb_id,
                tenant_id=document.tenant_id,
                chunk_index=chunk.index,
                content=chunk.content,
                metadata_json=chunk.metadata,
                vector_id=str(uuid.uuid4()),
            )
            self.db_session.add(knowledge_chunk)
        
        await self.db_session.commit()

    async def _update_document_status(
        self,
        document: KnowledgeDocument,
        status: str,
        chunk_count: Optional[int] = None,
        error: Optional[str] = None,
    ):
        document.parse_status = status
        if chunk_count is not None:
            document.chunk_count = chunk_count
        if error:
            document.error_message = error
        await self.db_session.commit()
