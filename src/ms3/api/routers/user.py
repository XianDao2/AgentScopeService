from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
import uuid
from passlib.context import CryptContext

from src.ms3.database.connection import get_db
from src.ms3.database.dal import SysUserDAL, SysRoleDAL, SysUserRoleDAL
from src.ms3.models.sys import SysUser, SysRole, SysUserRole
from src.ms3.auth.jwt_auth import create_access_token, create_refresh_token, decode_token

router = APIRouter(prefix="/api/v2/users", tags=["users"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


class UserBase(BaseModel):
    username: str = Field(..., description="用户名")
    nickname: Optional[str] = Field(None, description="昵称")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, description="手机号")
    avatar: Optional[str] = Field(None, description="头像")
    status: Optional[str] = Field("0", description="状态: 0-正常, 1-停用")


class UserCreate(UserBase):
    password: str = Field(..., description="密码")
    tenant_id: str = Field(..., description="租户ID")


class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None
    status: Optional[str] = None


class UserPasswordUpdate(BaseModel):
    old_password: str
    new_password: str


class UserResponse(UserBase):
    id: str
    tenant_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    username: str
    password: str
    tenant_id: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    dal = SysUserDAL(db)
    user = dal.get_by_username(credentials.username, credentials.tenant_id)
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    if user.status != "0":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    access_token = create_access_token(data={"sub": user.id, "tenant_id": user.tenant_id})
    refresh_token = create_refresh_token(data={"sub": user.id})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "tenant_id": user.tenant_id
        }
    )


@router.post("/refresh")
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    payload = decode_token(refresh_token)
    dal = SysUserDAL(db)
    user = dal.get_by_id(payload.get("sub"))
    
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    new_access_token = create_access_token(data={"sub": user.id, "tenant_id": user.tenant_id})
    return {"access_token": new_access_token, "token_type": "bearer"}


@router.post("/logout")
async def logout():
    return {"message": "Successfully logged out"}


@router.get("", response_model=List[UserResponse])
async def list_users(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    dal = SysUserDAL(db)
    filters = {}
    if status is not None:
        filters["status"] = status
    items, total, total_pages = dal.get_paginated(page=page, page_size=page_size, filters=filters)
    return items


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, db: Session = Depends(get_db)):
    dal = SysUserDAL(db)
    user = dal.get_with_roles(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    dal = SysUserDAL(db)
    existing = dal.get_by_username(user.username, user.tenant_id)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
    
    hashed_password = get_password_hash(user.password)
    user_data = user.model_dump(exclude={"password"})
    user_data["password_hash"] = hashed_password
    
    new_user = dal.create(**user_data)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user: UserUpdate, db: Session = Depends(get_db)):
    dal = SysUserDAL(db)
    updated = dal.update(user_id, **user.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    db.commit()
    db.refresh(updated)
    return updated


@router.put("/{user_id}/password")
async def update_user_password(user_id: str, password_update: UserPasswordUpdate, db: Session = Depends(get_db)):
    dal = SysUserDAL(db)
    user = dal.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if not verify_password(password_update.old_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Old password is incorrect")
    
    hashed_password = get_password_hash(password_update.new_password)
    dal.update(user_id, password_hash=hashed_password)
    db.commit()
    return {"message": "Password updated successfully"}


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, db: Session = Depends(get_db)):
    dal = SysUserDAL(db)
    success = dal.delete(user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    db.commit()
    return None


@router.post("/{user_id}/roles/{role_id}")
async def assign_role_to_user(user_id: str, role_id: str, db: Session = Depends(get_db)):
    user_dal = SysUserDAL(db)
    role_dal = SysRoleDAL(db)
    
    user = user_dal.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    role = role_dal.get_by_id(role_id, tenant_id=user.tenant_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    
    existing = db.query(SysUserRole).filter(
        SysUserRole.user_id == user_id,
        SysUserRole.role_id == role_id
    ).first()
    
    if not existing:
        db.add(SysUserRole(user_id=user_id, role_id=role_id))
        db.commit()
    
    return {"message": "Role assigned successfully"}


@router.delete("/{user_id}/roles/{role_id}")
async def remove_role_from_user(user_id: str, role_id: str, db: Session = Depends(get_db)):
    relation = db.query(SysUserRole).filter(
        SysUserRole.user_id == user_id,
        SysUserRole.role_id == role_id
    ).first()
    
    if not relation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relation not found")
    
    db.delete(relation)
    db.commit()
    return {"message": "Role removed successfully"}
