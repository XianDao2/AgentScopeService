from sqlalchemy import and_, or_, desc, asc, func
from sqlalchemy.orm import Session, Query
from typing import TypeVar, Type, Optional, List, Dict, Any, Tuple
from contextvars import ContextVar
import logging

from src.ms3.models.sys import (
    SysTenant, SysUser, SysRole, SysPermission, SysUserRole, SysRolePermission
)
from src.ms3.models.chat import ChatProvider, ChatModel, ChatSession, ChatMessage
from src.ms3.models.platform import (
    AgentDefinition, ToolGroupDefinition, ToolDefinition,
    KnowledgeBase, KnowledgeDocument, KnowledgeChunk, ExecutionTrace
)
from src.ms3.middleware.tenant_context import get_current_tenant_id

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BaseDAL:
    model: Type[T]

    def __init__(self, db: Session):
        self.db = db

    def _apply_tenant_filter(self, query: Query, tenant_id: Optional[str] = None) -> Query:
        if hasattr(self.model, 'tenant_id') and tenant_id:
            return query.filter(self.model.tenant_id == tenant_id)
        if hasattr(self.model, 'tenant_id') and get_current_tenant_id():
            return query.filter(self.model.tenant_id == get_current_tenant_id())
        return query

    def _apply_soft_delete_filter(self, query: Query) -> Query:
        if hasattr(self.model, 'del_flag'):
            return query.filter(self.model.del_flag == '0')
        return query

    def get_by_id(self, id: str, tenant_id: Optional[str] = None) -> Optional[T]:
        query = self.db.query(self.model).filter(self.model.id == id)
        query = self._apply_tenant_filter(query, tenant_id)
        query = self._apply_soft_delete_filter(query)
        return query.first()

    def get_all(
        self,
        tenant_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = True
    ) -> List[T]:
        query = self.db.query(self.model)
        query = self._apply_tenant_filter(query, tenant_id)
        query = self._apply_soft_delete_filter(query)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)
        
        if order_by and hasattr(self.model, order_by):
            if order_desc:
                query = query.order_by(desc(getattr(self.model, order_by)))
            else:
                query = query.order_by(asc(getattr(self.model, order_by)))
        else:
            query = query.order_by(desc(self.model.created_at))
        
        return query.all()

    def get_paginated(
        self,
        tenant_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = True
    ) -> Tuple[List[T], int, int]:
        query = self.db.query(self.model)
        query = self._apply_tenant_filter(query, tenant_id)
        query = self._apply_soft_delete_filter(query)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)
        
        if order_by and hasattr(self.model, order_by):
            if order_desc:
                query = query.order_by(desc(getattr(self.model, order_by)))
            else:
                query = query.order_by(asc(getattr(self.model, order_by)))
        else:
            query = query.order_by(desc(self.model.created_at))
        
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        
        return items, total, total_pages

    def create(self, **kwargs) -> T:
        obj = self.model(**kwargs)
        self.db.add(obj)
        self.db.flush()
        return obj

    def update(self, id: str, tenant_id: Optional[str] = None, **kwargs) -> Optional[T]:
        obj = self.get_by_id(id, tenant_id)
        if obj:
            for key, value in kwargs.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)
            self.db.flush()
        return obj

    def delete(self, id: str, tenant_id: Optional[str] = None, soft: bool = True) -> bool:
        obj = self.get_by_id(id, tenant_id)
        if not obj:
            return False
        
        if soft and hasattr(self.model, 'del_flag'):
            obj.del_flag = '1'
        else:
            self.db.delete(obj)
        
        self.db.flush()
        return True


class SysTenantDAL(BaseDAL):
    model = SysTenant

    def get_by_name(self, name: str) -> Optional[SysTenant]:
        return self.db.query(SysTenant).filter(
            and_(SysTenant.name == name, SysTenant.del_flag == '0')
        ).first()


class SysUserDAL(BaseDAL):
    model = SysUser

    def get_by_username(self, username: str, tenant_id: Optional[str] = None) -> Optional[SysUser]:
        query = self.db.query(SysUser).filter(SysUser.username == username)
        query = self._apply_tenant_filter(query, tenant_id)
        query = self._apply_soft_delete_filter(query)
        return query.first()

    def get_with_roles(self, id: str, tenant_id: Optional[str] = None) -> Optional[SysUser]:
        from sqlalchemy.orm import selectinload
        query = self.db.query(SysUser).options(selectinload(SysUser.roles)).filter(SysUser.id == id)
        query = self._apply_tenant_filter(query, tenant_id)
        query = self._apply_soft_delete_filter(query)
        return query.first()


class SysRoleDAL(BaseDAL):
    model = SysRole

    def get_with_permissions(self, id: str, tenant_id: Optional[str] = None) -> Optional[SysRole]:
        from sqlalchemy.orm import selectinload
        query = self.db.query(SysRole).options(selectinload(SysRole.permissions)).filter(SysRole.id == id)
        query = self._apply_tenant_filter(query, tenant_id)
        query = self._apply_soft_delete_filter(query)
        return query.first()


class SysPermissionDAL(BaseDAL):
    model = SysPermission

    def get_by_code(self, permission_code: str) -> Optional[SysPermission]:
        return self.db.query(SysPermission).filter(SysPermission.permission_code == permission_code).first()


class ChatProviderDAL(BaseDAL):
    model = ChatProvider

    def get_by_code(self, provider_code: str, tenant_id: Optional[str] = None) -> Optional[ChatProvider]:
        query = self.db.query(ChatProvider).filter(ChatProvider.provider_code == provider_code)
        query = self._apply_tenant_filter(query, tenant_id)
        query = self._apply_soft_delete_filter(query)
        return query.first()


