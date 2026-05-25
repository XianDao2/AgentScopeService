# Checklist

## Phase 1: 核心执行链路迁移

### 1.1 项目脚手架与基础设施
- [ ] `src/ms3/` 目录结构存在且包含 api/runtime/knowledge/middleware/auth/models/database/common 子包
- [ ] `pyproject.toml` 存在且声明了 Python 3.11+ 和所有核心依赖
- [ ] Dockerfile 存在且基于 python:3.11-slim，暴露 8080 端口
- [ ] `.env.example` 包含 MySQL/Redis/Qdrant/MongoDB/MinIO/JWT 全部环境变量
- [ ] `docker-compose.yaml` 编排了 6 个服务且资源限额符合设计文档
- [ ] MySQL DDL 迁移脚本包含 8 张保留表 + 2 张升级表 + 7 张新增表

### 1.2 数据库访问层
- [ ] SysTenant/SysUser/SysRole/SysPermission/SysUserRole/SysRolePermission ORM 模型存在且字段对齐
- [ ] ChatSession/ChatMessage ORM 模型存在且字段对齐
- [ ] ChatModel 包含 credential_type/context_size/output_size/input_types/output_types 升级字段
- [ ] ChatProvider 包含 credential_schema 升级字段
- [ ] AgentDefinition/ToolGroupDefinition/ToolDefinition/KnowledgeBase/KnowledgeDocument/KnowledgeChunk/ExecutionTrace ORM 模型存在
- [ ] MySQL 连接池配置为 pool_size=50, max_overflow=30
- [ ] Redis 连接池配置为 max_connections=100
- [ ] MongoDB 集合 session_execution_logs 和 llm_call_logs 可写入/读取
- [ ] DAL 层支持租户隔离查询、分页和软删除

### 1.3 认证与权限
- [ ] JWT 模块支持签发/验证/刷新/黑名单
- [ ] get_current_user_id 依赖项从 JWT 提取 user_id
- [ ] 租户上下文注入中间件将 tenant_id 注入 contextvars
- [ ] RBAC 权限校验依赖项基于 sys_user_role + sys_role_permission 查询权限
- [ ] Agent Service 默认认证已替换为 JWTAuthDependency

### 1.4 Agent Service 启动与扩展路由
- [ ] create_app 启动逻辑初始化 RedisStorage、LocalWorkspaceManager、注册扩展路由
- [ ] `/api/v2/tenants` 租户管理路由可用
- [ ] `/api/v2/users` 用户管理路由可用（登录返回 JWT）
- [ ] `/api/v2/roles` 角色权限路由可用
- [ ] `/api/v2/models` 模型管理路由可用且同步到 AgentScope Credential
- [ ] `/api/v2/tool-groups` 工具组管理路由可用
- [ ] `/api/v2/agents` 智能体管理路由可用且可绑定工具组/模型
- [ ] `/api/v2/execution-logs` 执行日志路由可用

### 1.5 Agent 运行时核心
- [ ] PlatformAgentBuilder 可根据 AgentDefinition 构建可运行的 Agent
- [ ] PlatformToolkitAssembler 可根据 ToolGroupDefinition 列表组装 Toolkit
- [ ] Credential 适配器可将 chat_provider + chat_model 配置转换为 AgentScope Credential
- [ ] TenantAwareWorkspaceManager 按 tenant_id + agent_id 隔离工作目录
- [ ] AgentState 持久化协调器在 reply 完成后同时写 Redis 和 MySQL
- [ ] 对话核心流程：POST /chat → 认证 → SessionManager → Agent.reply_stream → SSE → 持久化

### 1.6 Middleware 实现
- [ ] TenantIsolationMiddleware 在 on_reply 注入 tenant_id trace context
- [ ] TenantIsolationMiddleware 在 on_acting 校验工具调用资源归属
- [ ] AuditLoggingMiddleware 在 on_model_call 记录 LLM 调用信息到 MongoDB
- [ ] ExecutionTraceMiddleware 从 AgentEvent 流提取事件并记录到 execution_trace 表

### 1.7 技能迁移
- [ ] doc-tools ToolGroup 包含 generate/preview/download 三个 FunctionTool
- [ ] document-summary FunctionTool 可返回摘要结果
- [ ] email-helper FunctionTool 可返回发送结果
- [ ] 工具注册引导脚本执行后数据库有工具定义记录

### 1.8 前端适配
- [ ] 前端 API 层基础路径指向 /api/v2/ 且携带 JWT
- [ ] AgentChat 页面可正常流式接收文本和工具调用事件
- [ ] ThinkingBlock 展示区域可展示和折叠
- [ ] ToolCall 展示区域显示调用中/完成/失败状态
- [ ] Login 页面调用新登录接口获取 JWT 并跳转
- [ ] 智能体管理页面支持 CRUD + 工具组绑定 + 模型绑定
- [ ] 工具组管理页面支持 CRUD + 工具注册/注销
- [ ] ModelManagement 页面支持 Credential 管理和 ModelCard 展示

