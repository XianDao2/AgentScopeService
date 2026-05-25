# 实施任务清单

Feature Name: 2026-05-25-agentscope-replatform
Updated: 2026-05-25

---

## Phase 1: 核心执行链路迁移

目标：部署 AgentScope Agent Service 基础服务，实现核心对话与工具调用链路，替换认证为 JWT + RBAC。

---

### 1.1 项目脚手架与基础设施

| # | 任务 | 优先级 | 依赖 | 产出 | 验收标准 |
|---|------|--------|------|------|---------|
| 1.1.1 | 创建新项目目录结构 `src/ms3/`，包含 `api/`、`runtime/`、`knowledge/`、`middleware/`、`auth/`、`models/`、`database/`、`common/` 子包 | P0 | 无 | 目录结构 + `__init__.py` | 目录存在且 Python 可导入 |
| 1.1.2 | 编写 `pyproject.toml`，声明 Python 3.11+ 依赖：agentscope>=2.0、fastapi、uvicorn、sqlalchemy、aioredis、pymongo、qdrant-client、minio、python-jose、passlib | P0 | 1.1.1 | pyproject.toml | `pip install -e .` 成功 |
| 1.1.3 | 编写 Dockerfile（基于 python:3.11-slim），复制项目、安装依赖、暴露 8080 端口、CMD 启动 uvicorn | P0 | 1.1.2 | Dockerfile | `docker build -t ms3:1.0 .` 成功 |
| 1.1.4 | 编写 `.env` 模板，包含 MySQL/Redis/Qdrant/MongoDB/MinIO/JWT 全部环境变量（参考 design.md 10.2） | P0 | 无 | .env.example | 所有必要变量均已声明 |
| 1.1.5 | 编写 `docker-compose.yaml`，编排 ms3-api + mysql + redis + qdrant + mongodb + minio 六个服务，资源限额参考 design.md 7.2 | P0 | 1.1.3, 1.1.4 | docker-compose.yaml | `docker compose up -d` 全部服务健康 |
| 1.1.6 | 编写 MySQL DDL 迁移脚本：保留现有 8 张表 + 升级 chat_model/chat_provider 2 张表 + 新增 agent_definition/tool_group_definition/tool_definition/knowledge_base/knowledge_document/knowledge_chunk/execution_trace 7 张表（参考 design.md 4.1） | P0 | 无 | `src/ms3/database/migrations/V1__initial_schema.sql` | 在空库执行无报错，表结构符合设计文档 |

### 1.2 数据库访问层

| # | 任务 | 优先级 | 依赖 | 产出 | 验收标准 |
|---|------|--------|------|------|---------|
| 1.2.1 | 实现 SQLAlchemy ORM 模型：SysTenant、SysUser、SysRole、SysPermission、SysUserRole、SysRolePermission（保留现有模型，字段对齐 init.sql） | P0 | 1.1.6 | `models/sys.py` | 模型可创建表且字段与现有 init.sql 一致 |
| 1.2.2 | 实现 SQLAlchemy ORM 模型：ChatSession、ChatMessage（保留现有模型） | P0 | 1.1.6 | `models/chat.py` | 模型可创建表且字段与现有表一致 |
| 1.2.3 | 实现 SQLAlchemy ORM 模型：ChatModel（增加 credential_type/context_size/output_size/input_types/output_types）、ChatProvider（增加 credential_schema） | P0 | 1.1.6 | `models/chat_model.py` | 升级字段存在且默认值正确 |
| 1.2.4 | 实现 SQLAlchemy ORM 模型：AgentDefinition、ToolGroupDefinition、ToolDefinition、KnowledgeBase、KnowledgeDocument、KnowledgeChunk、ExecutionTrace（7 张新表） | P0 | 1.1.6 | `models/platform.py` | 模型可创建表且字段/索引符合 design.md 4.1.3 |
| 1.2.5 | 实现数据库连接管理：MySQL 连接池（pool_size=50, max_overflow=30）、会话工厂、健康检查 | P0 | 1.2.1 | `database/connection.py` | 连接池可获取会话、健康检查端点正常 |
| 1.2.6 | 实现 Redis 连接管理：aioredis 连接池（max_connections=100）、健康检查 | P0 | 1.2.5 | `database/redis_connection.py` | Redis 连接正常、健康检查端点正常 |
| 1.2.7 | 实现 MongoDB 连接管理：Motor 异步客户端、集合初始化（session_execution_logs / llm_call_logs） | P1 | 1.2.5 | `database/mongo_connection.py` | 可写入/读取日志集合 |
| 1.2.8 | 实现 DAL 层：各模型的 CRUD 基础操作（租户隔离查询、分页、软删除） | P0 | 1.2.4 | `database/dal.py` | 单元测试通过 |

