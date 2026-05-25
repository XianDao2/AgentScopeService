import os
import shutil
from datetime import datetime, timezone

from ms3.common.config import settings
from ms3.middleware.tenant_context import get_current_tenant_id


class LocalWorkspace:

    def __init__(self, workdir: str):
        self.workdir = workdir

    async def initialize(self) -> None:
        os.makedirs(self.workdir, exist_ok=True)

    async def write_file(self, relative_path: str, content: str | bytes) -> str:
        full_path = os.path.join(self.workdir, relative_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        mode = "w" if isinstance(content, str) else "wb"
        with open(full_path, mode) as f:
            f.write(content)
        return full_path

    async def read_file(self, relative_path: str) -> str:
        full_path = os.path.join(self.workdir, relative_path)
        with open(full_path) as f:
            return f.read()

    async def list_files(self, prefix: str = "") -> list[str]:
        target_dir = os.path.join(self.workdir, prefix) if prefix else self.workdir
        if not os.path.isdir(target_dir):
            return []
        result = []
        for root, _, files in os.walk(target_dir):
            for fname in files:
                abs_path = os.path.join(root, fname)
                rel_path = os.path.relpath(abs_path, self.workdir)
                result.append(rel_path)
        return result

    async def delete_file(self, relative_path: str) -> None:
        full_path = os.path.join(self.workdir, relative_path)
        if os.path.exists(full_path):
            os.remove(full_path)

    async def cleanup(self) -> None:
        if os.path.isdir(self.workdir):
            shutil.rmtree(self.workdir, ignore_errors=True)


class TenantAwareWorkspaceManager:

    def __init__(self, basedir: str | None = None):
        self._basedir = basedir or settings.workspace_basedir
        self._ttl = settings.workspace_ttl
        self._workspaces: dict[str, tuple[LocalWorkspace, float]] = {}

    def _make_key(self, tenant_id: str, agent_id: str) -> str:
        return f"{tenant_id}:{agent_id}"

    def _make_workdir(self, tenant_id: str, agent_id: str) -> str:
        return os.path.join(self._basedir, tenant_id, agent_id)

    async def create_workspace(
        self,
        user_id: str,
        agent_id: str,
        session_id: str,
    ) -> LocalWorkspace:
        tenant_id = get_current_tenant_id() or "default"
        workdir = self._make_workdir(tenant_id, agent_id)
        workspace = LocalWorkspace(workdir=workdir)
        await workspace.initialize()
        key = self._make_key(tenant_id, agent_id)
        self._workspaces[key] = (workspace, datetime.now(timezone.utc).timestamp())
        return workspace

    async def get_workspace(
        self,
        user_id: str,
        agent_id: str,
        session_id: str,
        workspace_id: str | None = None,
    ) -> LocalWorkspace:
        tenant_id = get_current_tenant_id() or "default"
        key = self._make_key(tenant_id, agent_id)
        cached = self._workspaces.get(key)
        if cached:
            workspace, _ = cached
            return workspace

        workdir = self._make_workdir(tenant_id, agent_id)
        workspace = LocalWorkspace(workdir=workdir)
        await workspace.initialize()
        self._workspaces[key] = (workspace, datetime.now(timezone.utc).timestamp())
        return workspace

    async def evict_expired(self) -> int:
        now = datetime.now(timezone.utc).timestamp()
        evicted = 0
        expired_keys = [
            k for k, (_, ts) in self._workspaces.items()
            if now - ts > self._ttl
        ]
        for key in expired_keys:
            workspace, _ = self._workspaces.pop(key)
            await workspace.cleanup()
            evicted += 1
        return evicted