### 1.9 Phase 1 集成验证
- [ ] 端到端冒烟测试：登录 → 创建智能体 → 绑定工具组 → 对话 → 流式回复和工具调用
- [ ] AgentState 持久化验证：对话中断 → 重启服务 → 恢复会话 → 上下文完整
- [ ] 多租户隔离验证：两个租户数据隔离和工具调用隔离
- [ ] Docker 镜像构建并启动验证

---

## Phase 2: 知识库与异步能力

### 2.1 知识库核心
- [ ] PlatformKnowledgeService 可创建 SimpleKnowledge 实例并缓存
- [ ] 文档入库流程：上传 → 解析 → 切片 → 向量化 → 存储 → 状态更新
- [ ] 知识检索流程返回 Document 列表 + 置信分数 + 来源元数据
- [ ] 文档版本管理支持增量重建和版本号自增
- [ ] 入库失败处理标记 failed 并保留重试能力
- [ ] 知识库统计信息可查询

### 2.2 RAG 集成
- [ ] 通用模式 RAG：Agent 构建时传入 knowledge 对象，回复包含知识库引用
- [ ] 智能体自主模式 RAG：retrieve_knowledge 注册为 FunctionTool，Agent 自主调用
- [ ] KnowledgeInjectionMiddleware 在 system_prompt 中注入检索上下文和引用信息
- [ ] 知识库降级策略：Qdrant 异常时 Agent 仍可正常对话

### 2.3 知识库前端
- [ ] 知识库管理页面支持 CRUD 和配置
- [ ] 文档管理子页面支持上传/删除/重建索引/状态查看
- [ ] 切片查看子页面可查看切片详情
- [ ] 知识库统计组件正确展示

### 2.4 知识库路由
- [ ] `/api/v2/kb` 知识库 CRUD 接口可用
- [ ] `/api/v2/kb/{id}/documents` 文档管理接口可用
- [ ] `/api/v2/kb/{id}/chunks` 切片查询接口可用

### 2.5 异步技能迁移
- [ ] image-generator ExternalExecutionTool 异步执行并结果回传
- [ ] audio-transcription ExternalExecutionTool 异步执行
- [ ] ImageGeneration 前端页面对接 ExternalExecutionTool 模式
- [ ] AudioTranscribe 前端页面对接 ExternalExecutionTool 模式

### 2.6 MCP 和 Skill 接入
- [ ] MCPClient 可连接外部 MCP Server 并调用工具
- [ ] `/api/v2/mcp` MCP 配置管理接口可用
- [ ] LocalSkillLoader 可扫描技能目录并注册到 Toolkit
- [ ] `/api/v2/skills` Skill 管理接口可用

### 2.7 长期记忆
- [ ] 跨会话 AgentState 恢复：历史会话可恢复并继续对话
- [ ] 内存策略支持 session 和 persistent 两种模式

### 2.8 Phase 2 集成验证
- [ ] 知识库端到端验证：创建 → 上传 → 入库 → 绑定 → 知识增强回复含引用
- [ ] RAG 两种模式验证均正常工作
- [ ] 异步技能验证：图片生成 + 音频转写结果正确
- [ ] MCP 接入验证：MCP 工具调用成功
- [ ] Phase 1 回归验证全部通过

---

## Phase 3: 容量与可观测性

### 3.1 限流与降级
- [ ] 租户级限流：超限请求返回 429 + Retry-After
- [ ] 全局级限流：总并发超限触发排队
- [ ] LLM 级限流：LLM 并发超限触发降级
- [ ] 降级策略在压力场景下生效

### 3.2 可观测性
- [ ] Prometheus 指标端点可抓取
- [ ] MongoDB 执行日志结构化存储可查询
- [ ] 结构化告警事件在异常时生成

### 3.3 SSE 断线重连
- [ ] 前端 SSE 断线重连不丢消息
- [ ] 前端消息重建正确

### 3.4 性能优化
- [ ] 消息批量写库 QPS 提升 5x+
- [ ] 知识库入库并行化耗时降低 50%+
- [ ] AgentState 序列化单次 < 50ms

### 3.5 压力测试
- [ ] 200 并发 P95 延迟达标
- [ ] 2000 SSE 连接稳定
- [ ] 知识检索 P95 < 500ms
- [ ] AgentState 序列化/反序列化 < 50ms

### 3.6 可靠性测试
- [ ] Redis 故障恢复后会话可继续
- [ ] LLM 超时后降级策略生效
- [ ] Worker 重启后会话可恢复
- [ ] Qdrant 异常时仍可无知识增强对话

### 3.7 旧链路下线
- [ ] 历史数据完整迁移到新表结构
- [ ] 旧代码目录标记为废弃且不再被新服务引用
- [ ] 旧容器入口标记为 deprecated