### 1.3 认证与权限

| # | 任务 | 优先级 | 依赖 | 产出 | 验收标准 |
|---|------|--------|------|------|---------|
| 1.3.1 | 实现 JWT 认证模块：签发 Token（access_token + refresh_token）、解码验证、Token 刷新、黑名单 | P0 | 1.2.1 | `auth/jwt_auth.py` | 签发/验证/刷新/黑名单单元测试通过 |
| 1.3.2 | 实现 FastAPI 依赖项 `get_current_user_id`：从 Authorization Header 提取 JWT、返回 user_id | P0 | 1.3.1 | `auth/dependencies.py` | 合法 Token 返回 user_id，非法 Token 返回 401 |
| 1.3.3 | 实现租户上下文注入中间件：从 JWT 提取 tenant_id，注入到请求上下文（contextvars） | P0 | 1.3.2 | `middleware/tenant_context.py` | 后续代码可通过 `get_current_tenant_id()` 获取 |
| 1.3.4 | 实现 RBAC 权限校验依赖项：基于 sys_user_role + sys_role_permission 查询用户权限列表，校验接口权限 | P0 | 1.3.2 | `auth/rbac.py` | 有权限返回通过，无权限返回 403 |
| 1.3.5 | 替换 AgentScope Agent Service 默认 X-User-ID 认证：`app.dependency_overrides[default_dep] = JWTAuthDependency()` | P0 | 1.3.2 | `api/app.py` | 调用 Agent Service 内置路由需携带 JWT |

### 1.4 Agent Service 启动与扩展路由

| # | 任务 | 优先级 | 依赖 | 产出 | 验收标准 |
|---|------|--------|------|------|---------|
| 1.4.1 | 实现 `create_app` 启动逻辑：初始化 RedisStorage、LocalWorkspaceManager、注册扩展路由、替换认证依赖、挂载静态资源 | P0 | 1.2.5, 1.3.5 | `api/app.py` | 服务启动后内置路由和扩展路由均可用 |
| 1.4.2 | 实现租户管理路由：CRUD + 用户管理（`/api/v2/tenants`） | P0 | 1.4.1, 1.2.8 | `api/routers/tenant.py` | 租户 CRUD + 用户分配接口可用 |
| 1.4.3 | 实现用户管理路由：登录/登出/用户 CRUD/角色分配（`/api/v2/users`） | P0 | 1.4.1, 1.3.1, 1.2.8 | `api/routers/user.py` | 登录返回 JWT，CRUD 正常 |
| 1.4.4 | 实现角色权限路由：角色 CRUD + 权限分配（`/api/v2/roles`） | P0 | 1.4.1, 1.2.8 | `api/routers/role.py` | 角色 CRUD + 权限绑定接口可用 |
| 1.4.5 | 实现模型管理路由：Provider CRUD + Model CRUD + Credential 同步（`/api/v2/models`） | P0 | 1.4.1, 1.2.8 | `api/routers/model.py` | 模型配置 CRUD 且同步到 AgentScope Credential |
| 1.4.6 | 实现工具组管理路由：ToolGroup CRUD + Tool 注册/注销（`/api/v2/tool-groups`） | P0 | 1.4.1, 1.2.8 | `api/routers/tool_group.py` | 工具组和工具的 CRUD 接口可用 |
| 1.4.7 | 实现智能体管理路由：AgentDefinition CRUD + 工具组绑定 + 模型绑定（`/api/v2/agents`） | P0 | 1.4.1, 1.2.8 | `api/routers/agent.py` | 智能体定义 CRUD 且可绑定工具组/模型 |
| 1.4.8 | 实现执行日志路由：按会话/租户/智能体/时间查询（`/api/v2/execution-logs`） | P1 | 1.4.1 | `api/routers/execution_log.py` | 日志查询分页接口可用 |

