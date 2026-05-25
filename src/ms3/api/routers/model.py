from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from ms3.auth.dependencies import get_current_user_id, get_current_tenant_id
from ms3.auth.rbac import require_permission
from ms3.common.pagination import PageRequest, PageResponse
from ms3.database.connection import get_db
from ms3.database.dal import ChatProviderDAL, ChatModelDAL

router = APIRouter(tags=["models"])


class ProviderCreate(BaseModel):
    provider_code: str
    provider_name: str
    description: str | None = None
    api_base: str | None = None
    status: str | None = None
    credential_schema: dict | None = None


class ProviderUpdate(BaseModel):
    provider_code: str | None = None
    provider_name: str | None = None
    description: str | None = None
    api_base: str | None = None
    status: str | None = None
    credential_schema: dict | None = None


class ProviderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    provider_code: str
    provider_name: str
    description: str | None
    api_base: str | None
    status: str | None
    credential_schema: dict | None
    created_at: datetime | None
    updated_at: datetime | None


class ModelCreate(BaseModel):
    provider_id: str | None = None
    model_code: str
    model_name: str
    description: str | None = None
    api_key: str | None = None
    api_base: str | None = None
    is_default: int | None = 0
    status: str | None = None
    credential_type: str | None = None
    context_size: int | None = None
    output_size: int | None = None
    input_types: dict | None = None
    output_types: dict | None = None


class ModelUpdate(BaseModel):
    provider_id: str | None = None
    model_code: str | None = None
    model_name: str | None = None
    description: str | None = None
    api_key: str | None = None
    api_base: str | None = None
    is_default: int | None = None
    status: str | None = None
    credential_type: str | None = None
    context_size: int | None = None
    output_size: int | None = None
    input_types: dict | None = None
    output_types: dict | None = None


class ModelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    provider_id: str | None
    model_code: str
    model_name: str
    description: str | None
    api_key: str | None
    api_base: str | None
    is_default: int | None
    status: str | None
    credential_type: str | None
    context_size: int | None
    output_size: int | None
    input_types: dict | None
    output_types: dict | None
    created_at: datetime | None
    updated_at: datetime | None


@router.get("/providers", response_model=PageResponse[ProviderResponse])
async def list_providers(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("model:list")),
):
    dal = ChatProviderDAL(session=db, tenant_id=tenant_id)
    page_req = PageRequest(page=page, page_size=page_size)
    result = await dal.list_paginated(page_req)
    items = [ProviderResponse.model_validate(item) for item in result.items]
    return PageResponse(
        items=items,
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
    )


@router.post("/providers", response_model=ProviderResponse, status_code=201)
async def create_provider(
    body: ProviderCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("model:create")),
):
    dal = ChatProviderDAL(session=db, tenant_id=tenant_id)
    data = body.model_dump(exclude_none=True)
    instance = await dal.create(**data)
    return ProviderResponse.model_validate(instance)


@router.get("/providers/{provider_id}", response_model=ProviderResponse)
async def get_provider(
    provider_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("model:read")),
):
    dal = ChatProviderDAL(session=db, tenant_id=tenant_id)
    instance = await dal.get(provider_id)
    return ProviderResponse.model_validate(instance)


@router.put("/providers/{provider_id}", response_model=ProviderResponse)
async def update_provider(
    provider_id: str,
    body: ProviderUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("model:update")),
):
    dal = ChatProviderDAL(session=db, tenant_id=tenant_id)
    data = body.model_dump(exclude_none=True)
    instance = await dal.update(provider_id, **data)
    return ProviderResponse.model_validate(instance)


@router.delete("/providers/{provider_id}", status_code=204)
async def delete_provider(
    provider_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("model:delete")),
):
    dal = ChatProviderDAL(session=db, tenant_id=tenant_id)
    await dal.delete(provider_id)


@router.get("/models", response_model=PageResponse[ModelResponse])
async def list_models(
    provider_id: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("model:list")),
):
    dal = ChatModelDAL(session=db, tenant_id=tenant_id)
    page_req = PageRequest(page=page, page_size=page_size)
    result = await dal.list_paginated(page_req, provider_id=provider_id)
    items = [ModelResponse.model_validate(item) for item in result.items]
    return PageResponse(
        items=items,
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
    )


@router.post("/models", response_model=ModelResponse, status_code=201)
async def create_model(
    body: ModelCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("model:create")),
):
    dal = ChatModelDAL(session=db, tenant_id=tenant_id)
    data = body.model_dump(exclude_none=True)
    instance = await dal.create(**data)
    return ModelResponse.model_validate(instance)


@router.get("/models/{model_id}", response_model=ModelResponse)
async def get_model(
    model_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("model:read")),
):
    dal = ChatModelDAL(session=db, tenant_id=tenant_id)
    instance = await dal.get(model_id)
    return ModelResponse.model_validate(instance)


@router.put("/models/{model_id}", response_model=ModelResponse)
async def update_model(
    model_id: str,
    body: ModelUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("model:update")),
):
    dal = ChatModelDAL(session=db, tenant_id=tenant_id)
    data = body.model_dump(exclude_none=True)
    instance = await dal.update(model_id, **data)
    return ModelResponse.model_validate(instance)


@router.delete("/models/{model_id}", status_code=204)
async def delete_model(
    model_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("model:delete")),
):
    dal = ChatModelDAL(session=db, tenant_id=tenant_id)
    await dal.delete(model_id)
