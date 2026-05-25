# Tasks

## Phase 1: 核心执行链路迁移

目标：部署 AgentScope Agent Service 基础服务，实现核心对话与工具调用链路，替换认证为 JWT + RBAC。

---

### 1.1 项目脚手架与基础设施

- [x] Task 1.1.1: 创建新项目目录结构 `src/ms3/`，包含 `api/`、`runtime/`、`knowledge/`、`middleware/`、`auth/`、`models/`、`database/`、`common/` 子包
  - [x] 创建 `src/ms3/` 及所有子包目录
  - [x] 每个子包添加 `__init__.py`
  - [x] 验证 Python 可导入

- [x] Task 1.1.2: 编写 `pyproject.toml`，声明 Python 3.11+ 依赖：agentscope>=2.0、fastapi、uvicorn、sqlalchemy、aioredis、pymongo、qdrant-client、minio、python-jose、passlib
  - [x] 声明项目元数据（name、version、requires-python）
  - [x] 声明所有核心依赖
  - [x] 验证 `pip install -e .` 成功

- [x] Task 1.1.3: 编写 Dockerfile（基于 python:3.11-slim），复制项目、安装依赖、暴露 8080 端口、CMD 启动 uvicorn
  - [x] 选择 python:3.11-slim 基础镜像
  - [x] 复制项目文件并安装依赖
  - [x] 暴露 8080 端口
  - [x] CMD 启动 uvicorn

- [x] Task 1.1.4: 编写 `.env.example` 模板，包含 MySQL/Redis/Qdrant/MongoDB/MinIO/JWT 全部环境变量
  - [x] 声明 MySQL 相关变量（MYSQL_HOST/PORT/USER/PASSWORD/DATABASE/POOL_SIZE/MAX_OVERFLOW）
  - [x] 声明 Redis 相关变量（REDIS_HOST/PORT）
  - [x] 声明 Qdrant/MinIO/MongoDB/JWT 变量
  - [x] 声明 DASHSCOPE_API_KEY/LLM_GLOBAL_MAX_CONCURRENCY/UVICORN_WORKERS

- [x] Task 1.1.5: 编写 `docker-compose.yaml`，编排 ms3-api + mysql + redis + qdrant + mongodb + minio 六个服务
  - [x] 定义 ms3-api 服务（依赖其余服务，资源限额 4C9G）
  - [x] 定义 mysql 服务（8.0，端口 23306，资源限额 1C1.5G）
  - [x] 定义 redis 服务（6.2，端口 6379，资源限额 1C1.5G）
  - [x] 定义 qdrant 服务（latest，端口 6333，资源限额 1C2G）
  - [x] 定义 mongodb 服务（7.0，端口 8010，资源限额 0.5C0.5G）
  - [x] 定义 minio 服务（latest，端口 9000/9001，资源限额 0.5C0.5G）

- [x] Task 1.1.6: 编写 MySQL DDL 迁移脚本
  - [x] 保留现有 8 张表 DDL（sys_tenant/sys_user/sys_role/sys_permission/sys_user_role/sys_role_permission/chat_session/chat_message）
  - [x] 升级 chat_model 表（增加 credential_type/context_size/output_size/input_types/output_types）
  - [x] 升级 chat_provider 表（增加 credential_schema）
  - [x] 新增 agent_definition 表
  - [x] 新增 tool_group_definition 表
  - [x] 新增 tool_definition 表
  - [x] 新增 knowledge_base 表
  - [x] 新增 knowledge_document 表
  - [x] 新增 knowledge_chunk 表
  - [x] 新增 execution_trace 表

### 1.2 数据库访问层

- [x] Task 1.2.1: 实现 SQLAlchemy ORM 模型：SysTenant、SysUser、SysRole、SysPermission、SysUserRole、SysRolePermission
  - [x] 定义 SysTenant 模型（字段对齐 init.sql）
  - [x] 定义 SysUser 模型
  - [x] 定义 SysRole 模型
  - [x] 定义 SysPermission 模型
  - [x] 定义 SysUserRole 关联模型
  - [x] 定义 SysRolePermission 关联模型

- [x] Task 1.2.2: 实现 SQLAlchemy ORM 模型：ChatSession、ChatMessage
  - [x] 定义 ChatSession 模型
  - [x] 定义 ChatMessage 模型

