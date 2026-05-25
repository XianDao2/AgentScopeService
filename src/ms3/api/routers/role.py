from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from src.ms3.database.connection import get_db
from src.ms3.database.dal import SysRoleDAL, SysPermissionDAL, SysRolePermissionDAL
from src.ms3.models.sys import SysRole, SysPermission, SysRolePermission

router = APIRouter(prefix="/api/v2/roles", tags=["roles"])


class RoleBase(BaseModel):
    role_name: str = Field(..., description="角色名称")
    role_code: str = Field(..., description="角色代码")
    description: Optional[str] = Field(None, description="描述")
    status: Optional[str] = Field("0", description="状态: 0-正常, 1-停用")


class RoleCreate(RoleBase):
    tenant_id: str = Field(..., description="租户ID")


class RoleUpdate(BaseModel):
    role_name: Optional[str] = None
    role_code: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class RoleResponse(RoleBase):
    id: str
    tenant_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PermissionBase(BaseModel):
    permission_code: str = Field(..., description="权限代码")
    permission_name: str = Field(..., description="权限名称")
    resource_type: Optional[str] = Field(None, description="资源类型")
    action: Optional[str] = Field(None, description="操作类型")
    description: Optional[str] = Field(None, description="描述")


class PermissionCreate(PermissionBase):
    pass


class PermissionResponse(PermissionBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=List[RoleResponse])
async def list_roles(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    dal = SysRoleDAL(db)
    filters = {}
    if status is not None:
        filters["status"] = status
    items, total, total_pages = dal.get_paginated(page=page, page_size=page_size, filters=filters)
    return items


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(role_id: str, db: Session = Depends(get_db)):
    dal = SysRoleDAL(db)
    role = dal.get_with_permissions(role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return role


@router.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(role: RoleCreate, db: Session = Depends(get_db)):
    dal = SysRoleDAL(db)
    new_role = dal.create(**role.model_dump())
    db.commit()
    db.refresh(new_role)
    return new_role


@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(role_id: str, role: RoleUpdate, db: Session = Depends(get_db)):
    dal = SysRoleDAL(db)
    updated = dal.update(role_id, **role.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    db.commit()
    db.refresh(updated)
    return updated


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(role_id: str, db: Session = Depends(get_db)):
    dal = SysRoleDAL(db)
    success = dal.delete(role_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    db.commit()
    return None


@router.post("/{role_id}/permissions/{permission_id}")
async def assign_permission_to_role(role_id: str, permission_id: str, db: Session = Depends(get_db)):
    role_dal = SysRoleDAL(db)
    perm_dal = SysPermissionDAL(db)
    
    role = role_dal.get_by_id(role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    
    permission = perm_dal.get_by_id(permission_id)
    if not permission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")
    
    existing = db.query(SysRolePermission).filter(
        SysRolePermission.role_id == role_id,
        SysRolePermission.permission_id == permission_id
    ).first()
    
    if not existing:
        db.add(SysRolePermission(role_id=role_id, permission_id=permission_id))
        db.commit()
    
    return {"message": "Permission assigned successfully"}


@router.delete("/{role_id}/permissions/{permission_id}")
async def remove_permission_from_role(role_id: str, permission_id: str, db: Session = Depends(get_db)):
    relation = db.query(SysRolePermission).filter(
        SysRolePermission.role_id == role_id,
        SysRolePermission.permission_id == permission_id
    ).first()
    
    if not relation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relation not found")
    
    db.delete(relation)
    db.commit()
    return {"message": "Permission removed successfully"}


@router.get("/permissions/list", response_model=List[PermissionResponse])
async def list_permissions(db: Session = Depends(get_db)):
    dal = SysPermissionDAL(db)
    return dal.get_all()


@router.post("/permissions", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED)
async def create_permission(permission: PermissionCreate, db: Session = Depends(get_db)):
    dal = SysPermissionDAL(db)
    existing = dal.get_by_code(permission.permission_code)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Permission code already exists")
    new_perm = dal.create(**permission.model_dump())
    db.commit()
    db.refresh(new_perm)
    return new_perm
