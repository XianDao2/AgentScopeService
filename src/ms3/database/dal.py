import math
import uuid
from datetime import datetime
from typing import Any, Generic, TypeVar

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ms3.common.exceptions import NotFoundException
from ms3.common.pagination import PageRequest, PageResponse
from ms3.models.chat import ChatMessage, ChatSession
from ms3.models.chat_model import ChatModel, ChatProvider
from ms3.models.platform import (
    AgentDefinition,
    ExecutionTrace,
    KnowledgeBase,
    KnowledgeChunk,
    KnowledgeDocument,
    ToolDefinition,
    ToolGroupDefinition,
)
from ms3.models.sys import Base, SysPermission, SysRole, SysRolePermission, SysTenant, SysUser, SysUserRole

M = TypeVar("M", bound=Base)


class BaseDAL(Generic[M]):
    model: type[M]
    tenant_isolated: bool = True
    soft_delete: bool = True

    def __init__(self, session: AsyncSession, tenant_id: str | None = None):
        self.session = session
        self.tenant_id = tenant_id

    def _apply_tenant_filter(self, stmt: Select) -> Select:
        if self.tenant_isolated and self.tenant_id and hasattr(self.model, "tenant_id"):
            stmt = stmt.where(self.model.tenant_id == self.tenant_id)
        return stmt

    def _apply_soft_delete_filter(self, stmt: Select) -> Select:
        if self.soft_delete and hasattr(self.model, "del_flag"):
            stmt = stmt.where(self.model.del_flag == "0")
        return stmt

    def _apply_base_filters(self, stmt: Select) -> Select:
        stmt = self._apply_tenant_filter(stmt)
        stmt = self._apply_soft_delete_filter(stmt)
        return stmt

    async def get(self, id: str) -> M:
        stmt = select(self.model).where(self.model.id == id)
        stmt = self._apply_base_filters(stmt)
        result = await self.session.execute(stmt)
        instance = result.scalar_one_or_none()
        if instance is None:
            raise NotFoundException(f"{self.model.__tablename__} not found: {id}")
        return instance

    async def get_or_none(self, id: str) -> M | None:
        stmt = select(self.model).where(self.model.id == id)
        stmt = self._apply_base_filters(stmt)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self, **filters: Any) -> list[M]:
        stmt = select(self.model)
        stmt = self._apply_base_filters(stmt)
        for key, value in filters.items():
            if hasattr(self.model, key) and value is not None:
                stmt = stmt.where(getattr(self.model, key) == value)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_paginated(self, page_request: PageRequest, **filters: Any) -> PageResponse[M]:
        count_stmt = select(func.count()).select_from(self.model)
        count_stmt = self._apply_base_filters(count_stmt)
        for key, value in filters.items():
            if hasattr(self.model, key) and value is not None:
                count_stmt = count_stmt.where(getattr(self.model, key) == value)
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar() or 0

        total_pages = math.ceil(total / page_request.page_size) if total > 0 else 0

        stmt = select(self.model)
        stmt = self._apply_base_filters(stmt)
        for key, value in filters.items():
            if hasattr(self.model, key) and value is not None:
                stmt = stmt.where(getattr(self.model, key) == value)
        offset = (page_request.page - 1) * page_request.page_size
        stmt = stmt.offset(offset).limit(page_request.page_size)
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())

        return PageResponse(
            items=items,
            total=total,
            page=page_request.page,
            page_size=page_request.page_size,
            total_pages=total_pages,
        )

    async def create(self, **data: Any) -> M:
        if "id" not in data:
            data["id"] = uuid.uuid4().hex
        if self.tenant_isolated and self.tenant_id and "tenant_id" not in data and hasattr(self.model, "tenant_id"):
            data["tenant_id"] = self.tenant_id
        now = datetime.now()
        if hasattr(self.model, "created_at") and "created_at" not in data:
            data["created_at"] = now
        if hasattr(self.model, "updated_at") and "updated_at" not in data:
            data["updated_at"] = now
        instance = self.model(**data)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def update(self, id: str, **data: Any) -> M:
        instance = await self.get(id)
        if hasattr(self.model, "updated_at") and "updated_at" not in data:
            data["updated_at"] = datetime.now()
        for key, value in data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        await self.session.flush()
        return instance

    async def _soft_delete(self, id: str) -> None:
        if not self.soft_delete or not hasattr(self.model, "del_flag"):
            raise NotImplementedError(f"{self.model.__tablename__} does not support soft delete")
        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(del_flag="1", updated_at=datetime.now())
        )
        stmt = self._apply_tenant_filter(stmt)
        await self.session.execute(stmt)
        await self.session.flush()

    async def hard_delete(self, id: str) -> None:
        instance = await self.get(id)
        await self.session.delete(instance)
        await self.session.flush()

    async def delete(self, id: str) -> None:
        if self.soft_delete and hasattr(self.model, "del_flag"):
            await self._soft_delete(id)
        else:
            await self.hard_delete(id)

    async def count(self, **filters: Any) -> int:
        stmt = select(func.count()).select_from(self.model)
        stmt = self._apply_base_filters(stmt)
        for key, value in filters.items():
            if hasattr(self.model, key) and value is not None:
                stmt = stmt.where(getattr(self.model, key) == value)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def exists(self, id: str) -> bool:
        stmt = select(func.count()).select_from(self.model).where(self.model.id == id)
        stmt = self._apply_base_filters(stmt)
        result = await self.session.execute(stmt)
        return (result.scalar() or 0) > 0