### 1.5 Agent 运行时核心

| # | 任务 | 优先级 | 依赖 | 产出 | 验收标准 |
|---|------|--------|------|------|---------|
| 1.5.1 | 实现 PlatformAgentBuilder：根据 AgentDefinition 构建 AgentScope Agent 实例（name/sys_prompt/model/toolkit/state/context_config/react_config/middlewares） | P0 | 1.4.7 | `runtime/agent_builder.py` | 给定 AgentDefinition 可构建出可运行的 Agent |
| 1.5.2 | 实现 PlatformToolkitAssembler：根据 ToolGroupDefinition 列表组装 AgentScope Toolkit（FunctionTool/ToolGroup/MCPClient/Skill） | P0 | 1.4.6 | `runtime/toolkit_assembler.py` | 给定工具组定义可构建出 Toolkit |
| 1.5.3 | 实现 AgentScope Credential 适配器：将 chat_provider + chat_model 配置转换为 AgentScope Credential + ModelCard | P0 | 1.4.5 | `runtime/credential_adapter.py` | 模型配置可被 Agent 实例使用 |
| 1.5.4 | 实现 TenantAwareWorkspaceManager：继承 LocalWorkspaceManager，按 tenant_id + agent_id 隔离工作目录 | P1 | 1.4.1 | `runtime/workspace_manager.py` | 不同租户的工作目录物理隔离 |
| 1.5.5 | 实现 AgentState 持久化协调器：reply 完成后持久化 AgentState 到 RedisStorage + 同步写 chat_message 到 MySQL | P0 | 1.5.1 | `runtime/state_coordinator.py` | 会话结束后 Redis 和 MySQL 均有数据 |
| 1.5.6 | 实现对话核心流程：接收 POST /chat → 认证 → SessionManager.get_or_create → PlatformAgentBuilder.build → agent.reply_stream → AgentEvent 转 SSE → 持久化 | P0 | 1.5.1, 1.5.2, 1.5.5 | `runtime/chat_handler.py` | 前端可发送消息并收到流式回复 |

### 1.6 Middleware 实现

| # | 任务 | 优先级 | 依赖 | 产出 | 验收标准 |
|---|------|--------|------|------|---------|
| 1.6.1 | 实现 TenantIsolationMiddleware：on_reply 注入 tenant_id trace context，on_acting 校验工具调用资源归属 | P0 | 1.3.3 | `middleware/tenant_isolation.py` | 跨租户工具调用被拒绝 |
| 1.6.2 | 实现 AuditLoggingMiddleware：on_model_call 记录 LLM 调用信息到 MongoDB（token/耗时/模型名） | P0 | 1.2.7 | `middleware/audit_logging.py` | LLM 调用记录写入 MongoDB |
| 1.6.3 | 实现 ExecutionTraceMiddleware：从 AgentEvent 流提取 ToolCallStartEvent/ToolResultEndEvent/ModelCallStartEvent/ModelCallEndEvent，记录到 execution_trace 表 | P0 | 1.2.8 | `middleware/execution_trace.py` | 工具调用和 LLM 调用均有执行追踪记录 |

### 1.7 技能迁移 - 第一批（同步工具）

| # | 任务 | 优先级 | 依赖 | 产出 | 验收标准 |
|---|------|--------|------|------|---------|
| 1.7.1 | 迁移 official-doc-writer 为 ToolGroup(doc-tools)：generate_document + preview_document + download_document 三个 FunctionTool | P0 | 1.5.2 | `runtime/tools/doc_tools.py` | 调用 generate_official_document 返回预览，download_official_document 返回下载链接 |
| 1.7.2 | 迁移 document-summary 为 FunctionTool | P0 | 1.5.2 | `runtime/tools/summary_tool.py` | 调用 document_summary 返回摘要结果 |
| 1.7.3 | 迁移 email-helper 为 FunctionTool | P1 | 1.5.2 | `runtime/tools/email_tool.py` | 调用 email_helper 返回发送结果 |
| 1.7.4 | 实现工具注册引导脚本：将上述 FunctionTool 对应的 tool_definition 记录写入数据库 | P0 | 1.7.1, 1.7.2, 1.7.3 | `scripts/seed_tools.py` | 执行后数据库有工具定义记录 |

