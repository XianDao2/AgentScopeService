import logging
from datetime import datetime

from ms3.knowledge.service import knowledge_service

logger = logging.getLogger(__name__)


async def delete_document_vectors(document_id: str) -> int:
    from ms3.database.connection import async_session_factory
    from ms3.database.dal import KnowledgeChunkDAL

    deleted_count = 0

    try:
        async with async_session_factory() as session:
            chunk_dal = KnowledgeChunkDAL(session=session, tenant_id=None)
            chunks = await chunk_dal.list_by_document(document_id)

            for chunk in chunks:
                if chunk.vector_id:
                    try:
                        kb_id = chunk.kb_id
                        if kb_id in knowledge_service._cache:
                            _, cached_knowledge = knowledge_service._cache[kb_id]
                            if hasattr(cached_knowledge, "store") and hasattr(cached_knowledge.store, "delete"):
                                await cached_knowledge.store.delete(ids=[chunk.vector_id])
                    except Exception as e:
                        logger.error("Failed to delete vector %s from Qdrant: %s", chunk.vector_id, e)

                await session.delete(chunk)
                deleted_count += 1

            await session.commit()

        return deleted_count

    except Exception as e:
        logger.error("Failed to delete document vectors for %s: %s", document_id, e)
        raise


async def increment_version(document_id: str) -> int:
    from ms3.database.connection import async_session_factory
    from ms3.database.dal import KnowledgeDocumentDAL

    try:
        async with async_session_factory() as session:
            doc_dal = KnowledgeDocumentDAL(session=session, tenant_id=None)
            doc = await doc_dal.get(document_id)
            new_version = doc.version + 1
            await doc_dal.update(document_id, version=new_version, updated_at=datetime.now())
            await session.commit()
            return new_version

    except Exception as e:
        logger.error("Failed to increment version for document %s: %s", document_id, e)
        raise


async def rebuild_document_index(document_id: str) -> int:
    from ms3.database.connection import async_session_factory
    from ms3.database.dal import KnowledgeDocumentDAL
    from ms3.knowledge.ingest import ingest_document

    try:
        async with async_session_factory() as session:
            doc_dal = KnowledgeDocumentDAL(session=session, tenant_id=None)
            doc = await doc_dal.get(document_id)
            await session.commit()

        await delete_document_vectors(document_id)

        new_version = await increment_version(document_id)

        result_id = await ingest_document(
            kb_id=doc.kb_id,
            file_path=doc.storage_path,
            content_type=doc.content_type or "text/plain",
            tenant_id=doc.tenant_id,
        )

        knowledge_service.invalidate_cache(doc.kb_id)

        return new_version

    except Exception as e:
        logger.error("Failed to rebuild document index for %s: %s", document_id, e)
        raise