class SysTenantDAL(BaseDAL):
    model = SysTenant
    tenant_isolated = False
    soft_delete = True


class SysUserDAL(BaseDAL):
    model = SysUser
    tenant_isolated = True
    soft_delete = True

    async def get_by_username(self, tenant_id: str, username: str) -> SysUser | None:
        stmt = select(SysUser).where(
            SysUser.tenant_id == tenant_id,
            SysUser.username == username,
            SysUser.del_flag == "0",
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class SysRoleDAL(BaseDAL):
    model = SysRole
    tenant_isolated = True
    soft_delete = True


class SysPermissionDAL(BaseDAL):
    model = SysPermission
    tenant_isolated = False
    soft_delete = False

    async def get_by_code(self, code: str) -> SysPermission | None:
        stmt = select(SysPermission).where(SysPermission.code == code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class SysUserRoleDAL(BaseDAL):
    model = SysUserRole
    tenant_isolated = False
    soft_delete = False

    async def list_by_user(self, user_id: str) -> list[SysUserRole]:
        stmt = select(SysUserRole).where(SysUserRole.user_id == user_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_role(self, role_id: str) -> list[SysUserRole]:
        stmt = select(SysUserRole).where(SysUserRole.role_id == role_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class SysRolePermissionDAL(BaseDAL):
    model = SysRolePermission
    tenant_isolated = False
    soft_delete = False

    async def list_by_role(self, role_id: str) -> list[SysRolePermission]:
        stmt = select(SysRolePermission).where(SysRolePermission.role_id == role_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class ChatSessionDAL(BaseDAL):
    model = ChatSession
    tenant_isolated = True
    soft_delete = True

    async def list_by_user(self, user_id: str, page_request: PageRequest) -> PageResponse[ChatSession]:
        return await self.list_paginated(page_request, user_id=user_id)


class ChatMessageDAL(BaseDAL):
    model = ChatMessage
    tenant_isolated = False
    soft_delete = False

    async def list_by_session(self, session_id: str) -> list[ChatMessage]:
        stmt = select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class ChatProviderDAL(BaseDAL):
    model = ChatProvider
    tenant_isolated = True
    soft_delete = True

    async def get_by_code(self, provider_code: str) -> ChatProvider | None:
        stmt = select(ChatProvider).where(ChatProvider.provider_code == provider_code)
        stmt = self._apply_base_filters(stmt)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class ChatModelDAL(BaseDAL):
    model = ChatModel
    tenant_isolated = True
    soft_delete = True

    async def get_default(self) -> ChatModel | None:
        stmt = select(ChatModel).where(ChatModel.is_default == 1)
        stmt = self._apply_base_filters(stmt)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_provider(self, provider_id: str, page_request: PageRequest) -> PageResponse[ChatModel]:
        return await self.list_paginated(page_request, provider_id=provider_id)


class AgentDefinitionDAL(BaseDAL):
    model = AgentDefinition
    tenant_isolated = True
    soft_delete = True


class ToolGroupDefinitionDAL(BaseDAL):
    model = ToolGroupDefinition
    tenant_isolated = True
    soft_delete = True

    async def get_by_code(self, group_code: str) -> ToolGroupDefinition | None:
        stmt = select(ToolGroupDefinition).where(ToolGroupDefinition.group_code == group_code)
        stmt = self._apply_base_filters(stmt)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class ToolDefinitionDAL(BaseDAL):
    model = ToolDefinition
    tenant_isolated = True
    soft_delete = True

    async def list_by_group(self, group_id: str, page_request: PageRequest) -> PageResponse[ToolDefinition]:
        return await self.list_paginated(page_request, group_id=group_id)


class KnowledgeBaseDAL(BaseDAL):
    model = KnowledgeBase
    tenant_isolated = True
    soft_delete = True


class KnowledgeDocumentDAL(BaseDAL):
    model = KnowledgeDocument
    tenant_isolated = True
    soft_delete = False

    async def list_by_kb(self, kb_id: str, page_request: PageRequest) -> PageResponse[KnowledgeDocument]:
        return await self.list_paginated(page_request, kb_id=kb_id)


class KnowledgeChunkDAL(BaseDAL):
    model = KnowledgeChunk
    tenant_isolated = True
    soft_delete = False

    async def list_by_document(self, document_id: str) -> list[KnowledgeChunk]:
        stmt = select(KnowledgeChunk).where(KnowledgeChunk.document_id == document_id).order_by(KnowledgeChunk.chunk_index)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_kb(self, kb_id: str) -> list[KnowledgeChunk]:
        stmt = select(KnowledgeChunk).where(KnowledgeChunk.kb_id == kb_id).order_by(KnowledgeChunk.chunk_index)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class ExecutionTraceDAL(BaseDAL):
    model = ExecutionTrace
    tenant_isolated = True
    soft_delete = False

    async def list_by_session(self, session_id: str, page_request: PageRequest) -> PageResponse[ExecutionTrace]:
        return await self.list_paginated(page_request, session_id=session_id)

    async def list_by_agent(self, agent_id: str, page_request: PageRequest) -> PageResponse[ExecutionTrace]:
        return await self.list_paginated(page_request, agent_id=agent_id)