### 1.8 前端适配 - Phase 1

| # | 任务 | 优先级 | 依赖 | 产出 | 验收标准 |
|---|------|--------|------|------|---------|
| 1.8.1 | 适配前端 API 层：更新 axios 基础路径指向新 API（`/api/v2/`），调整请求头携带 JWT | P0 | 1.4.1 | `web/src/api/` | 前端请求可到达新后端 |
| 1.8.2 | 适配 AgentChat SSE 事件处理：映射 AgentEvent 流到前端事件（ReplyStart→reply_start, TextBlockDelta→text_delta, ToolCallStart→tool_call_start, ReplyEnd→reply_end 等） | P0 | 1.5.6 | `web/src/views/AgentChat.vue` | 聊天页面可正常流式接收文本和工具调用事件 |
| 1.8.3 | 新增 ThinkingBlock 展示区域：当收到 ThinkingBlockDeltaEvent 时在消息中显示思考过程（可折叠） | P1 | 1.8.2 | `web/src/components/ThinkingBlock.vue` | 思考过程可展示和折叠 |
| 1.8.4 | 新增 ToolCall 展示区域：当收到 ToolCallStartEvent/ToolResultEndEvent 时显示工具调用状态（调用中/完成/失败） | P1 | 1.8.2 | `web/src/components/ToolCallBlock.vue` | 工具调用状态正确展示 |
| 1.8.5 | 适配 Login 页面：调用新登录接口获取 JWT，存储到 localStorage | P0 | 1.4.3 | `web/src/views/Login.vue` | 登录成功获取 JWT 并跳转 |
| 1.8.6 | 新增智能体管理页面：AgentDefinition 列表 + 新增/编辑/删除表单 + 工具组绑定 + 模型绑定 | P0 | 1.4.7 | `web/src/views/AgentManagement.vue` | 智能体 CRUD + 绑定操作可用 |
| 1.8.7 | 新增工具组管理页面：ToolGroup 列表 + 工具注册/注销 + 工具组启用/停用 | P0 | 1.4.6 | `web/src/views/ToolGroupManagement.vue` | 工具组管理操作可用 |
| 1.8.8 | 升级 ModelManagement 页面：增加 Credential 管理和 ModelCard 展示 | P1 | 1.4.5 | `web/src/views/ModelManagement.vue` | 可管理模型凭证 |

### 1.9 Phase 1 集成验证

| # | 任务 | 优先级 | 依赖 | 产出 | 验收标准 |
|---|------|--------|------|------|---------|
| 1.9.1 | 端到端冒烟测试：登录 → 创建智能体 → 绑定 doc-tools 工具组 → 发起对话 → 验证流式回复和工具调用 | P0 | 1.5~1.8 | 测试报告 | 核心对话+工具调用链路通畅 |
| 1.9.2 | AgentState 持久化验证：对话中断 → 重启服务 → 恢复会话 → 验证上下文完整 | P0 | 1.5.5 | 测试报告 | 崩溃恢复后会话可继续 |
| 1.9.3 | 多租户隔离验证：两个租户各自创建智能体 → 验证数据隔离和工具调用隔离 | P0 | 1.6.1 | 测试报告 | 跨租户数据不可见 |
| 1.9.4 | 构建 ms3:1.0 Docker 镜像并使用 `docker run -d -p 8080:8080 --name ms3 --env-file .env ms3:1.0` 启动验证 | P0 | 1.1.3 | 镜像 | 容器启动健康，API 可访问 |

---

## Phase 2: 知识库与异步能力

目标：部署 Qdrant，实现知识库全链路，迁移异步技能，接入 MCP 和 Skill。

---

### 2.1 知识库核心