- [x] Task 1.2.3: 实现 SQLAlchemy ORM 模型：ChatModel（升级字段）、ChatProvider（升级字段）
  - [x] ChatModel 增加 credential_type/context_size/output_size/input_types/output_types
  - [x] ChatProvider 增加 credential_schema

- [x] Task 1.2.4: 实现 SQLAlchemy ORM 模型：7 张新表
  - [x] AgentDefinition 模型
  - [x] ToolGroupDefinition 模型
  - [x] ToolDefinition 模型
  - [x] KnowledgeBase 模型
  - [x] KnowledgeDocument 模型
  - [x] KnowledgeChunk 模型
  - [x] ExecutionTrace 模型

- [x] Task 1.2.5: 实现数据库连接管理：MySQL 连接池、会话工厂、健康检查
  - [x] 创建 AsyncSession 工厂（pool_size=50, max_overflow=30）
  - [x] 实现 get_db 依赖项
  - [x] 实现健康检查端点

- [x] Task 1.2.6: 实现 Redis 连接管理：aioredis 连接池、健康检查
  - [x] 创建 aioredis 连接池（max_connections=100）
  - [x] 实现健康检查

- [x] Task 1.2.7: 实现 MongoDB 连接管理：Motor 异步客户端、集合初始化
  - [x] 创建 Motor 异步客户端
  - [x] 初始化 session_execution_logs 和 llm_call_logs 集合

- [x] Task 1.2.8: 实现 DAL 层：各模型的 CRUD 基础操作
  - [x] 实现租户隔离查询基类
  - [x] 实现分页查询
  - [x] 实现软删除
  - [x] 实现各模型 CRUD 方法

### 1.3 认证与权限

- [x] Task 1.3.1: 实现 JWT 认证模块
  - [x] 签发 Token（access_token + refresh_token）
  - [x] 解码验证
  - [x] Token 刷新
  - [x] 黑名单机制

- [x] Task 1.3.2: 实现 FastAPI 依赖项 `get_current_user_id`
  - [x] 从 Authorization Header 提取 JWT
  - [x] 返回 user_id
  - [x] 非法 Token 返回 401

- [x] Task 1.3.3: 实现租户上下文注入中间件
  - [x] 从 JWT 提取 tenant_id
  - [x] 注入到 contextvars
  - [x] 提供 get_current_tenant_id() 函数

- [x] Task 1.3.4: 实现 RBAC 权限校验依赖项
  - [x] 基于 sys_user_role + sys_role_permission 查询用户权限列表
  - [x] 校验接口权限
  - [x] 无权限返回 403

- [x] Task 1.3.5: 替换 AgentScope Agent Service 默认认证
  - [x] 获取 Agent Service 默认 get_current_user_id 依赖
  - [x] 通过 dependency_overrides 替换为 JWTAuthDependency

### 1.4 Agent Service 启动与扩展路由

- [x] Task 1.4.1: 实现 `create_app` 启动逻辑
  - [x] 初始化 RedisStorage
  - [x] 初始化 LocalWorkspaceManager
  - [x] 注册扩展路由
  - [x] 替换认证依赖
  - [x] 挂载静态资源

- [x] Task 1.4.2: 实现租户管理路由（`/api/v2/tenants`）
  - [x] 租户 CRUD 接口
  - [x] 用户管理接口

- [x] Task 1.4.3: 实现用户管理路由（`/api/v2/users`）
  - [x] 登录/登出接口
  - [x] 用户 CRUD 接口
  - [x] 角色分配接口

- [x] Task 1.4.4: 实现角色权限路由（`/api/v2/roles`）
  - [x] 角色 CRUD 接口
  - [x] 权限分配接口

- [x] Task 1.4.5: 实现模型管理路由（`/api/v2/models`）
  - [x] Provider CRUD 接口
  - [x] Model CRUD 接口
  - [x] Credential 同步逻辑

- [x] Task 1.4.6: 实现工具组管理路由（`/api/v2/tool-groups`）
  - [x] ToolGroup CRUD 接口
  - [x] Tool 注册/注销接口

- [x] Task 1.4.7: 实现智能体管理路由（`/api/v2/agents`）
  - [x] AgentDefinition CRUD 接口
  - [x] 工具组绑定接口
  - [x] 模型绑定接口

- [x] Task 1.4.8: 实现执行日志路由（`/api/v2/execution-logs`）
  - [x] 按会话查询
  - [x] 按租户查询
  - [x] 按智能体查询
  - [x] 按时间范围查询

