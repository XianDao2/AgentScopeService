#!/usr/bin/env python3
"""
Database initialization script
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import uuid
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

from src.ms3.common.config import get_settings
from src.ms3.models.sys import SysTenant, SysUser, SysRole
from src.ms3.models.chat import ChatSession, ChatMessage

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def init_database():
    settings = get_settings()
    engine = create_engine(settings.mysql_dsn, echo=True)

    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Create default tenant
        tenant = SysTenant(
            id=str(uuid.uuid4()),
            name="Default Tenant",
            status="0",
            max_skills=100,
            max_concurrent_executions=50,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            del_flag="0"
        )
        session.add(tenant)
        session.flush()

        # Create default role
        role = SysRole(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            role_name="Admin",
            role_code="admin",
            description="Administrator role",
            status="0",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            del_flag="0"
        )
        session.add(role)
        session.flush()

        # Create default user
        user = SysUser(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            username="admin",
            password_hash=pwd_context.hash("admin123"),
            nickname="Administrator",
            email="admin@example.com",
            status="0",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            del_flag="0"
        )
        session.add(user)
        session.flush()

        # Add user to role
        from src.ms3.models.sys import SysUserRole
        user_role = SysUserRole(
            user_id=user.id,
            role_id=role.id
        )
        session.add(user_role)

        session.commit()
        print("Database initialized successfully!")
        print(f"Tenant ID: {tenant.id}")
        print(f"User: admin / admin123")

    except Exception as e:
        session.rollback()
        print(f"Error initializing database: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    init_database()