class ChatModelDAL(BaseDAL):
    model = ChatModel

    def get_by_code(self, model_code: str, tenant_id: Optional[str] = None) -> Optional[ChatModel]:
        query = self.db.query(ChatModel).filter(ChatModel.model_code == model_code)
        query = self._apply_tenant_filter(query, tenant_id)
        query = self._apply_soft_delete_filter(query)
        return query.first()

    def get_by_provider(self, provider_id: str, tenant_id: Optional[str] = None) -> List[ChatModel]:
        query = self.db.query(ChatModel).filter(ChatModel.provider_id == provider_id)
        query = self._apply_tenant_filter(query, tenant_id)
        query = self._apply_soft_delete_filter(query)
        return query.all()


class ChatSessionDAL(BaseDAL):
    model = ChatSession

    def get_by_user(self, user_id: str, tenant_id: Optional[str] = None) -> List[ChatSession]:
        query = self.db.query(ChatSession).filter(ChatSession.user_id == user_id)
        query = self._apply_tenant_filter(query, tenant_id)
        query = self._apply_soft_delete_filter(query)
        return query.order_by(desc(ChatSession.created_at)).all()


class ChatMessageDAL(BaseDAL):
    model = ChatMessage

    def get_by_session(self, session_id: str, tenant_id: Optional[str] = None, limit: int = 100) -> List[ChatMessage]:
        query = self.db.query(ChatMessage).filter(ChatMessage.session_id == session_id)
        query = self._apply_tenant_filter(query, tenant_id)
        query = self._apply_soft_delete_filter(query)
        return query.order_by(asc(ChatMessage.created_at)).limit(limit).all()


class AgentDefinitionDAL(BaseDAL):
    model = AgentDefinition


class ToolGroupDefinitionDAL(BaseDAL):
    model = ToolGroupDefinition

    def get_by_code(self, group_code: str, tenant_id: Optional[str] = None) -> Optional[ToolGroupDefinition]:
        query = self.db.query(ToolGroupDefinition).filter(ToolGroupDefinition.group_code == group_code)
        query = self._apply_tenant_filter(query, tenant_id)
        query = self._apply_soft_delete_filter(query)
        return query.first()


class ToolDefinitionDAL(BaseDAL):
    model = ToolDefinition

    def get_by_group(self, group_id: str, tenant_id: Optional[str] = None) -> List[ToolDefinition]:
        query = self.db.query(ToolDefinition).filter(ToolDefinition.group_id == group_id)
        query = self._apply_tenant_filter(query, tenant_id)
        query = self._apply_soft_delete_filter(query)
        return query.all()

    def get_by_code(self, tool_code: str, tenant_id: Optional[str] = None) -> Optional[ToolDefinition]:
        query = self.db.query(ToolDefinition).filter(ToolDefinition.tool_code == tool_code)
        query = self._apply_tenant_filter(query, tenant_id)
        query = self._apply_soft_delete_filter(query)
        return query.first()


class KnowledgeBaseDAL(BaseDAL):
    model = KnowledgeBase


class KnowledgeDocumentDAL(BaseDAL):
    model = KnowledgeDocument

    def get_by_kb(self, kb_id: str, tenant_id: Optional[str] = None) -> List[KnowledgeDocument]:
        query = self.db.query(KnowledgeDocument).filter(KnowledgeDocument.kb_id == kb_id)
        query = self._apply_tenant_filter(query, tenant_id)
        return query.all()


class KnowledgeChunkDAL(BaseDAL):
    model = KnowledgeChunk

    def get_by_document(self, document_id: str, tenant_id: Optional[str] = None) -> List[KnowledgeChunk]:
        query = self.db.query(KnowledgeChunk).filter(KnowledgeChunk.document_id == document_id)
        query = self._apply_tenant_filter(query, tenant_id)
        return query.order_by(KnowledgeChunk.chunk_index).all()

    def get_by_kb(self, kb_id: str, tenant_id: Optional[str] = None) -> List[KnowledgeChunk]:
        query = self.db.query(KnowledgeChunk).filter(KnowledgeChunk.kb_id == kb_id)
        query = self._apply_tenant_filter(query, tenant_id)
        return query.all()


class ExecutionTraceDAL(BaseDAL):
    model = ExecutionTrace

    def get_by_session(self, session_id: str, tenant_id: Optional[str] = None) -> List[ExecutionTrace]:
        query = self.db.query(ExecutionTrace).filter(ExecutionTrace.session_id == session_id)
        query = self._apply_tenant_filter(query, tenant_id)
        return query.order_by(ExecutionTrace.created_at).all()

    def get_by_agent(self, agent_id: str, tenant_id: Optional[str] = None) -> List[ExecutionTrace]:
        query = self.db.query(ExecutionTrace).filter(ExecutionTrace.agent_id == agent_id)
        query = self._apply_tenant_filter(query, tenant_id)
        return query.order_by(desc(ExecutionTrace.created_at)).all()

    def get_paginated_by_filters(
        self,
        tenant_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        session_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        stage: Optional[str] = None,
        status: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> Tuple[List[ExecutionTrace], int, int]:
        query = self.db.query(ExecutionTrace)
        query = self._apply_tenant_filter(query, tenant_id)
        
        if session_id:
            query = query.filter(ExecutionTrace.session_id == session_id)
        if agent_id:
            query = query.filter(ExecutionTrace.agent_id == agent_id)
        if stage:
            query = query.filter(ExecutionTrace.stage == stage)
        if status:
            query = query.filter(ExecutionTrace.status == status)
        if start_time:
            query = query.filter(ExecutionTrace.created_at >= start_time)
        if end_time:
            query = query.filter(ExecutionTrace.created_at <= end_time)
        
        query = query.order_by(desc(ExecutionTrace.created_at))
        
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        
        return items, total, total_pages