### 1.5 Agent 运行时核心

- [x] Task 1.5.1: 实现 PlatformAgentBuilder
  - [x] 根据 AgentDefinition 构建 AgentScope Agent 实例
  - [x] 配置 name/system_prompt/model/toolkit/state/context_config/react_config/middlewares
  - [x] 支持从 AgentState 恢复

- [x] Task 1.5.2: 实现 PlatformToolkitAssembler
  - [x] 根据 ToolGroupDefinition 列表组装 AgentScope Toolkit
  - [x] 支持 FunctionTool 注册
  - [x] 支持 ToolGroup 定义
  - [x] 支持 MCPClient 注册
  - [x] 支持 Skill 注册

- [x] Task 1.5.3: 实现 AgentScope Credential 适配器
  - [x] 将 chat_provider + chat_model 配置转换为 AgentScope Credential
  - [x] 支持 DashScope/OpenAI/DeepSeek/智谱/Ollama 等供应商

- [x] Task 1.5.4: 实现 TenantAwareWorkspaceManager
  - [x] 继承 LocalWorkspaceManager
  - [x] 按 tenant_id + agent_id 隔离工作目录
  - [x] 实现 create_workspace 和 get_workspace

- [x] Task 1.5.5: 实现 AgentState 持久化协调器
  - [x] reply 完成后持久化 AgentState 到 RedisStorage
  - [x] 同步写 chat_message 到 MySQL
  - [x] 支持从 RedisStorage 加载 AgentState

- [x] Task 1.5.6: 实现对话核心流程
  - [x] 接收 POST /chat 请求
  - [x] JWT 认证 + 租户上下文注入
  - [x] SessionManager.get_or_create_session
  - [x] PlatformAgentBuilder.build
  - [x] agent.reply_stream
  - [x] AgentEvent 转 SSE
  - [x] 持久化 AgentState 和 chat_message

### 1.6 Middleware 实现

- [x] Task 1.6.1: 实现 TenantIsolationMiddleware
  - [x] on_reply 注入 tenant_id trace context
  - [x] on_acting 校验工具调用资源归属

- [x] Task 1.6.2: 实现 AuditLoggingMiddleware
  - [x] on_model_call 记录 LLM 调用信息到 MongoDB
  - [x] 记录 token 消耗、耗时、模型名

- [x] Task 1.6.3: 实现 ExecutionTraceMiddleware
  - [x] 从 AgentEvent 流提取 ToolCallStartEvent/ToolResultEndEvent
  - [x] 提取 ModelCallStartEvent/ModelCallEndEvent
  - [x] 记录到 execution_trace 表

### 1.7 技能迁移 - 第一批（同步工具）

- [x] Task 1.7.1: 迁移 official-doc-writer 为 ToolGroup(doc-tools)
  - [x] 实现 generate_official_document FunctionTool
  - [x] 实现 preview_official_document FunctionTool
  - [x] 实现 download_official_document FunctionTool
  - [x] 组装为 doc-tools ToolGroup

- [x] Task 1.7.2: 迁移 document-summary 为 FunctionTool
  - [x] 实现 document_summary FunctionTool

- [x] Task 1.7.3: 迁移 email-helper 为 FunctionTool
  - [x] 实现 email_helper FunctionTool

- [x] Task 1.7.4: 实现工具注册引导脚本
  - [x] 将 FunctionTool 对应的 tool_definition 记录写入数据库
  - [x] 将 ToolGroup 对应的 tool_group_definition 记录写入数据库

### 1.8 前端适配 - Phase 1

- [x] Task 1.8.1: 适配前端 API 层
  - [x] 更新 axios 基础路径指向新 API（`/api/v2/`）
  - [x] 调整请求头携带 JWT

- [x] Task 1.8.2: 适配 AgentChat SSE 事件处理
  - [x] 映射 AgentEvent 流到前端事件
  - [x] 使用 @agentscope-ai/agentscope TypeScript SDK 重建消息

- [x] Task 1.8.3: 新增 ThinkingBlock 展示区域
  - [x] 当收到 ThinkingBlockDeltaEvent 时显示思考过程
  - [x] 支持折叠/展开

- [x] Task 1.8.4: 新增 ToolCall 展示区域
  - [x] 当收到 ToolCallStartEvent/ToolResultEndEvent 时显示工具调用状态
  - [x] 显示调用中/完成/失败状态