| # | 任务 | 优先级 | 依赖 | 产出 | 验收标准 |
|---|------|--------|------|------|---------|
| 2.1.1 | 实现 PlatformKnowledgeService：create_knowledge（SimpleKnowledge + QdrantStore + DashScopeTextEmbedding）、_get_or_create（实例缓存 TTL 10min） | P0 | 1.2.8 | `knowledge/service.py` | 可创建 SimpleKnowledge 实例并缓存 |
| 2.1.2 | 实现文档入库流程：上传文件到 MinIO → TextReader/ImageReader 解析 → 切片 → DashScopeTextEmbedding 向量化 → QdrantStore upsert → 更新 knowledge_document/knowledge_chunk 状态 | P0 | 2.1.1 | `knowledge/ingest.py` | 上传 PDF/TXT/DOCX/MD/图片后文档状态变为 completed |
| 2.1.3 | 实现知识检索流程：SimpleKnowledge.retrieve → 返回 Document 列表 + 置信分数 + 来源元数据 | P0 | 2.1.1 | `knowledge/retrieve.py` | 给定 query 返回相关切片和来源 |
| 2.1.4 | 实现文档版本管理：增量重建切片/向量索引、删除文档时清理 Qdrant 向量、版本号自增 | P1 | 2.1.2 | `knowledge/version.py` | 更新文档后版本号+1，旧版本切片可回溯 |
| 2.1.5 | 实现入库失败处理：parse_status 标记 failed、保留 error_message 和 storage_path、支持重试 | P0 | 2.1.2 | `knowledge/ingest.py` | 失败文档可重试入库 |
| 2.1.6 | 实现知识库统计信息：文档数量、切片数量、索引状态、最近更新时间 | P1 | 2.1.2 | `knowledge/service.py` | 知识库详情页可展示统计 |

### 2.2 RAG 集成

| # | 任务 | 优先级 | 依赖 | 产出 | 验收标准 |
|---|------|--------|------|------|---------|
| 2.2.1 | 实现通用模式 RAG：Agent 构建时传入 knowledge 对象，AgentScope 自动在回复前注入检索上下文 | P0 | 2.1.3, 1.5.1 | `runtime/agent_builder.py` 修改 | 智能体回复包含知识库引用 |
| 2.2.2 | 实现智能体自主模式 RAG：将 retrieve_knowledge 注册为 FunctionTool，由 Agent 自主决定何时调用 | P0 | 2.1.3, 1.5.2 | `runtime/tools/knowledge_tool.py` | Agent 在需要时主动调用检索工具 |
| 2.2.3 | 实现 KnowledgeInjectionMiddleware：on_system_prompt 钩子注入检索结果 + 引用回传 | P0 | 2.1.3 | `middleware/knowledge_injection.py` | system_prompt 中包含检索上下文和引用信息 |
| 2.2.4 | 实现知识库降级策略：Qdrant 不可用时切换为无知识增强模式并记录告警 | P1 | 2.2.1 | `middleware/knowledge_injection.py` | Qdrant 异常时 Agent 仍可正常对话 |

### 2.3 知识库前端

| # | 任务 | 优先级 | 依赖 | 产出 | 验收标准 |
|---|------|--------|------|------|---------|
| 2.3.1 | 新增知识库管理页面：列表 + 创建/编辑/删除表单（名称/描述/Embedding 模型/检索策略/权限） | P0 | 2.1.1 | `web/src/views/KnowledgeBase.vue` | 知识库 CRUD 可用 |
| 2.3.2 | 新增文档管理子页面：上传文件（拖拽+批量）/ 删除文档 / 重建索引 / 查看解析状态 | P0 | 2.1.2 | `web/src/views/KnowledgeDocument.vue` | 文档上传和管理操作可用 |
| 2.3.3 | 新增切片查看子页面：按文档查看切片列表 + 切片内容 + 向量状态 + 来源元数据 | P1 | 2.1.3 | `web/src/views/KnowledgeChunk.vue` | 可查看切片详情 |
| 2.3.4 | 新增知识库统计组件：文档数/切片数/索引状态/最近更新（嵌入知识库详情页） | P1 | 2.1.6 | `web/src/components/KnowledgeStats.vue` | 统计数据正确展示 |

### 2.4 知识库路由

