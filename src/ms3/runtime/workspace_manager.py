import logging
import os
import shutil
from typing import Optional
from pathlib import Path

from src.ms3.common.config import get_settings
from src.ms3.middleware.tenant_context import get_current_tenant_id

logger = logging.getLogger(__name__)
settings = get_settings()


class TenantAwareWorkspaceManager:
    """
    按 tenant_id + agent_id 隔离本地工作目录的 Workspace 管理器
    """

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir or settings.workspace_base_dir or "/data/workspaces")
        self._ensure_base_dir()

    def _ensure_base_dir(self) -> None:
        """
        确保基础目录存在
        """
        try:
            self.base_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Workspace base directory: {self.base_dir}")
        except Exception as e:
            logger.error(f"Failed to create workspace base directory: {str(e)}")
            raise

    def _get_workspace_path(self, tenant_id: str, agent_id: str) -> Path:
        """
        获取工作空间路径

        Args:
            tenant_id: 租户 ID
            agent_id: Agent ID

        Returns:
            工作空间路径
        """
        return self.base_dir / tenant_id / agent_id

    async def create_workspace(
        self,
        tenant_id: str,
        agent_id: str,
        session_id: Optional[str] = None,
    ) -> "TenantWorkspace":
        """
        创建工作空间

        Args:
            tenant_id: 租户 ID
            agent_id: Agent ID
            session_id: 可选的会话 ID

        Returns:
            工作空间实例
        """
        try:
            workspace_path = self._get_workspace_path(tenant_id, agent_id)
            workspace_path.mkdir(parents=True, exist_ok=True)

            logger.info(f"Created workspace: {workspace_path}")

            return TenantWorkspace(
                path=workspace_path,
                tenant_id=tenant_id,
                agent_id=agent_id,
                session_id=session_id,
            )

        except Exception as e:
            logger.error(f"Failed to create workspace: {str(e)}")
            raise

    async def get_workspace(
        self,
        tenant_id: str,
        agent_id: str,
        session_id: Optional[str] = None,
    ) -> Optional["TenantWorkspace"]:
        """
        获取工作空间

        Args:
            tenant_id: 租户 ID
            agent_id: Agent ID
            session_id: 可选的会话 ID

        Returns:
            工作空间实例或 None
        """
        workspace_path = self._get_workspace_path(tenant_id, agent_id)

        if not workspace_path.exists():
            return None

        return TenantWorkspace(
            path=workspace_path,
            tenant_id=tenant_id,
            agent_id=agent_id,
            session_id=session_id,
        )

    async def delete_workspace(self, tenant_id: str, agent_id: str) -> None:
        """
        删除工作空间

        Args:
            tenant_id: 租户 ID
            agent_id: Agent ID
        """
        workspace_path = self._get_workspace_path(tenant_id, agent_id)

        if workspace_path.exists():
            try:
                shutil.rmtree(workspace_path)
                logger.info(f"Deleted workspace: {workspace_path}")
            except Exception as e:
                logger.error(f"Failed to delete workspace: {str(e)}")
                raise

    async def cleanup_old_workspaces(self, days: int = 30) -> None:
        """
        清理旧的工作空间

        Args:
            days: 天数阈值
        """
        # TODO: 实现清理逻辑
        logger.warning(f"Cleanup old workspaces not implemented (threshold: {days} days)")


class TenantWorkspace:
    """
    租户感知的工作空间
    """

    def __init__(
        self,
        path: Path,
        tenant_id: str,
        agent_id: str,
        session_id: Optional[str] = None,
    ):
        self.path = path
        self.tenant_id = tenant_id
        self.agent_id = agent_id
        self.session_id = session_id
        self._agent_scope_workspace: Optional[Any] = None

    def get_path(self) -> Path:
        """
        获取工作空间路径

        Returns:
            路径
        """
        return self.path

    def get_subdir(self, name: str) -> Path:
        """
        获取子目录

        Args:
            name: 子目录名称

        Returns:
            子目录路径
        """
        subdir = self.path / name
        subdir.mkdir(parents=True, exist_ok=True)
        return subdir

    def write_file(self, filename: str, content: str) -> Path:
        """
        写入文件

        Args:
            filename: 文件名
            content: 文件内容

        Returns:
            文件路径
        """
        file_path = self.path / filename
        file_path.write_text(content, encoding="utf-8")
        return file_path

    def read_file(self, filename: str) -> Optional[str]:
        """
        读取文件

        Args:
            filename: 文件名

        Returns:
            文件内容或 None
        """
        file_path = self.path / filename
        if not file_path.exists():
            return None
        return file_path.read_text(encoding="utf-8")

    def delete_file(self, filename: str) -> bool:
        """
        删除文件

        Args:
            filename: 文件名

        Returns:
            是否成功
        """
        file_path = self.path / filename
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    def list_files(self) -> list[Path]:
        """
        列出文件

        Returns:
            文件列表
        """
        return [f for f in self.path.iterdir() if f.is_file()]

    def to_agent_scope_workspace(self) -> Any:
        """
        转换为 AgentScope Workspace

        Returns:
            AgentScope Workspace 实例
        """
        if self._agent_scope_workspace:
            return self._agent_scope_workspace

        try:
            from agentscope.workspace import LocalWorkspace

            self._agent_scope_workspace = LocalWorkspace(
                workdir=str(self.path),
            )
            return self._agent_scope_workspace

        except ImportError:
            logger.warning("AgentScope not available, returning mock workspace")
            return self
