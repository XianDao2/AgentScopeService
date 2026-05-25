# AgentScope v2 多租户智能体平台重构 Spec

## Why

现有 CoAssitant Skills 管理平台采用自研技能执行链路，缺乏标准化智能体框架支撑，且不具备企业知识库能力。需将其重构为基于 AgentScope v2 运行框架的新一代智能体平台，新增企业知识库能力，并在 8C16G 单机服务器上支撑 200+ 同时技能执行用户。

## What Changes

- 将自研技能执行链路替换为 AgentScope v2 Agent + Toolkit + Workspace 运行框架
- 基于 AgentScope Agent Service 构建 HTTP 服务层，扩展租户管理、知识库管理、工具组管理和执行日志路由
- 替换 AgentScope 默认 X-User-ID 认证为基于 JWT + RBAC 的企业级认证方案
- 新增企业知识库能力（SimpleKnowledge + QdrantStore + DashScopeTextEmbedding）
- 实现 TenantIsolationMiddleware、AuditLoggingMiddleware、KnowledgeInjectionMiddleware 三个自定义中间件
- 迁移现有技能为 AgentScope FunctionTool / ExternalExecutionTool / Skill
- 新增 7 张 MySQL 表（agent_definition、tool_group_definition、tool_definition、knowledge_base、knowledge_document、knowledge_chunk、execution_trace）
- 升级 2 张现有 MySQL 表（chat_model、chat_provider）
- 前端适配 AgentEvent SSE 流，新增智能体管理、工具组管理、知识库管理页面
- 实现三级限流（租户级/全局级/LLM 级）和降级策略
- 实现 Prometheus 指标输出和 MongoDB 执行日志

## Impact

- Affected specs: 智能体执行引擎、工具管理系统、会话管理、认证鉴权、知识库、前端界面
- Affected code: 全新项目 `src/ms3/`，无现有代码需要修改（从零构建）

## ADDED Requirements

### Requirement: AgentScope Agent 运行框架

系统 SHALL 使用 AgentScope v2 的 Agent 类作为智能体执行引擎。

#### Scenario: 构建 Agent 实例
- **WHEN** 根据智能体定义构建运行时 Agent 实例
- **THEN** 系统 SHALL 配置 Agent 的 name、system_prompt、model、toolkit、state、context_config、react_config 和 middlewares

#### Scenario: 流式对话
- **WHEN** 用户发起对话请求
- **THEN** 系统 SHALL 使用 Agent.reply_stream 产出 AgentEvent 事件流并通过 SSE 回传前端

#### Scenario: 上下文压缩
- **WHEN** 上下文 token 数量超过 trigger_ratio × model.context_length
- **THEN** 系统 SHALL 自动压缩上下文，对较旧消息进行摘要

#### Scenario: 用户确认
- **WHEN** Agent 遇到需要用户确认的工具调用（RequireUserConfirmEvent）
- **THEN** 系统 SHALL 暂停执行并回传确认请求给前端

### Requirement: Toolkit 和工具组

系统 SHALL 使用 AgentScope Toolkit 注册和管理所有工具函数、MCP 客户端和技能。

#### Scenario: 工具组管理
- **WHEN** 管理员在后台配置工具组
- **THEN** 系统 SHALL 使用 ToolGroup 将工具按业务领域分组，支持运行时通过 reset_tools 按组激活/停用

#### Scenario: 技能迁移
- **WHEN** 现有技能需要迁移
- **THEN** 系统 SHALL 支持迁移为 FunctionTool、MCPTool 或 Skill 三种形式

#### Scenario: 动态配置
- **WHEN** 管理员在后台修改工具组配置
- **THEN** 系统 SHALL 在不重启主服务的情况下更新 Toolkit 配置

### Requirement: Workspace 管理

系统 SHALL 使用 AgentScope Workspace 作为智能体执行环境。

#### Scenario: 本地工作空间
- **WHEN** 构建工作空间
- **THEN** 系统 SHALL 使用 LocalWorkspace 作为首期实现后端，按 tenant_id + agent_id 隔离工作目录

#### Scenario: Docker 工作空间
- **WHEN** Workspace 中需要执行不可信代码或需要强隔离
- **THEN** 系统 SHALL 支持切换到 DockerWorkspace 后端

#### Scenario: 工作空间生命周期
- **WHEN** Workspace 空闲超过 TTL
- **THEN** 系统 SHALL 通过 WorkspaceManager 自动淘汰并释放资源

### Requirement: Agent Service 集成

系统 SHALL 基于 AgentScope Agent Service 构建 HTTP 服务层。