| # | 任务 | 优先级 | 依赖 | 产出 | 验收标准 |
|---|------|--------|------|------|---------|
| 2.4.1 | 实现知识库管理路由：CRUD + 统计信息（`/api/v2/kb`） | P0 | 2.1.1, 1.4.1 | `api/routers/knowledge.py` | 知识库 CRUD 接口可用 |
| 2.4.2 | 实现文档管理路由：上传/删除/重建索引/状态查询（`/api/v2/kb/{id}/documents`） | P0 | 2.1.2, 2.4.1 | `api/routers/knowledge.py` 扩展 | 文档管理接口可用 |
| 2.4.3 | 实现切片查询路由：按文档/知识库查询切片（`/api/v2/kb/{id}/chunks`） | P1 | 2.1.3, 2.4.1 | `api/routers/knowledge.py` 扩展 | 切片查询接口可用 |

### 2.5 异步技能迁移

| # | 任务 | 优先级 | 依赖 | 产出 | 验收标准 |
|---|------|--------|------|------|---------|
| 2.5.1 | 迁移 image-generator 为 ExternalExecutionTool：封装为异步工具函数，通过 BackgroundTaskManager 提交任务，完成后注入 ExternalExecutionResultEvent | P0 | 1.5.2 | `runtime/tools/image_gen_tool.py` | 图片生成任务异步执行，完成后结果回传 Agent |
| 2.5.2 | 迁移 audio-transcription 为 ExternalExecutionTool | P0 | 1.5.2 | `runtime/tools/audio_tool.py` | 音频转写任务异步执行 |
| 2.5.3 | 适配 ImageGeneration 前端页面：对接 ExternalExecutionTool 模式，显示任务进度 | P1 | 2.5.1, 1.8.2 | `web/src/views/ImageGeneration.vue` | 图片生成页面可用 |
| 2.5.4 | 适配 AudioTranscribe 前端页面：对接 ExternalExecutionTool 模式 | P1 | 2.5.2, 1.8.2 | `web/src/views/AudioTranscribe.vue` | 音频转写页面可用 |

### 2.6 MCP 和 Skill 接入

| # | 任务 | 优先级 | 依赖 | 产出 | 验收标准 |
|---|------|--------|------|------|---------|
| 2.6.1 | 实现 MCP 工具接入：MCPClient 注册到 Toolkit，支持 Stateful(STDIO/HTTP) 和 Stateless(HTTP) 两种模式 | P0 | 1.5.2 | `runtime/mcp_manager.py` | 可连接外部 MCP Server 并调用工具 |
| 2.6.2 | 实现 MCP 管理路由：MCP Server 配置 CRUD + 连接状态（`/api/v2/mcp`） | P0 | 2.6.1 | `api/routers/mcp.py` | MCP 配置管理接口可用 |
| 2.6.3 | 实现 Skill 指令集接入：LocalSkillLoader 扫描技能目录 + 注册到 Toolkit | P1 | 1.5.2 | `runtime/skill_loader.py` | SKILL.md 格式技能可被 Agent 使用 |
| 2.6.4 | 实现 Skill 管理路由：Skill 目录扫描 + CRUD（`/api/v2/skills`） | P1 | 2.6.3 | `api/routers/skill.py` | Skill 管理接口可用 |

### 2.7 长期记忆

| # | 任务 | 优先级 | 依赖 | 产出 | 验收标准 |
|---|------|--------|------|------|---------|
| 2.7.1 | 实现跨会话 AgentState 恢复：用户重新打开会话时从 RedisStorage 加载历史 AgentState 重建 Agent 实例 | P0 | 1.5.5 | `runtime/state_coordinator.py` 修改 | 历史会话可恢复并继续对话 |
| 2.7.2 | 实现内存策略支持：session 模式（会话结束释放）和 persistent 模式（长期保留） | P1 | 2.7.1 | `runtime/state_coordinator.py` 修改 | persistent 策略下 AgentState 持久化保留 |

### 2.8 Phase 2 集成验证