- [x] Task 1.8.5: 适配 Login 页面
  - [x] 调用新登录接口获取 JWT
  - [x] 存储到 localStorage

- [x] Task 1.8.6: 新增智能体管理页面
  - [x] AgentDefinition 列表
  - [x] 新增/编辑/删除表单
  - [x] 工具组绑定
  - [x] 模型绑定

- [x] Task 1.8.7: 新增工具组管理页面
  - [x] ToolGroup 列表
  - [x] 工具注册/注销
  - [x] 工具组启用/停用

- [x] Task 1.8.8: 升级 ModelManagement 页面
  - [x] 增加 Credential 管理
  - [x] 增加 ModelCard 展示

### 1.9 Phase 1 集成验证

- [x] Task 1.9.1: 端到端冒烟测试
  - [x] 登录 → 创建智能体 → 绑定 doc-tools 工具组 → 发起对话 → 验证流式回复和工具调用

- [x] Task 1.9.2: AgentState 持久化验证
  - [x] 对话中断 → 重启服务 → 恢复会话 → 验证上下文完整

- [x] Task 1.9.3: 多租户隔离验证
  - [x] 两个租户各自创建智能体 → 验证数据隔离和工具调用隔离

- [x] Task 1.9.4: Docker 镜像构建验证
  - [x] 构建 ms3:1.0 Docker 镜像
  - [x] 使用 docker run 启动验证

---

## Phase 2: 知识库与异步能力

目标：部署 Qdrant，实现知识库全链路，迁移异步技能，接入 MCP 和 Skill。

---

### 2.1 知识库核心

- [x] Task 2.1.1: 实现 PlatformKnowledgeService
  - [x] create_knowledge（SimpleKnowledge + QdrantStore + DashScopeTextEmbedding）
  - [x] _get_or_create（实例缓存 TTL 10min）

- [x] Task 2.1.2: 实现文档入库流程
  - [x] 上传文件到 MinIO
  - [x] TextReader/ImageReader 解析
  - [x] 切片
  - [x] DashScopeTextEmbedding 向量化
  - [x] QdrantStore upsert
  - [x] 更新 knowledge_document/knowledge_chunk 状态

- [x] Task 2.1.3: 实现知识检索流程
  - [x] SimpleKnowledge.retrieve
  - [x] 返回 Document 列表 + 置信分数 + 来源元数据

- [x] Task 2.1.4: 实现文档版本管理
  - [x] 增量重建切片/向量索引
  - [x] 删除文档时清理 Qdrant 向量
  - [x] 版本号自增

- [x] Task 2.1.5: 实现入库失败处理
  - [x] parse_status 标记 failed
  - [x] 保留 error_message 和 storage_path
  - [x] 支持重试

- [x] Task 2.1.6: 实现知识库统计信息
  - [x] 文档数量、切片数量、索引状态、最近更新时间

### 2.2 RAG 集成

- [x] Task 2.2.1: 实现通用模式 RAG
  - [x] Agent 构建时传入 knowledge 对象
  - [x] AgentScope 自动在回复前注入检索上下文

- [x] Task 2.2.2: 实现智能体自主模式 RAG
  - [x] 将 retrieve_knowledge 注册为 FunctionTool
  - [x] 由 Agent 自主决定何时调用

- [x] Task 2.2.3: 实现 KnowledgeInjectionMiddleware
  - [x] on_system_prompt 钩子注入检索结果
  - [x] 引用回传

- [x] Task 2.2.4: 实现知识库降级策略
  - [x] Qdrant 不可用时切换为无知识增强模式
  - [x] 记录告警

### 2.3 知识库前端

- [x] Task 2.3.1: 新增知识库管理页面
  - [x] 列表 + 创建/编辑/删除表单
  - [x] 名称/描述/Embedding 模型/检索策略/权限配置

- [x] Task 2.3.2: 新增文档管理子页面
  - [x] 上传文件（拖拽+批量）
  - [x] 删除文档
  - [x] 重建索引
  - [x] 查看解析状态

- [x] Task 2.3.3: 新增切片查看子页面
  - [x] 按文档查看切片列表
  - [x] 切片内容 + 向量状态 + 来源元数据

- [x] Task 2.3.4: 新增知识库统计组件
  - [x] 文档数/切片数/索引状态/最近更新

### 2.4 知识库路由

