import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from ms3.auth.dependencies import get_current_user_id, get_current_tenant_id
from ms3.auth.rbac import require_permission
from ms3.common.config import settings
from ms3.common.pagination import PageRequest, PageResponse
from ms3.database.connection import get_db
from ms3.database.dal import KnowledgeBaseDAL, KnowledgeDocumentDAL, KnowledgeChunkDAL
from ms3.knowledge.service import knowledge_service

router = APIRouter(tags=["knowledge"])


class KBCreate(BaseModel):
    name: str
    description: str | None = None
    embedding_model: str | None = "text-embedding-v4"
    embedding_api_key: str | None = None
    dimensions: int | None = 1024
    qdrant_url: str | None = None
    qdrant_collection: str | None = None
    retrieval_strategy: str | None = "auto"
    chunk_size: int | None = 512
    top_k: int | None = 5
    score_threshold: float | None = 0.5
    visibility: str | None = "tenant"
    allowed_roles: dict | None = None


class KBUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    embedding_model: str | None = None
    embedding_api_key: str | None = None
    dimensions: int | None = None
    qdrant_url: str | None = None
    qdrant_collection: str | None = None
    retrieval_strategy: str | None = None
    chunk_size: int | None = None
    top_k: int | None = None
    score_threshold: float | None = None
    visibility: str | None = None
    allowed_roles: dict | None = None
    status: str | None = None


class KBResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    name: str
    description: str | None
    embedding_model: str
    dimensions: int
    qdrant_url: str | None
    qdrant_collection: str | None
    retrieval_strategy: str
    chunk_size: int
    top_k: int
    score_threshold: float
    visibility: str
    allowed_roles: dict | None
    status: str
    created_at: datetime
    updated_at: datetime


class KBStatsResponse(BaseModel):
    doc_count: int
    chunk_count: int
    index_status: str
    completed_docs: int = 0
    failed_docs: int = 0
    pending_docs: int = 0
    last_update: str | None = None


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    kb_id: str
    tenant_id: str
    filename: str
    content_type: str | None
    storage_path: str
    file_size: int | None
    parse_status: str
    chunk_count: int
    version: int
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class ChunkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    kb_id: str
    tenant_id: str
    chunk_index: int
    content: str
    metadata_json: dict | None
    vector_id: str | None
    created_at: datetime


@router.get("/kb", response_model=PageResponse[KBResponse])
async def list_knowledge_bases(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("kb:list")),
):
    dal = KnowledgeBaseDAL(session=db, tenant_id=tenant_id)
    page_req = PageRequest(page=page, page_size=page_size)
    result = await dal.list_paginated(page_req)
    items = [KBResponse.model_validate(item) for item in result.items]
    return PageResponse(
        items=items,
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
    )


@router.post("/kb", response_model=KBResponse, status_code=201)
async def create_knowledge_base(
    body: KBCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("kb:create")),
):
    dal = KnowledgeBaseDAL(session=db, tenant_id=tenant_id)
    data = body.model_dump(exclude_none=True)
    if "qdrant_collection" not in data:
        data["qdrant_collection"] = f"kb_{uuid.uuid4().hex[:12]}"
    instance = await dal.create(**data)

    try:
        knowledge_service.create_knowledge(instance)
    except Exception:
        pass

    return KBResponse.model_validate(instance)


@router.get("/kb/{kb_id}", response_model=KBResponse)
async def get_knowledge_base(
    kb_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("kb:read")),
):
    dal = KnowledgeBaseDAL(session=db, tenant_id=tenant_id)
    instance = await dal.get(kb_id)
    return KBResponse.model_validate(instance)


@router.put("/kb/{kb_id}", response_model=KBResponse)
async def update_knowledge_base(
    kb_id: str,
    body: KBUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("kb:update")),
):
    dal = KnowledgeBaseDAL(session=db, tenant_id=tenant_id)
    data = body.model_dump(exclude_none=True)
    instance = await dal.update(kb_id, **data)

    knowledge_service.invalidate_cache(kb_id)

    return KBResponse.model_validate(instance)


@router.delete("/kb/{kb_id}", status_code=204)
async def delete_knowledge_base(
    kb_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("kb:delete")),
):
    dal = KnowledgeBaseDAL(session=db, tenant_id=tenant_id)
    await dal.delete(kb_id)
    knowledge_service.invalidate_cache(kb_id)


@router.get("/kb/{kb_id}/stats", response_model=KBStatsResponse)
async def get_knowledge_base_stats(
    kb_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("kb:read")),
):
    dal = KnowledgeBaseDAL(session=db, tenant_id=tenant_id)
    await dal.get(kb_id)

    stats = await knowledge_service.get_stats(kb_id)
    return KBStatsResponse(**stats)