| # | 任务 | 优先级 | 依赖 | 产出 | 验收标准 |
|---|------|--------|------|------|---------|
| 2.8.1 | 知识库端到端验证：创建知识库 → 上传文档 → 等待入库完成 → 绑定到智能体 → 对话验证知识增强回复 | P0 | 2.1~2.4 | 测试报告 | 知识增强回复包含引用来源 |
| 2.8.2 | RAG 两种模式验证：通用模式自动注入 + 智能体自主模式工具调用 | P0 | 2.2.1, 2.2.2 | 测试报告 | 两种模式均可正常工作 |
| 2.8.3 | 异步技能验证：图片生成 + 音频转写异步执行 → 结果回传 | P0 | 2.5 | 测试报告 | 异步任务完成并结果正确 |
| 2.8.4 | MCP 接入验证：配置外部 MCP Server → Agent 调用 MCP 工具 → 返回结果 | P0 | 2.6.1 | 测试报告 | MCP 工具调用成功 |
| 2.8.5 | 全部 Phase 1 回归验证：确保 Phase 2 改动未破坏 Phase 1 功能 | P0 | 1.9, 2.8.1~2.8.4 | 测试报告 | Phase 1 功能全部正常 |

---

## Phase 3: 容量与可观测性

目标：8C16G 容量压测通过 200+ 并发，实施限流/监控/告警，完善执行日志，旧链路下线。

---

### 3.1 限流与降级

| # | 任务 | 优先级 | 依赖 | 产出 | 验收标准 |
|---|------|--------|------|------|---------|
| 3.1.1 | 实现租户级限流：基于 Redis ZSET 分布式信号量，单租户并发 > max_concurrent_executions 时排队等待，超时返回 429 | P0 | 1.2.6 | `middleware/rate_limiter.py` | 超限请求返回 429 + Retry-After |
| 3.1.2 | 实现全局级限流：总并发 > 300 时新请求排队，优先保障已执行请求 | P0 | 3.1.1 | `middleware/rate_limiter.py` 修改 | 全局超限触发排队 |
| 3.1.3 | 实现 LLM 级限流：信号量控制 LLM 调用并发 > 200 时等待，超时降级为缓存回复 | P0 | 3.1.1 | `middleware/llm_limiter.py` | LLM 并发超限触发降级 |
| 3.1.4 | 实现降级策略：大文件异步入库、降低异步技能并发、限制知识检索 top_k 和上下文拼接长度、低优先级租户排队 | P1 | 3.1.1 | `middleware/degradation.py` | 压力场景下降级策略生效 |

### 3.2 可观测性

| # | 任务 | 优先级 | 依赖 | 产出 | 验收标准 |
|---|------|--------|------|------|---------|
| 3.2.1 | 实现 Prometheus 指标输出：请求总数/活跃会话/工具调用延迟/LLM 调用延迟/错误率/队列深度（`/api/v2/observability/metrics`） | P0 | 1.4.1 | `api/routers/observability.py` | Prometheus 可抓取指标 |
| 3.2.2 | 完善 MongoDB 执行日志：session_execution_logs 层级结构 + llm_call_logs token 消耗和响应时间 | P0 | 1.6.2 | `middleware/audit_logging.py` 修改 | 执行日志结构化存储可查询 |
| 3.2.3 | 实现结构化告警事件：执行超时/失败/降级时生成告警并写入 MongoDB | P1 | 3.2.2 | `common/alerting.py` | 异常事件触发告警记录 |

### 3.3 SSE 断线重连

| # | 任务 | 优先级 | 依赖 | 产出 | 验收标准 |
|---|------|--------|------|------|---------|
| 3.3.1 | 实现前端 SSE 断线重连：利用 AgentScope SessionManager 的 buffered replay 能力，断线后从 last_event_id 恢复 | P0 | 1.5.6 | `web/src/composables/useSSE.ts` | 网络断开后重连不丢消息 |
| 3.3.2 | 前端消息重建：使用 @agentscope-ai/agentscope TypeScript SDK 的 AssistantMsg.appendEvent 重建完整消息 | P0 | 3.3.1 | `web/src/composables/useChat.ts` | 事件流正确重建为结构化消息 |

### 3.4 性能优化

| # | 任务 | 优先级 | 依赖 | 产出 | 验收标准 |
|---|------|--------|------|------|---------|
| 3.4.1 | 消息批量写库：chat_message 从逐条 INSERT 改为批量 INSERT（缓冲 500ms 或 50 条） | P0 | 1.5.5 | `runtime/state_coordinator.py` 修改 | 写库 QPS 提升 5x+ |
| 3.4.2 | 知识库入库并行化：文件解析 + 切片 + 向量化采用流水线并行（而非顺序执行） | P1 | 2.1.2 | `knowledge/ingest.py` 修改 | 入库耗时降低 50%+ |
| 3.4.3 | AgentState 序列化优化：压缩大状态、懒加载历史消息 | P1 | 1.5.5 | `runtime/state_coordinator.py` 修改 | 单次序列化 < 50ms |

