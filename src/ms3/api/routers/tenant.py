from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

from src.ms3.database.connection import get_db
from src.ms3.database.dal import SysTenantDAL, SysUserDAL
from src.ms3.models.sys import SysTenant, SysUser

router = APIRouter(prefix="/api/v2/tenants", tags=["tenants"])


class TenantBase(BaseModel):
    name: str = Field(..., description="租户名称")
    status: Optional[str] = Field("0", description="状态: 0-正常, 1-停用")
    skills_dir: Optional[str] = Field(None, description="技能目录")
    work_dir: Optional[str] = Field(None, description="工作目录")
    max_skills: Optional[int] = Field(100, description="最大技能数")
    max_concurrent_executions: Optional[int] = Field(50, description="最大并发执行数")
    metadata: Optional[dict] = Field(None, description="元数据")


class TenantCreate(TenantBase):
    pass


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    skills_dir: Optional[str] = None
    work_dir: Optional[str] = None
    max_skills: Optional[int] = None
    max_concurrent_executions: Optional[int] = None
    metadata: Optional[dict] = None


class TenantResponse(TenantBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=List[TenantResponse])
async def list_tenants(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    dal = SysTenantDAL(db)
    filters = {}
    if status is not None:
        filters["status"] = status
    items, total, total_pages = dal.get_paginated(page=page, page_size=page_size, filters=filters)
    return items


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(tenant_id: str, db: Session = Depends(get_db)):
    dal = SysTenantDAL(db)
    tenant = dal.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    return tenant


@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(tenant: TenantCreate, db: Session = Depends(get_db)):
    dal = SysTenantDAL(db)
    existing = dal.get_by_name(tenant.name)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant name already exists")
    new_tenant = dal.create(**tenant.model_dump())
    db.commit()
    db.refresh(new_tenant)
    return new_tenant


@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(tenant_id: str, tenant: TenantUpdate, db: Session = Depends(get_db)):
    dal = SysTenantDAL(db)
    updated = dal.update(tenant_id, **tenant.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    db.commit()
    db.refresh(updated)
    return updated


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(tenant_id: str, db: Session = Depends(get_db)):
    dal = SysTenantDAL(db)
    success = dal.delete(tenant_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    db.commit()
    return None


@router.get("/{tenant_id}/users", response_model=List[dict])
async def list_tenant_users(tenant_id: str, db: Session = Depends(get_db)):
    dal = SysUserDAL(db)
    users = dal.get_all(tenant_id=tenant_id)
    return [{"id": u.id, "username": u.username, "status": u.status, "created_at": u.created_at} for u in users]