- [x] Task 2.4.1: 实现知识库管理路由（`/api/v2/kb`）
  - [x] 知识库 CRUD 接口
  - [x] 统计信息接口

- [x] Task 2.4.2: 实现文档管理路由（`/api/v2/kb/{id}/documents`）
  - [x] 上传/删除/重建索引/状态查询

- [x] Task 2.4.3: 实现切片查询路由（`/api/v2/kb/{id}/chunks`）
  - [x] 按文档/知识库查询切片

### 2.5 异步技能迁移

- [x] Task 2.5.1: 迁移 image-generator 为 ExternalExecutionTool
  - [x] 封装为异步工具函数
  - [x] 通过 BackgroundTaskManager 提交任务
  - [x] 完成后注入 ExternalExecutionResultEvent

- [x] Task 2.5.2: 迁移 audio-transcription 为 ExternalExecutionTool
  - [x] 封装为异步工具函数

- [x] Task 2.5.3: 适配 ImageGeneration 前端页面
  - [x] 对接 ExternalExecutionTool 模式
  - [x] 显示任务进度

- [x] Task 2.5.4: 适配 AudioTranscribe 前端页面
  - [x] 对接 ExternalExecutionTool 模式

### 2.6 MCP 和 Skill 接入

- [x] Task 2.6.1: 实现 MCP 工具接入
  - [x] MCPClient 注册到 Toolkit
  - [x] 支持 Stateful(STDIO/HTTP) 和 Stateless(HTTP) 模式

- [x] Task 2.6.2: 实现 MCP 管理路由（`/api/v2/mcp`）
  - [x] MCP Server 配置 CRUD
  - [x] 连接状态查询

- [x] Task 2.6.3: 实现 Skill 指令集接入
  - [x] LocalSkillLoader 扫描技能目录
  - [x] 注册到 Toolkit

- [x] Task 2.6.4: 实现 Skill 管理路由（`/api/v2/skills`）
  - [x] Skill 目录扫描
  - [x] Skill CRUD

### 2.7 长期记忆

- [x] Task 2.7.1: 实现跨会话 AgentState 恢复
  - [x] 用户重新打开会话时从 RedisStorage 加载历史 AgentState
  - [x] 重建 Agent 实例

- [x] Task 2.7.2: 实现内存策略支持
  - [x] session 模式（会话结束释放）
  - [x] persistent 模式（长期保留）

### 2.8 Phase 2 集成验证

- [x] Task 2.8.1: 知识库端到端验证
  - [x] 创建知识库 → 上传文档 → 等待入库完成 → 绑定到智能体 → 对话验证知识增强回复

- [x] Task 2.8.2: RAG 两种模式验证
  - [x] 通用模式自动注入
  - [x] 智能体自主模式工具调用

- [x] Task 2.8.3: 异步技能验证
  - [x] 图片生成 + 音频转写异步执行 → 结果回传

- [x] Task 2.8.4: MCP 接入验证
  - [x] 配置外部 MCP Server → Agent 调用 MCP 工具 → 返回结果

- [x] Task 2.8.5: 全部 Phase 1 回归验证
  - [x] 确保 Phase 2 改动未破坏 Phase 1 功能

---

## Phase 3: 容量与可观测性

目标：8C16G 容量压测通过 200+ 并发，实施限流/监控/告警，完善执行日志，旧链路下线。

---

### 3.1 限流与降级

- [x] Task 3.1.1: 实现租户级限流
  - [x] 基于 Redis ZSET 分布式信号量
  - [x] 单租户并发 > max_concurrent_executions 时排队等待
  - [x] 超时返回 429 + Retry-After

- [x] Task 3.1.2: 实现全局级限流
  - [x] 总并发 > 300 时新请求排队
  - [x] 优先保障已执行请求

- [x] Task 3.1.3: 实现 LLM 级限流
  - [x] 信号量控制 LLM 调用并发 > 200 时等待
  - [x] 超时降级为缓存回复

- [x] Task 3.1.4: 实现降级策略
  - [x] 大文件异步入库
  - [x] 降低异步技能并发
  - [x] 限制知识检索 top_k 和上下文拼接长度
  - [x] 低优先级租户排队

### 3.2 可观测性

- [x] Task 3.2.1: 实现 Prometheus 指标输出
  - [x] 请求总数/活跃会话/工具调用延迟/LLM 调用延迟/错误率/队列深度
  - [x] `/api/v2/observability/metrics` 端点