#### Scenario: 服务启动
- **WHEN** 启动服务
- **THEN** 系统 SHALL 初始化 RedisStorage、LocalWorkspaceManager、注册扩展路由、替换认证依赖

#### Scenario: 会话持久化
- **WHEN** Agent reply 完成
- **THEN** 系统 SHALL 将 AgentState 持久化到 RedisStorage，同时同步写 chat_message 到 MySQL

#### Scenario: 会话恢复
- **WHEN** 用户恢复历史会话
- **THEN** 系统 SHALL 从 RedisStorage 加载 AgentState 并重建 Agent 实例

### Requirement: JWT + RBAC 认证

系统 SHALL 替换 AgentScope 默认的 X-User-ID 认证为基于 JWT + RBAC 的企业级认证方案。

#### Scenario: JWT 认证
- **WHEN** 用户访问 API 接口
- **THEN** 系统 SHALL 从 Authorization Header 提取 JWT 并验证用户身份

#### Scenario: RBAC 权限校验
- **WHEN** 用户调用受限工具或受限知识库
- **THEN** 系统 SHALL 校验角色权限（RBAC）、资源归属（tenant_id）和租户授权范围

#### Scenario: 认证依赖替换
- **WHEN** Agent Service 启动
- **THEN** 系统 SHALL 通过 dependency_overrides 替换默认的 get_current_user_id 依赖

### Requirement: 企业知识库

系统 SHALL 使用 AgentScope SimpleKnowledge 作为知识库核心实现。

#### Scenario: 知识库创建
- **WHEN** 管理员创建知识库
- **THEN** 系统 SHALL 支持设置名称、描述、租户归属、Embedding 模型选择、检索策略和权限范围

#### Scenario: 文档入库
- **WHEN** 用户上传文档到知识库
- **THEN** 系统 SHALL 使用 TextReader/ImageReader 解析、DashScopeTextEmbedding 向量化、QdrantStore 存储

#### Scenario: 知识检索
- **WHEN** 智能体需要知识增强
- **THEN** 系统 SHALL 支持通用模式（自动注入）和智能体自主模式（工具调用）两种 RAG 集成模式

#### Scenario: 入库失败处理
- **WHEN** 文档解析或向量化失败
- **THEN** 系统 SHALL 标记文档状态为 failed 并保留原始文件引用以支持重试

### Requirement: 自定义 Middleware

系统 SHALL 实现 AgentScope Middleware 在 Agent 生命周期的关键节点注入自定义逻辑。

#### Scenario: 租户隔离
- **WHEN** Agent 执行 reply 或 acting
- **THEN** TenantIsolationMiddleware SHALL 注入租户上下文并校验工具调用资源归属

#### Scenario: 审计日志
- **WHEN** Agent 调用模型
- **THEN** AuditLoggingMiddleware SHALL 记录 LLM 调用信息到 MongoDB

#### Scenario: 知识注入
- **WHEN** Agent 组装 system_prompt
- **THEN** KnowledgeInjectionMiddleware SHALL 注入知识检索结果和引用信息

### Requirement: 多租户管理

系统 SHALL 保留并增强现有租户管理能力。

#### Scenario: 数据隔离
- **WHEN** 任意租户访问智能体、知识库、会话或工具配置
- **THEN** 系统 SHALL 仅返回当前租户授权范围内的数据

#### Scenario: 租户停用
- **WHEN** 租户被停用
- **THEN** 系统 SHALL 阻止该租户发起新的智能体执行请求并保留历史审计数据

#### Scenario: 租户配额
- **WHEN** 租户处于活跃状态
- **THEN** 系统 SHALL 对该租户的并发配额、向量索引集合和对象存储路径进行独立管理

### Requirement: 对话系统

系统 SHALL 保留并增强现有对话能力。

#### Scenario: 流式事件回传
- **WHEN** Agent 执行过程中产生 AgentEvent
- **THEN** 系统 SHALL 将事件流转换为 SSE 事件回传前端

#### Scenario: 会话持久化
- **WHEN** 会话仍在进行中
- **THEN** 系统 SHALL 通过 AgentState 持久化会话上下文到 RedisStorage

#### Scenario: 执行中断
- **WHEN** 用户中断当前执行
- **THEN** 系统 SHALL 停止对应的 Agent reply_stream 迭代并回传中断状态

### Requirement: 技能迁移

系统 SHALL 将现有技能迁移为 AgentScope 工具形式。

#### Scenario: 公文生成
- **WHEN** 迁移 official-doc-writer 技能
- **THEN** 系统 SHALL 将其迁移为 ToolGroup(doc-tools)，包含 generate_document + preview_document + download_document 三个 FunctionTool