@router.post("/kb/{kb_id}/documents", response_model=DocumentResponse, status_code=201)
async def upload_document(
    kb_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("kb:upload")),
):
    dal = KnowledgeBaseDAL(session=db, tenant_id=tenant_id)
    kb = await dal.get(kb_id)

    upload_dir = os.path.join(settings.workspace_basedir, "kb_uploads", kb_id)
    os.makedirs(upload_dir, exist_ok=True)

    file_id = uuid.uuid4().hex
    filename = file.filename or "unknown"
    ext = os.path.splitext(filename)[1] if filename else ""
    storage_path = os.path.join(upload_dir, f"{file_id}{ext}")

    content = await file.read()
    with open(storage_path, "wb") as f:
        f.write(content)

    content_type = file.content_type or "application/octet-stream"

    from ms3.knowledge.ingest import ingest_document

    document_id = await ingest_document(
        kb_id=kb_id,
        file_path=storage_path,
        content_type=content_type,
        tenant_id=tenant_id,
    )

    doc_dal = KnowledgeDocumentDAL(session=db, tenant_id=tenant_id)
    doc = await doc_dal.get(document_id)
    return DocumentResponse.model_validate(doc)


@router.get("/kb/{kb_id}/documents", response_model=PageResponse[DocumentResponse])
async def list_documents(
    kb_id: str,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("kb:read")),
):
    dal = KnowledgeBaseDAL(session=db, tenant_id=tenant_id)
    await dal.get(kb_id)

    doc_dal = KnowledgeDocumentDAL(session=db, tenant_id=tenant_id)
    page_req = PageRequest(page=page, page_size=page_size)
    result = await doc_dal.list_by_kb(kb_id, page_req)
    items = [DocumentResponse.model_validate(item) for item in result.items]
    return PageResponse(
        items=items,
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
    )


@router.delete("/kb/{kb_id}/documents/{doc_id}", status_code=204)
async def delete_document(
    kb_id: str,
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("kb:delete")),
):
    from ms3.knowledge.version import delete_document_vectors

    doc_dal = KnowledgeDocumentDAL(session=db, tenant_id=tenant_id)
    doc = await doc_dal.get(doc_id)

    if doc.kb_id != kb_id:
        raise HTTPException(status_code=400, detail="Document does not belong to this knowledge base")

    await delete_document_vectors(doc_id)
    await doc_dal.hard_delete(doc_id)


@router.post("/kb/{kb_id}/documents/{doc_id}/retry", response_model=DocumentResponse)
async def retry_document(
    kb_id: str,
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("kb:upload")),
):
    from ms3.knowledge.ingest import retry_failed_document

    doc_dal = KnowledgeDocumentDAL(session=db, tenant_id=tenant_id)
    doc = await doc_dal.get(doc_id)

    if doc.kb_id != kb_id:
        raise HTTPException(status_code=400, detail="Document does not belong to this knowledge base")

    result_id = await retry_failed_document(doc_id)
    if result_id is None:
        raise HTTPException(status_code=400, detail="Document is not in failed state")

    doc = await doc_dal.get(result_id)
    return DocumentResponse.model_validate(doc)


@router.post("/kb/{kb_id}/documents/{doc_id}/rebuild")
async def rebuild_document(
    kb_id: str,
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("kb:upload")),
):
    from ms3.knowledge.version import rebuild_document_index

    doc_dal = KnowledgeDocumentDAL(session=db, tenant_id=tenant_id)
    doc = await doc_dal.get(doc_id)

    if doc.kb_id != kb_id:
        raise HTTPException(status_code=400, detail="Document does not belong to this knowledge base")

    new_version = await rebuild_document_index(doc_id)
    return {"document_id": doc_id, "new_version": new_version}


@router.get("/kb/{kb_id}/chunks", response_model=PageResponse[ChunkResponse])
async def list_chunks(
    kb_id: str,
    document_id: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("kb:read")),
):
    dal = KnowledgeBaseDAL(session=db, tenant_id=tenant_id)
    await dal.get(kb_id)

    chunk_dal = KnowledgeChunkDAL(session=db, tenant_id=tenant_id)
    page_req = PageRequest(page=page, page_size=page_size)

    filters: dict = {"kb_id": kb_id}
    if document_id:
        filters["document_id"] = document_id

    result = await chunk_dal.list_paginated(page_req, **filters)
    items = [ChunkResponse.model_validate(item) for item in result.items]
    return PageResponse(
        items=items,
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
    )