- [x] Task 3.2.2: 完善 MongoDB 执行日志
  - [x] session_execution_logs 层级结构
  - [x] llm_call_logs token 消耗和响应时间

- [x] Task 3.2.3: 实现结构化告警事件
  - [x] 执行超时/失败/降级时生成告警
  - [x] 写入 MongoDB

### 3.3 SSE 断线重连

- [ ] Task 3.3.1: 实现前端 SSE 断线重连
  - [ ] 利用 SessionManager 的 buffered replay 能力
  - [ ] 断线后从 last_event_id 恢复

- [ ] Task 3.3.2: 前端消息重建
  - [ ] 使用 @agentscope-ai/agentscope TypeScript SDK 的 AssistantMsg.appendEvent
  - [ ] 重建完整消息

### 3.4 性能优化

- [ ] Task 3.4.1: 消息批量写库
  - [ ] chat_message 从逐条 INSERT 改为批量 INSERT
  - [ ] 缓冲 500ms 或 50 条

- [ ] Task 3.4.2: 知识库入库并行化
  - [ ] 文件解析 + 切片 + 向量化采用流水线并行

- [ ] Task 3.4.3: AgentState 序列化优化
  - [ ] 压缩大状态
  - [ ] 懒加载历史消息

### 3.5 压力测试

- [ ] Task 3.5.1: 编写 200 并发用户技能执行压测脚本
  - [ ] 模拟混合负载（轻量问答 60% + 工具调用 30% + 知识检索 10%）

- [ ] Task 3.5.2: 执行压测并验证
  - [ ] 200+ 并发下核心接口可访问
  - [ ] P95 延迟达标
  - [ ] 无单租户突发导致全局不可用

- [ ] Task 3.5.3: SSE 长连接压测
  - [ ] 2000+ 连接稳定性验证

- [ ] Task 3.5.4: 知识库检索 P95 压测
  - [ ] 验证 < 500ms

- [ ] Task 3.5.5: AgentState 序列化/反序列化性能测试
  - [ ] 单次操作 < 50ms

### 3.6 可靠性测试

- [ ] Task 3.6.1: Redis 故障演练
  - [ ] AgentState 丢失后恢复验证

- [ ] Task 3.6.2: LLM 超时演练
  - [ ] 降级路径验证

- [ ] Task 3.6.3: Worker 重启恢复演练

- [ ] Task 3.6.4: Qdrant 不可用演练
  - [ ] 无知识增强降级验证

### 3.7 旧链路下线

- [ ] Task 3.7.1: 数据迁移脚本
  - [ ] 将现有 chat_session/chat_message 数据迁移到新表结构

- [ ] Task 3.7.2: 标记旧代码目录为废弃
  - [ ] 添加 DEPRECATED.md
  - [ ] 移除旧路由注册

- [ ] Task 3.7.3: 清理旧 Dockerfile 和启动脚本
  - [ ] 保留 ms2 兼容入口直到完全下线

---

# Task Dependencies

- Task 1.1.1 → Task 1.1.2 → Task 1.1.3 → Task 1.1.5（基础设施链路）
- Task 1.1.6 → Task 1.2.1~1.2.4 → Task 1.2.5 → Task 1.2.8（数据库层）
- Task 1.2.1 → Task 1.3.1 → Task 1.3.2 → Task 1.3.5（认证链路）
- Task 1.2.5 + Task 1.3.5 → Task 1.4.1 → Task 1.4.2~1.4.7（路由层）
- Task 1.4.6 + Task 1.4.7 → Task 1.5.1 + Task 1.5.2 → Task 1.5.6（运行时核心 ← 最长路径）
- Task 1.5.6 → Task 1.8.2（前端 SSE 适配）
- Task 1.5.6 → Task 1.9.1（集成验证）
- Task 2.1.1 → Task 2.1.2 → Task 2.1.3（知识库核心）
- Task 2.1.3 + Task 1.5.1 → Task 2.2.1（RAG 通用模式）
- Task 2.1.3 + Task 1.5.2 → Task 2.2.2（RAG 自主模式）
- Task 1.5.2 → Task 2.5.1 + Task 2.5.2（异步技能迁移）
- Task 1.5.2 → Task 2.6.1（MCP 接入）
- Phase 1 完成 → Phase 2 开始
- Phase 2 完成 → Phase 3 开始
