import uuid
import logging
from datetime import datetime
from typing import Any

from ms3.common.config import settings
from ms3.knowledge.service import knowledge_service

logger = logging.getLogger(__name__)


async def _update_document_status(document_id: str, status: str, error_message: str | None = None) -> None:
    from ms3.database.connection import async_session_factory
    from ms3.database.dal import KnowledgeDocumentDAL

    try:
        async with async_session_factory() as session:
            dal = KnowledgeDocumentDAL(session=session, tenant_id=None)
            update_data: dict[str, Any] = {"parse_status": status, "updated_at": datetime.now()}
            if error_message is not None:
                update_data["error_message"] = error_message
            await dal.update(document_id, **update_data)
            await session.commit()
    except Exception as e:
        logger.error("Failed to update document %s status: %s", document_id, e)


def _parse_file(file_path: str, content_type: str) -> list[dict]:
    docs: list[dict] = []

    if content_type and content_type.startswith("image/"):
        try:
            from agentscope.rag import ImageReader

            reader = ImageReader()
            result = reader.load(file_path)
            for item in result:
                docs.append({
                    "content": item.get("content", "") if isinstance(item, dict) else str(item),
                    "source": file_path,
                    "page": 0,
                })
        except Exception as e:
            logger.error("ImageReader failed for %s: %s", file_path, e)
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                docs.append({"content": content, "source": file_path, "page": 0})
            except Exception as e2:
                logger.error("Fallback text read failed for %s: %s", file_path, e2)
    else:
        try:
            from agentscope.rag import TextReader

            reader = TextReader()
            result = reader.load(file_path)
            for item in result:
                docs.append({
                    "content": item.get("content", "") if isinstance(item, dict) else str(item),
                    "source": file_path,
                    "page": item.get("page", 0) if isinstance(item, dict) else 0,
                })
        except Exception as e:
            logger.error("TextReader failed for %s: %s", file_path, e)
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                docs.append({"content": content, "source": file_path, "page": 0})
            except Exception as e2:
                logger.error("Fallback text read failed for %s: %s", file_path, e2)

    return docs