#### Scenario: 图片生成
- **WHEN** 迁移 image-generator 技能
- **THEN** 系统 SHALL 将其迁移为 ExternalExecutionTool，通过 BackgroundTaskManager 异步执行

#### Scenario: MCP 接入
- **WHEN** 需要接入外部 MCP 协议工具
- **THEN** 系统 SHALL 支持通过 MCPClient 接入，支持 Stateful 和 Stateless 两种连接模式

### Requirement: 三级限流与降级

系统 SHALL 实现三级限流和降级策略以支撑 200+ 并发。

#### Scenario: 租户级限流
- **WHEN** 单租户并发超过 max_concurrent_executions
- **THEN** 系统 SHALL 排队等待，超时返回 HTTP 429 + Retry-After

#### Scenario: 全局级限流
- **WHEN** 总并发超过 300
- **THEN** 系统 SHALL 新请求排队，优先保障已执行请求

#### Scenario: LLM 级限流
- **WHEN** LLM 调用并发超过 200
- **THEN** 系统 SHALL 信号量等待，超时降级为缓存回复

### Requirement: 可观测性

系统 SHALL 输出 Prometheus 格式核心指标和结构化执行日志。

#### Scenario: Prometheus 指标
- **WHEN** 管理员访问 /api/v2/observability/metrics
- **THEN** 系统 SHALL 输出请求总数/活跃会话/工具调用延迟/LLM 调用延迟/错误率/队列深度

#### Scenario: 执行日志
- **WHEN** 智能体执行请求进入系统
- **THEN** 系统 SHALL 记录 session_id、tenant_id、user_id、agent_id、阶段、耗时和结果状态

### Requirement: 前端适配

系统 SHALL 适配前端到 AgentScope AgentEvent SSE 流并新增管理页面。

#### Scenario: SSE 事件映射
- **WHEN** 前端接收 AgentEvent 流
- **THEN** 前端 SHALL 将 ReplyStartEvent→reply_start、TextBlockDeltaEvent→text_delta、ToolCallStartEvent→tool_call_start 等事件正确映射

#### Scenario: 智能体管理页面
- **WHEN** 管理员访问智能体管理页面
- **THEN** 页面 SHALL 支持 AgentDefinition 列表 + 新增/编辑/删除 + 工具组绑定 + 模型绑定

#### Scenario: 知识库管理页面
- **WHEN** 管理员访问知识库管理页面
- **THEN** 页面 SHALL 支持知识库 CRUD、文档上传/管理、切片查看

### Requirement: 数据模型

系统 SHALL 保留现有 8 张表、升级 2 张表、新增 7 张表。

#### Scenario: 新增智能体定义表
- **WHEN** 创建智能体定义
- **THEN** agent_definition 表 SHALL 包含 tenant_id、name、agent_type、sys_prompt、model_id、credential_id、tool_group_config、kb_binding_config、context_config、react_config 等字段

#### Scenario: 新增知识库表
- **WHEN** 创建知识库
- **THEN** knowledge_base 表 SHALL 包含 tenant_id、name、embedding_model、dimensions、qdrant_collection、retrieval_strategy 等字段

#### Scenario: Qdrant 集合隔离
- **WHEN** 为租户创建知识库向量存储
- **THEN** 系统 SHALL 使用 `tenant_{tenant_id}_kb_{kb_id}` 命名规则创建独立 collection

## MODIFIED Requirements

### Requirement: 模型管理升级

现有 chat_model 和 chat_provider 表 SHALL 增加字段以支持 AgentScope Credential 和 ModelCard。

- chat_model 增加：credential_type、context_size、output_size、input_types、output_types
- chat_provider 增加：credential_schema

### Requirement: 前端管理台升级

现有前端管理台 SHALL 保留全部页面和布局，并新增智能体管理、工具组管理、知识库管理页面。

## REMOVED Requirements

### Requirement: 自研技能执行链路

**Reason**: 替换为 AgentScope v2 Agent + Toolkit + Workspace 运行框架
**Migration**: 分阶段迁移，一期覆盖核心会话与技能执行，二期接入知识库和长期记忆，三期完成容量压测和旧链路下线

### Requirement: 自研 context_budget 模块

**Reason**: 替换为 AgentScope ContextConfig + Offloader
**Migration**: 使用 AgentScope ContextConfig 管理 trigger_ratio、reserve_ratio 和 tool_result_limit

### Requirement: 自研 _sessions 内存字典

**Reason**: 替换为 AgentScope AgentState + RedisStorage
**Migration**: 使用 RedisStorage 持久化 AgentState，支持多 worker、持久化、崩溃恢复