### 3.5 压力测试

| # | 任务 | 优先级 | 依赖 | 产出 | 验收标准 |
|---|------|--------|------|------|---------|
| 3.5.1 | 编写 200 并发用户技能执行压测脚本（Locust/k6）：模拟混合负载（轻量问答 60% + 工具调用 30% + 知识检索 10%） | P0 | 3.1, 3.4 | `tests/perf/load_test.py` | 压测脚本可运行 |
| 3.5.2 | 执行压测并验证：200+ 并发下核心接口可访问、P95 延迟达标、无单租户突发导致全局不可用 | P0 | 3.5.1 | 压测报告 | 200 并发 P95 延迟达标 |
| 3.5.3 | SSE 长连接压测：2000+ 连接稳定性验证 | P1 | 3.5.1 | 压测报告 | 2000 SSE 连接稳定 |
| 3.5.4 | 知识库检索 P95 压测：验证 < 500ms | P1 | 3.5.1 | 压测报告 | 知识检索 P95 < 500ms |
| 3.5.5 | AgentState 序列化/反序列化性能测试 | P2 | 3.4.3 | 性能报告 | 单次操作 < 50ms |

### 3.6 可靠性测试

| # | 任务 | 优先级 | 依赖 | 产出 | 验收标准 |
|---|------|--------|------|------|---------|
| 3.6.1 | Redis 故障演练：AgentState 丢失后恢复验证 | P1 | 1.5.5 | 测试报告 | Redis 恢复后会话可继续 |
| 3.6.2 | LLM 超时演练：降级路径验证 | P1 | 3.1.3 | 测试报告 | LLM 超时后降级策略生效 |
| 3.6.3 | Worker 重启恢复演练 | P1 | 1.5.5 | 测试报告 | Worker 重启后会话可恢复 |
| 3.6.4 | Qdrant 不可用演练：无知识增强降级验证 | P1 | 2.2.4 | 测试报告 | Qdrant 异常时仍可无知识增强对话 |

### 3.7 旧链路下线

| # | 任务 | 优先级 | 依赖 | 产出 | 验收标准 |
|---|------|--------|------|------|---------|
| 3.7.1 | 数据迁移脚本：将现有 chat_session/chat_message 数据迁移到新表结构 | P0 | 1.2 | `scripts/migrate_data.py` | 历史数据完整迁移 |
| 3.7.2 | 标记旧代码目录 `src/co_assitant_skills_isolated/` 为废弃（添加 DEPRECATED.md），移除旧路由注册 | P1 | 3.7.1 | DEPRECATED.md | 旧代码不再被新服务引用 |
| 3.7.3 | 清理旧 Dockerfile 和启动脚本（保留 ms2 兼容入口直到完全下线） | P2 | 3.7.2 | 清理完成 | 旧容器入口标记为 deprecated |

---

## 任务统计

| Phase | 任务数 | P0 | P1 | P2 |
|-------|--------|----|----|-----|
| Phase 1 | 34 | 24 | 8 | 2 |
| Phase 2 | 24 | 13 | 9 | 2 |
| Phase 3 | 19 | 9 | 9 | 1 |
| **合计** | **77** | **46** | **26** | **5** |

## 关键路径

```
1.1.1→1.1.2→1.1.3→1.1.5 (基础设施)
1.1.6→1.2.1~1.2.4→1.2.5→1.2.8 (数据库层)
1.2.1→1.3.1→1.3.2→1.3.5 (认证)
1.2.5+1.3.5→1.4.1→1.4.2~1.4.7 (路由)
1.4.6+1.4.7→1.5.1+1.5.2→1.5.6 (运行时核心) ← 最长路径
1.5.6→1.8.2 (前端 SSE 适配)
1.5.6→1.9.1 (集成验证)
```

Phase 1 最长路径约 15 步，建议按关键路径优先推进。