def _chunk_documents(docs: list[dict], chunk_size: int = 512) -> list[dict]:
    chunks: list[dict] = []
    chunk_overlap = min(chunk_size // 5, 64)

    for doc in docs:
        content = doc.get("content", "")
        source = doc.get("source", "")
        page = doc.get("page", 0)

        if not content:
            continue

        start = 0
        chunk_index = 0
        while start < len(content):
            end = start + chunk_size
            chunk_text = content[start:end]
            chunks.append({
                "content": chunk_text,
                "source": source,
                "page": page,
                "chunk_index": chunk_index,
            })
            chunk_index += 1
            start += chunk_size - chunk_overlap
            if start >= len(content):
                break

    return chunks


async def _embed_and_store(kb_id: str, chunks: list[dict], document_id: str, tenant_id: str) -> int:
    from ms3.database.connection import async_session_factory
    from ms3.database.dal import KnowledgeBaseDAL, KnowledgeChunkDAL

    try:
        async with async_session_factory() as session:
            kb_dal = KnowledgeBaseDAL(session=session, tenant_id=tenant_id)
            kb = await kb_dal.get(kb_id)

            knowledge = knowledge_service._get_or_create(kb_id, kb)

            stored_count = 0
            chunk_dal = KnowledgeChunkDAL(session=session, tenant_id=tenant_id)

            for chunk_data in chunks:
                chunk_id = uuid.uuid4().hex
                content = chunk_data["content"]
                metadata = {
                    "source": chunk_data.get("source", ""),
                    "page": chunk_data.get("page", 0),
                    "document_id": document_id,
                    "chunk_index": chunk_data.get("chunk_index", 0),
                }

                vector_id = None
                try:
                    if hasattr(knowledge, "add_texts"):
                        ids = await knowledge.add_texts(
                            texts=[content],
                            metadatas=[metadata],
                        )
                        vector_id = ids[0] if ids else None
                    elif hasattr(knowledge, "store") and hasattr(knowledge.store, "upsert"):
                        embedding = knowledge.embedding_model
                        if hasattr(embedding, "embed"):
                            vectors = await embedding.embed([content])
                        elif hasattr(embedding, "encode"):
                            vectors = embedding.encode([content])
                        else:
                            vectors = [None]

                        vector = vectors[0] if vectors else None
                        if vector is not None:
                            point_id = await knowledge.store.upsert(
                                ids=[chunk_id],
                                vectors=[vector],
                                payloads=[metadata],
                            )
                            vector_id = chunk_id
                except Exception as e:
                    logger.error("Failed to embed/store chunk %s: %s", chunk_id, e)
                    vector_id = None

                await chunk_dal.create(
                    id=chunk_id,
                    document_id=document_id,
                    kb_id=kb_id,
                    tenant_id=tenant_id,
                    chunk_index=chunk_data.get("chunk_index", 0),
                    content=content,
                    metadata_json=metadata,
                    vector_id=vector_id,
                    created_at=datetime.now(),
                )
                stored_count += 1

            await session.commit()
            return stored_count

    except Exception as e:
        logger.error("Failed to embed and store for kb %s: %s", kb_id, e)
        raise


async def ingest_document(kb_id: str, file_path: str, content_type: str, tenant_id: str) -> str:
    from ms3.database.connection import async_session_factory
    from ms3.database.dal import KnowledgeDocumentDAL, KnowledgeBaseDAL

    document_id = uuid.uuid4().hex

    try:
        async with async_session_factory() as session:
            kb_dal = KnowledgeBaseDAL(session=session, tenant_id=tenant_id)
            kb = await kb_dal.get(kb_id)
            chunk_size = kb.chunk_size if kb else 512

            doc_dal = KnowledgeDocumentDAL(session=session, tenant_id=tenant_id)
            await doc_dal.create(
                id=document_id,
                kb_id=kb_id,
                tenant_id=tenant_id,
                filename=file_path.split("/")[-1] if "/" in file_path else file_path,
                content_type=content_type,
                storage_path=file_path,
                parse_status="pending",
                chunk_count=0,
                version=1,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            await session.commit()
    except Exception as e:
        logger.error("Failed to create document record: %s", e)
        raise

    await _update_document_status(document_id, "parsing")

    try:
        docs = _parse_file(file_path, content_type)
        if not docs:
            await _update_document_status(document_id, "failed", error_message="No content parsed from file")
            return document_id

        await _update_document_status(document_id, "chunking")

        chunks = _chunk_documents(docs, chunk_size=chunk_size)
        if not chunks:
            await _update_document_status(document_id, "failed", error_message="No chunks produced")
            return document_id

        await _update_document_status(document_id, "embedding")

        stored_count = await _embed_and_store(kb_id, chunks, document_id, tenant_id)

        async with async_session_factory() as session:
            doc_dal = KnowledgeDocumentDAL(session=session, tenant_id=tenant_id)
            await doc_dal.update(document_id, chunk_count=stored_count, parse_status="completed", updated_at=datetime.now())
            await session.commit()

        return document_id

    except Exception as e:
        logger.error("Document ingestion failed for %s: %s", document_id, e)
        await _update_document_status(document_id, "failed", error_message=str(e))
        return document_id


async def retry_failed_document(document_id: str) -> str | None:
    from ms3.database.connection import async_session_factory
    from ms3.database.dal import KnowledgeDocumentDAL

    try:
        async with async_session_factory() as session:
            doc_dal = KnowledgeDocumentDAL(session=session, tenant_id=None)
            doc = await doc_dal.get(document_id)

            if doc.parse_status != "failed":
                return None

            await session.commit()

        return await ingest_document(
            kb_id=doc.kb_id,
            file_path=doc.storage_path,
            content_type=doc.content_type or "text/plain",
            tenant_id=doc.tenant_id,
        )

    except Exception as e:
        logger.error("Retry failed for document %s: %s", document_id, e)
        await _update_document_status(document_id, "failed", error_message=f"Retry failed: {e}")
        return None
