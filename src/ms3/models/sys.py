import uuid
from datetime import datetime

from sqlalchemy import CHAR, DateTime, Index, JSON, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class SysTenant(Base):
    __tablename__ = "sys_tenant"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    name: Mapped[str | None] = mapped_column(String(100), default=None)
    status: Mapped[str | None] = mapped_column(CHAR(1), default="0")
    skills_dir: Mapped[str | None] = mapped_column(String(255), default=None)
    work_dir: Mapped[str | None] = mapped_column(String(255), default=None)
    max_skills: Mapped[int | None] = mapped_column(default=10)
    max_concurrent_executions: Mapped[int | None] = mapped_column(default=50)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, default=None)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    del_flag: Mapped[str | None] = mapped_column(CHAR(1), default="0")


class SysUser(Base):
    __tablename__ = "sys_user"
    __table_args__ = (
        UniqueConstraint("tenant_id", "username", name="idx_tenant_username"),
        Index("idx_tenant_id", "tenant_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(100), default=None)
    email: Mapped[str | None] = mapped_column(String(100), default=None)
    phone: Mapped[str | None] = mapped_column(String(20), default=None)
    avatar: Mapped[str | None] = mapped_column(String(255), default=None)
    is_active: Mapped[int | None] = mapped_column(default=1)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    del_flag: Mapped[str | None] = mapped_column(CHAR(1), default="0")


class SysRole(Base):
    __tablename__ = "sys_role"
    __table_args__ = (Index("idx_tenant_id", "tenant_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    role_name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(String(200), default=None)
    status: Mapped[str | None] = mapped_column(CHAR(1), default="0")
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    del_flag: Mapped[str | None] = mapped_column(CHAR(1), default="0")


class SysPermission(Base):
    __tablename__ = "sys_permission"
    __table_args__ = (UniqueConstraint("code", name="code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(20), default=None)
    action: Mapped[str | None] = mapped_column(String(20), default=None)
    description: Mapped[str | None] = mapped_column(String(200), default=None)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)


class SysUserRole(Base):
    __tablename__ = "sys_user_role"
    __table_args__ = (
        Index("idx_user_id", "user_id"),
        Index("idx_role_id", "role_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    role_id: Mapped[str] = mapped_column(String(36), nullable=False)


class SysRolePermission(Base):
    __tablename__ = "sys_role_permission"
    __table_args__ = (
        Index("idx_role_id", "role_id"),
        Index("idx_permission_id", "permission_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    role_id: Mapped[str] = mapped_column(String(36), nullable=False)
    permission_id: Mapped[str] = mapped_column(String(36), nullable=False)
