from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional

from src.ms3.database.connection import get_db
from src.ms3.models.sys import SysUser, SysTenant
from src.ms3.auth.jwt_auth import (
    verify_password,
    create_access_token,
    create_refresh_token,
    get_password_hash,
)
from src.ms3.auth.dependencies import get_current_user

router = APIRouter(prefix="/api/v2/auth", tags=["认证"])


class LoginRequest(BaseModel):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
    tenant_id: Optional[str] = Field(None, description="租户ID")


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(SysUser).filter(
        SysUser.username == request.username,
        SysUser.del_flag == "0"
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    if request.tenant_id and user.tenant_id != request.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="租户不匹配"
        )

    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    if user.status != "0":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )

    tenant = db.query(SysTenant).filter(SysTenant.id == user.tenant_id).first()
    if tenant and tenant.status != "0":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="租户已被禁用"
        )

    data = {"sub": user.id, "tenant_id": user.tenant_id, "username": user.username}
    access_token = create_access_token(data=data)
    refresh_token = create_refresh_token(data=data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user={
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "email": user.email,
            "tenant_id": user.tenant_id
        }
    )


@router.get("/me")
async def get_current_user_info(current_user: SysUser = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "nickname": current_user.nickname,
        "email": current_user.email,
        "phone": current_user.phone,
        "avatar": current_user.avatar,
        "tenant_id": current_user.tenant_id
    }
