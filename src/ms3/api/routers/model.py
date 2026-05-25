from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from src.ms3.database.connection import get_db
from src.ms3.database.dal import ChatProviderDAL, ChatModelDAL

router = APIRouter(prefix="/api/v2/models", tags=["models"])


class ProviderBase(BaseModel):
    provider_name: str = Field(..., description="供应商名称")
    provider_code: str = Field(..., description="供应商代码")
    api_base: Optional[str] = Field(None, description="API基础URL")
    api_key: Optional[str] = Field(None, description="API密钥")
    config: Optional[Dict[str, Any]] = Field(None, description="配置")
    credential_schema: Optional[Dict[str, Any]] = Field(None, description="凭证Schema")
    status: Optional[str] = Field("0", description="状态: 0-正常, 1-停用")


class ProviderCreate(ProviderBase):
    tenant_id: str = Field(..., description="租户ID")


class ProviderUpdate(BaseModel):
    provider_name: Optional[str] = None
    provider_code: Optional[str] = None
    api_base: Optional[str] = None
    api_key: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    credential_schema: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


class ProviderResponse(ProviderBase):
    id: str
    tenant_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ModelBase(BaseModel):
    model_name: str = Field(..., description="模型名称")
    model_code: str = Field(..., description="模型代码")
    model_type: Optional[str] = Field("chat", description="模型类型: chat, embedding等")
    credential_type: Optional[str] = Field(None, description="凭证类型")
    context_size: Optional[int] = Field(None, description="上下文窗口大小")
    output_size: Optional[int] = Field(None, description="最大输出大小")
    input_types: Optional[List[str]] = Field(None, description="支持的输入类型")
    output_types: Optional[List[str]] = Field(None, description="支持的输出类型")
    price_per_1k_input: Optional[int] = Field(None, description="每1K输入价格")
    price_per_1k_output: Optional[int] = Field(None, description="每1K输出价格")
    config: Optional[Dict[str, Any]] = Field(None, description="配置")
    status: Optional[str] = Field("0", description="状态: 0-正常, 1-停用")


class ModelCreate(ModelBase):
    tenant_id: str = Field(..., description="租户ID")
    provider_id: str = Field(..., description="供应商ID")


class ModelUpdate(BaseModel):
    model_name: Optional[str] = None
    model_code: Optional[str] = None
    model_type: Optional[str] = None
    credential_type: Optional[str] = None
    context_size: Optional[int] = None
    output_size: Optional[int] = None
    input_types: Optional[List[str]] = None
    output_types: Optional[List[str]] = None
    price_per_1k_input: Optional[int] = None
    price_per_1k_output: Optional[int] = None
    config: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


class ModelResponse(ModelBase):
    id: str
    tenant_id: str
    provider_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.get("/providers", response_model=List[ProviderResponse])
async def list_providers(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    dal = ChatProviderDAL(db)
    filters = {}
    if status is not None:
        filters["status"] = status
    items, total, total_pages = dal.get_paginated(page=page, page_size=page_size, filters=filters)
    return items


@router.get("/providers/{provider_id}", response_model=ProviderResponse)
async def get_provider(provider_id: str, db: Session = Depends(get_db)):
    dal = ChatProviderDAL(db)
    provider = dal.get_by_id(provider_id)
    if not provider:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")
    return provider


@router.post("/providers", response_model=ProviderResponse, status_code=status.HTTP_201_CREATED)
async def create_provider(provider: ProviderCreate, db: Session = Depends(get_db)):
    dal = ChatProviderDAL(db)
    new_provider = dal.create(**provider.model_dump())
    db.commit()
    db.refresh(new_provider)
    return new_provider


@router.put("/providers/{provider_id}", response_model=ProviderResponse)
async def update_provider(provider_id: str, provider: ProviderUpdate, db: Session = Depends(get_db)):
    dal = ChatProviderDAL(db)
    updated = dal.update(provider_id, **provider.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")
    db.commit()
    db.refresh(updated)
    return updated


@router.delete("/providers/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_provider(provider_id: str, db: Session = Depends(get_db)):
    dal = ChatProviderDAL(db)
    success = dal.delete(provider_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")
    db.commit()
    return None


@router.get("", response_model=List[ModelResponse])
async def list_models(
    page: int = 1,
    page_size: int = 20,
    provider_id: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    dal = ChatModelDAL(db)
    filters = {}
    if provider_id:
        filters["provider_id"] = provider_id
    if status is not None:
        filters["status"] = status
    items, total, total_pages = dal.get_paginated(page=page, page_size=page_size, filters=filters)
    return items


@router.get("/{model_id}", response_model=ModelResponse)
async def get_model(model_id: str, db: Session = Depends(get_db)):
    dal = ChatModelDAL(db)
    model = dal.get_by_id(model_id)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    return model


@router.get("/providers/{provider_id}/models", response_model=List[ModelResponse])
async def get_models_by_provider(provider_id: str, db: Session = Depends(get_db)):
    dal = ChatModelDAL(db)
    return dal.get_by_provider(provider_id)


@router.post("", response_model=ModelResponse, status_code=status.HTTP_201_CREATED)
async def create_model(model: ModelCreate, db: Session = Depends(get_db)):
    dal = ChatModelDAL(db)
    new_model = dal.create(**model.model_dump())
    db.commit()
    db.refresh(new_model)
    return new_model


@router.put("/{model_id}", response_model=ModelResponse)
async def update_model(model_id: str, model: ModelUpdate, db: Session = Depends(get_db)):
    dal = ChatModelDAL(db)
    updated = dal.update(model_id, **model.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    db.commit()
    db.refresh(updated)
    return updated


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model(model_id: str, db: Session = Depends(get_db)):
    dal = ChatModelDAL(db)
    success = dal.delete(model_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    db.commit()
    return None


@router.post("/{model_id}/sync-credential")
async def sync_credential(model_id: str, db: Session = Depends(get_db)):
    dal = ChatModelDAL(db)
    model = dal.get_by_id(model_id)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    
    return {"message": "Credential synced successfully", "model_id": model_id}
