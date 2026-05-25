from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from src.ms3.database.connection import get_db
from src.ms3.database.dal import KnowledgeBaseDAL, KnowledgeDocumentDAL, KnowledgeChunkDAL

router = APIRouter(prefix="/api/v2/knowledge", tags=["knowledge"])


class KnowledgeBaseBase(BaseModel):
    name: str = Field(..., description="知识库名称")
    description: Optional[str] = Field(None, description="描述")
    embedding_model: Optional[str] = Field("text-embedding-v4", description="嵌入模型")
    embedding_api_key: Optional[str] = Field(None, description="嵌入API密钥")
    dimensions: Optional[int] = Field(1024, description="向量维度")
    qdrant_url: Optional[str] = Field(None, description="Qdrant地址")
    qdrant_collection: Optional[str] = Field(None, description="Qdrant集合名")
    retrieval_strategy: Optional[str] = Field("auto", description="检索策略: auto, agent-controlled")
    chunk_size: Optional[int] = Field(512, description="块大小")
    top_k: Optional[int] = Field(5, description="默认检索数量")
    score_threshold: Optional[float] = Field(0.5, description="分数阈值")
    visibility: Optional[str] = Field("tenant", description="可见性: private, tenant, public")
    allowed_roles: Optional[List[str]] = Field(None, description="允许的角色")
    status: Optional[str] = Field("0", description="状态: 0-正常, 1-停用")


class KnowledgeBaseCreate(KnowledgeBaseBase):
    tenant_id: str = Field(..., description="租户ID")


class KnowledgeBaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    embedding_model: Optional[str] = None
    embedding_api_key: Optional[str] = None
    dimensions: Optional[int] = None
    qdrant_url: Optional[str] = None
    qdrant_collection: Optional[str] = None
    retrieval_strategy: Optional[str] = None
    chunk_size: Optional[int] = None
    top_k: Optional[int] = None
    score_threshold: Optional[float] = None
    visibility: Optional[str] = None
    allowed_roles: Optional[List[str]] = None
    status: Optional[str] = None


class KnowledgeBaseResponse(KnowledgeBaseBase):
    id: str
    tenant_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentBase(BaseModel):
    filename: str = Field(..., description="文件名")
    original_filename: Optional[str] = Field(None, description="原始文件名")
    content_type: Optional[str] = Field(None, description="内容类型")
    storage_path: Optional[str] = Field(None, description="存储路径")
    file_size: Optional[int] = Field(None, description="文件大小")
    parse_status: Optional[str] = Field("pending", description="解析状态: pending, parsing, chunking, embedding, completed, failed")
    chunk_count: Optional[int] = Field(0, description="块数量")
    version: Optional[int] = Field(1, description="版本")
    error_message: Optional[str] = Field(None, description="错误信息")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class DocumentCreate(DocumentBase):
    kb_id: str = Field(..., description="知识库ID")
    tenant_id: str = Field(..., description="租户ID")


class DocumentUpdate(BaseModel):
    parse_status: Optional[str] = None
    chunk_count: Optional[int] = None
    version: Optional[int] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DocumentResponse(DocumentBase):
    id: str
    kb_id: str
    tenant_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChunkResponse(BaseModel):
    id: str
    document_id: str
    kb_id: str
    tenant_id: str
    chunk_index: int
    content: str
    metadata_json: Optional[dict]
    vector_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/bases", response_model=List[KnowledgeBaseResponse])
async def list_knowledge_bases(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    dal = KnowledgeBaseDAL(db)
    filters = {}
    if status is not None:
        filters["status"] = status
    items, total, total_pages = dal.get_paginated(page=page, page_size=page_size, filters=filters)
    return items


@router.get("/bases/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(kb_id: str, db: Session = Depends(get_db)):
    dal = KnowledgeBaseDAL(db)
    kb = dal.get_by_id(kb_id)
    if not kb:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found")
    return kb


@router.post("/bases", response_model=KnowledgeBaseResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge_base(kb: KnowledgeBaseCreate, db: Session = Depends(get_db)):
    dal = KnowledgeBaseDAL(db)
    new_kb = dal.create(**kb.model_dump())
    db.commit()
    db.refresh(new_kb)
    return new_kb


@router.put("/bases/{kb_id}", response_model=KnowledgeBaseResponse)
async def update_knowledge_base(kb_id: str, kb: KnowledgeBaseUpdate, db: Session = Depends(get_db)):
    dal = KnowledgeBaseDAL(db)
    updated = dal.update(kb_id, **kb.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found")
    db.commit()
    db.refresh(updated)
    return updated


@router.delete("/bases/{kb_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_base(kb_id: str, db: Session = Depends(get_db)):
    dal = KnowledgeBaseDAL(db)
    success = dal.delete(kb_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found")
    db.commit()
    return None


@router.get("/bases/{kb_id}/documents", response_model=List[DocumentResponse])
async def get_documents_by_kb(kb_id: str, db: Session = Depends(get_db)):
    dal = KnowledgeDocumentDAL(db)
    return dal.get_by_kb(kb_id)


@router.get("/documents/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: str, db: Session = Depends(get_db)):
    dal = KnowledgeDocumentDAL(db)
    doc = dal.get_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc


@router.post("/bases/{kb_id}/documents/upload")
async def upload_document(
    kb_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    return {"message": "Document uploaded successfully", "filename": file.filename}


@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(doc_id: str, db: Session = Depends(get_db)):
    dal = KnowledgeDocumentDAL(db)
    success = dal.delete(doc_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    db.commit()
    return None


@router.get("/documents/{doc_id}/chunks", response_model=List[ChunkResponse])
async def get_chunks_by_document(doc_id: str, db: Session = Depends(get_db)):
    dal = KnowledgeChunkDAL(db)
    return dal.get_by_document(doc_id)


@router.get("/bases/{kb_id}/chunks", response_model=List[ChunkResponse])
async def get_chunks_by_kb(kb_id: str, db: Session = Depends(get_db)):
    dal = KnowledgeChunkDAL(db)
    return dal.get_by_kb(kb_id)
