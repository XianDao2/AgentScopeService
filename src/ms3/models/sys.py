from sqlalchemy import Column, String, Integer, Text, JSON, ForeignKey, BigInteger
from sqlalchemy.orm import relationship

from src.ms3.database.connection import Base
from src.ms3.models.base import BaseModel


class SysTenant(Base, BaseModel):
    __tablename__ = "sys_tenant"

    name = Column(String(100), nullable=False)
    status = Column(String(1), nullable=False, default="0")
    skills_dir = Column(String(255), nullable=True)
    work_dir = Column(String(255), nullable=True)
    max_skills = Column(Integer, nullable=False, default=100)
    max_concurrent_executions = Column(Integer, nullable=False, default=50)
    tenant_metadata = Column(JSON, nullable=True)
    del_flag = Column(String(1), nullable=False, default="0")

    users = relationship("SysUser", back_populates="tenant")
    roles = relationship("SysRole", back_populates="tenant")


class SysUser(Base, BaseModel):
    __tablename__ = "sys_user"

    tenant_id = Column(String(36), ForeignKey("sys_tenant.id"), nullable=False, index=True)
    username = Column(String(50), nullable=False)
    password_hash = Column(String(255), nullable=False)
    nickname = Column(String(50), nullable=True)
    email = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    avatar = Column(String(255), nullable=True)
    status = Column(String(1), nullable=False, default="0")
    del_flag = Column(String(1), nullable=False, default="0")

    tenant = relationship("SysTenant", back_populates="users")
    roles = relationship("SysRole", secondary="sys_user_role", back_populates="users")


class SysRole(Base, BaseModel):
    __tablename__ = "sys_role"

    tenant_id = Column(String(36), ForeignKey("sys_tenant.id"), nullable=False, index=True)
    role_name = Column(String(50), nullable=False)
    role_code = Column(String(50), nullable=False)
    description = Column(String(500), nullable=True)
    status = Column(String(1), nullable=False, default="0")
    del_flag = Column(String(1), nullable=False, default="0")

    tenant = relationship("SysTenant", back_populates="roles")
    users = relationship("SysUser", secondary="sys_user_role", back_populates="roles")
    permissions = relationship("SysPermission", secondary="sys_role_permission", back_populates="roles")


class SysPermission(Base, BaseModel):
    __tablename__ = "sys_permission"

    permission_code = Column(String(100), nullable=False, unique=True)
    permission_name = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=True)
    action = Column(String(50), nullable=True)
    description = Column(String(500), nullable=True)

    roles = relationship("SysRole", secondary="sys_role_permission", back_populates="permissions")


class SysUserRole(Base):
    __tablename__ = "sys_user_role"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("sys_user.id"), nullable=False)
    role_id = Column(String(36), ForeignKey("sys_role.id"), nullable=False)


class SysRolePermission(Base):
    __tablename__ = "sys_role_permission"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    role_id = Column(String(36), ForeignKey("sys_role.id"), nullable=False)
    permission_id = Column(String(36), ForeignKey("sys_permission.id"), nullable=False)
