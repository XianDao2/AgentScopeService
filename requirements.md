# 新项目详细需求方案

## 1 文档概述

### 1.1 项目背景

当前项目 CoAssitant Skills 管理平台是一个企业级多租户 AI 技能隔离管理平台，采用自研技能执行链路，支持技能注册、执行、对话式交互与 RBAC 权限控制。现需将其重构为基于 AgentScope v2 运行框架的新一代智能体平台，同时新增企业知识库能力，并在 8C16G 单机服务器上支撑 200+ 同时技能执行用户。

### 1.2 需求来源

- 现有系统功能保留与迁移需求
- AgentScope v2 框架能力接入需求（https://docs.agentscope.io/zh/v2/quickstart）
- 企业知识库新增需求
- 8C16G 单机 200+ 并发执行容量需求

### 1.3 术语表

| 术语 | 定义 |
|------|------|
| 新平台 | 基于 AgentScope v2 重构后的多租户智能体平台 |
| AgentScope v2 | 阿里达摩院开源的智能体开发框架，提供 Agent/Toolkit/Workspace/Service/RAG 等核心构建块 |
| Agent | AgentScope 中的无状态推理-行动循环引擎，集成 Model/Toolkit/Memory/Permission/Context |
| Toolkit | AgentScope 中的工具容器，注册和管理 Tool/MCP/Skill/ToolGroup |
| Tool Group | AgentScope 中的命名工具组，支持运行时按组激活/停用 |
| Skill | AgentScope 中基于 Markdown 的指令集，扩展 Agent 行为而无需写新工具代码 |
| MCP | Model Context Protocol，AgentScope 支持的标准化外部工具协议 |
| Workspace | AgentScope 中的执行环境，提供工具/技能/上下文卸载能力，支持 Local/Docker/E2B 三种后端 |
| WorkspaceManager | Workspace 的分配器和生命周期管理器，支持按 agent/user/session 隔离策略 |
| Agent Service | AgentScope 内置的 FastAPI 多租户多会话 HTTP 服务层 |
| Credential | AgentScope 中的模型供应商连接配置（API Key + 供应商设置） |
| AgentState | AgentScope 中可序列化的 Agent 完整状态，支持持久化到 Redis |
| SimpleKnowledge | AgentScope RAG 中的知识库实现，结合 Embedding 模型和向量存储 |
| QdrantStore | AgentScope RAG 支持的向量存储后端 |
| TextReader/ImageReader | AgentScope RAG 中的文档解析器 |
| 租户 | 在平台上拥有独立数据、权限、智能体配置和知识库空间的组织单元 |
| 智能体定义 | 平台管理的智能体配置模板，包含系统提示词、模型绑定、工具组绑定、知识库绑定 |
| 工具定义 | 平台管理的工具注册信息，映射到 AgentScope Tool/FunctionTool/MCPTool |
| 知识库 | 由文档解析、切片、向量化、索引检索和引用回传组成的企业知识增强模块 |
| 会话 | 用户与智能体的一次连续交互过程，对应 AgentScope Session |
| 执行链路 | 从用户发起请求到智能体完成回复或任务结果返回的完整流程 |
| 并发执行用户 | 在同一时间窗口内处于技能执行、工作流执行或知识库检索中的在线用户 |

---

## 2 现有系统功能保留需求

### 2.1 多租户管理

**FR-2.1-1** WHEN 任意租户访问智能体、知识库、会话或工具配置, THE 新平台 SHALL 仅返回当前租户授权范围内的数据。

**FR-2.1-2** WHEN 新平台为租户创建智能体运行上下文, THE 新平台 SHALL 绑定租户级模型配置（Credential）、工具组（ToolGroup）、知识库（Knowledge）和权限策略（Permission）。

**FR-2.1-3** WHILE 租户处于活跃状态, THE 新平台 SHALL 对该租户的并发配额、向量索引集合和对象存储路径进行独立管理。

**FR-2.1-4** IF 租户被停用, THE 新平台 SHALL 阻止该租户发起新的智能体执行请求并保留历史审计数据。

### 2.2 用户与权限管理

**FR-2.2-1** WHEN 用户访问管理后台或对话能力, THE 新平台 SHALL 通过统一认证鉴权机制校验用户身份和操作权限。

**FR-2.2-2** WHEN 用户调用受限工具或受限知识库, THE 新平台 SHALL 校验角色权限（RBAC）、资源归属（tenant_id）和租户授权范围。

**FR-2.2-3** WHEN 用户执行管理操作, THE 新平台 SHALL 记录操作审计日志。

**FR-2.2-4** IF 系统检测到未授权访问, THE 新平台 SHALL 拒绝请求并记录安全事件。

**FR-2.2-5** THE 新平台 SHALL 保留现有 sys_user、sys_role、sys_permission、sys_user_role、sys_role_permission 五张表的数据模型和权限分配逻辑。

### 2.3 对话系统

**FR-2.3-1** WHEN 用户发起文本、文件或多模态输入, THE 新平台 SHALL 创建 UserMsg 并交由 AgentScope Agent 处理。

**FR-2.3-2** WHEN Agent 执行过程中产生 TextBlockDeltaEvent、ThinkingBlockDeltaEvent、ToolCallStartEvent、ToolResultEndEvent 等事件, THE 新平台 SHALL 将 AgentEvent 流转换为 SSE 事件回传前端。

**FR-2.3-3** WHILE 会话仍在进行中, THE 新平台 SHALL 通过 AgentScope AgentState 持久化会话上下文到 RedisStorage。

**FR-2.3-4** IF 用户中断当前执行, THE 新平台 SHALL 停止对应的 Agent reply_stream 迭代并回传中断状态。

**FR-2.3-5** THE 新平台 SHALL 保留现有会话历史消息（chat_session、chat_message）的存储和分页查询能力。

### 2.4 模型管理

**FR-2.4-1** THE 新平台 SHALL 保留现有 chat_model 和 chat_provider 表，同时将模型供应商密钥映射为 AgentScope Credential。

**FR-2.4-2** WHEN 管理员新增或修改模型供应商配置, THE 新平台 SHALL 在不重启主服务的情况下完成配置生效。

**FR-2.4-3** THE 新平台 SHALL 支持多个模型供应商并存，包括阿里云百炼、OpenAI、DeepSeek、智谱 AI，以及自部署 Ollama 等。

### 2.5 管理后台

**FR-2.5-1** THE 新平台 SHALL 保留现有前端管理台的全部页面和布局。

**FR-2.5-2** THE 新平台 SHALL 新增智能体管理页面、工具组管理页面、知识库管理页面。

**FR-2.5-3** THE 新平台 SHALL 保留现有字典管理、菜单管理、反馈系统和健康检查能力。

### 2.6 文件上传与预览

**FR-2.6-1** THE 新平台 SHALL 保留现有文件上传、MinIO 对象存储集成和文件预览能力。

**FR-2.6-2** THE 新平台 SHALL 将文件上传能力扩展为支持知识库文档入库。

### 2.7 执行日志与可观测性

**FR-2.7-1** WHEN 智能体执行请求进入系统, THE 新平台 SHALL 记录 session_id、tenant_id、user_id、agent_id 和开始时间。

**FR-2.7-2** WHEN Agent 调用工具、知识库或工作流, THE 新平台 SHALL 从 AgentEvent 流中提取 ToolCallStartEvent、ToolResultEndEvent、ModelCallStartEvent、ModelCallEndEvent 等事件并记录阶段、耗时、结果状态。

**FR-2.7-3** WHEN 管理员查看运行日志, THE 新平台 SHALL 支持按租户、会话、智能体、工具和时间范围进行查询。

**FR-2.7-4** IF 某次执行超时、失败或降级, THE 新平台 SHALL 生成结构化告警事件。

### 2.8 异步任务系统

**FR-2.8-1** THE 新平台 SHALL 保留现有异步任务的创建、查询、取消和状态追踪能力。

**FR-2.8-2** THE 新平台 SHALL 利用 AgentScope Agent Service 的 BackgroundTaskManager 接管异步工具执行的生命周期管理。

---

## 3 AgentScope v2 框架接入需求

### 3.1 Agent 运行框架

**FR-3.1-1** THE 新平台 SHALL 使用 AgentScope v2 的 Agent 类作为智能体执行引擎，替代现有自研技能执行主链路。

**FR-3.1-2** WHEN 构建运行时 Agent 实例, THE 新平台 SHALL 根据智能体定义配置 Agent 的 name、system_prompt、model、toolkit、state、context_config 和 react_config。

**FR-3.1-3** THE 新平台 SHALL 使用 Agent.reply_stream 作为流式对话入口，产出 AgentEvent 事件流。

**FR-3.1-4** THE 新平台 SHALL 使用 AgentScope ContextConfig 管理上下文窗口压缩策略，替代现有自研 context_budget 模块。

**FR-3.1-5** WHEN Agent 遇到需要用户确认的工具调用（RequireUserConfirmEvent）, THE 新平台 SHALL 暂停执行并回传确认请求给前端。

**FR-3.1-6** THE 新平台 SHALL 使用 AgentScope ReActConfig 控制最大推理-行动迭代次数和拒绝处理策略。

### 3.2 Toolkit 和工具组

**FR-3.2-1** THE 新平台 SHALL 使用 AgentScope Toolkit 注册和管理所有工具函数、MCP 客户端和技能。

**FR-3.2-2** THE 新平台 SHALL 使用 AgentScope ToolGroup 将工具按业务领域分组，支持运行时通过 reset_tools 元工具按组激活/停用。

**FR-3.2-3** THE 新平台 SHALL 支持将现有技能迁移为以下三种形式之一：
- FunctionTool（轻量级同步/异步工具函数）
- MCPTool（通过 MCP 协议接入外部工具服务）
- Skill（基于 SKILL.md 的指令集）

**FR-3.2-4** WHEN 管理员在后台配置工具组, THE 新平台 SHALL 在不重启主服务的情况下更新 Toolkit 配置。

### 3.3 Workspace

**FR-3.3-1** THE 新平台 SHALL 使用 AgentScope Workspace 作为智能体执行环境，提供工具/技能/上下文卸载能力。

**FR-3.3-2** THE 新平台 SHALL 使用 LocalWorkspace 作为首期 Workspace 实现后端，按 tenant_id + agent_id 隔离工作目录。

**FR-3.3-3** THE 新平台 SHALL 使用 AgentScope WorkspaceManager 管理 Workspace 的分配、缓存和 TTL 淘汰。

**FR-3.3-4** WHEN Workspace 中需要执行不可信代码或需要强隔离, THE 新平台 SHALL 支持切换到 DockerWorkspace 后端。

### 3.4 Agent Service 集成

**FR-3.4-1** THE 新平台 SHALL 基于 AgentScope Agent Service 构建 HTTP 服务层，利用其内置的 SessionManager、BackgroundTaskManager、WorkspaceManager 和 ChatService。

**FR-3.4-2** THE 新平台 SHALL 使用 AgentScope RedisStorage 作为 Agent/Session/Credential/Message/Schedule 的持久化存储。

**FR-3.4-3** THE 新平台 SHALL 替换 AgentScope 默认的 X-User-ID 认证为基于 JWT + RBAC 的企业级认证方案。

**FR-3.4-4** THE 新平台 SHALL 在 Agent Service 的基础上扩展租户管理、知识库管理、工具组管理和执行日志查询等自定义路由。

### 3.5 AgentState 持久化

**FR-3.5-1** THE 新平台 SHALL 在每次 Agent reply 完成后将 AgentState 持久化到 RedisStorage。

**FR-3.5-2** WHEN 用户恢复历史会话, THE 新平台 SHALL 从 RedisStorage 加载 AgentState 并重建 Agent 实例。

**FR-3.5-3** THE 新平台 SHALL 同步将会话消息写入 MySQL chat_message 表，保留现有消息历史查询能力。

### 3.6 Permission System

**FR-3.6-1** THE 新平台 SHALL 利用 AgentScope Permission System 控制工具调用的执行权限。

**FR-3.6-2** WHEN 工具调用触发权限检查, THE 新平台 SHALL 根据 RBAC 角色和租户授权范围决定 ALLOW/ASK/DENY。

**FR-3.6-3** THE 新平台 SHALL 将现有技能可见性控制（private/tenant/public）映射到 AgentScope Permission 策略。

### 3.7 Middleware

**FR-3.7-1** THE 新平台 SHALL 使用 AgentScope Middleware 在 Agent 生命周期的关键节点注入自定义逻辑。

**FR-3.7-2** THE 新平台 SHALL 实现 TenantIsolationMiddleware，在 reply 和 acting 钩子中注入租户上下文。

**FR-3.7-3** THE 新平台 SHALL 实现 AuditLoggingMiddleware，在 model_call 钩子中记录 LLM 调用信息。

**FR-3.7-4** THE 新平台 SHALL 实现 KnowledgeInjectionMiddleware，在 system_prompt 钩子中注入知识检索结果。

---

## 4 知识库新增需求

### 4.1 知识库管理

**FR-4.1-1** WHEN 管理员创建知识库, THE 新平台 SHALL 支持设置知识库名称、描述、租户归属、Embedding 模型选择、检索策略和权限范围。

**FR-4.1-2** WHEN 管理员停用知识库, THE 新平台 SHALL 阻止新会话继续使用该知识库并保留审计记录。

**FR-4.1-3** WHILE 知识库处于启用状态, THE 新平台 SHALL 提供文档数量、切片数量、索引状态和最近更新时间等统计信息。

**FR-4.1-4** THE 新平台 SHALL 使用 AgentScope SimpleKnowledge 作为知识库核心实现。

**FR-4.1-5** THE 新平台 SHALL 使用 QdrantStore 作为向量存储后端，每个租户使用独立的 collection。

### 4.2 文档入库

**FR-4.2-1** WHEN 用户上传文档到知识库, THE 新平台 SHALL 使用 AgentScope TextReader 或 ImageReader 完成文档解析和切片。

**FR-4.2-2** WHEN 文档切片完成, THE 新平台 SHALL 使用 DashScopeTextEmbedding 将切片向量化并写入 QdrantStore。

**FR-4.2-3** WHEN 文档入库全流程完成, THE 新平台 SHALL 更新知识库文档状态为 completed 并记录切片数量。

**FR-4.2-4** IF 文档解析或向量化失败, THE 新平台 SHALL 标记文档状态为 failed 并保留原始文件引用以支持重试。

**FR-4.2-5** THE 新平台 SHALL 支持以下文档格式：TXT、PDF、DOCX、MD、图片（PNG/JPG/WEBP）。

### 4.3 知识检索增强

**FR-4.3-1** WHEN 智能体需要知识增强, THE 新平台 SHALL 使用 SimpleKnowledge.retrieve 进行向量检索。

**FR-4.3-2** THE 新平台 SHALL 支持两种 RAG 集成模式：
- 通用模式：将 Knowledge 对象直接传给 Agent 构造参数，自动在回复前注入检索上下文
- 智能体自主模式：将 retrieve_knowledge 注册为 Toolkit 中的工具函数，由 Agent 自主决定何时调用

**FR-4.3-3** WHEN 系统返回知识增强答案, THE 新平台 SHALL 回传引用片段、来源文档名称、切片编号和命中置信分数。

**FR-4.3-4** IF 知识库检索失败, THE 新平台 SHALL 降级为无知识增强模式并记录告警。

### 4.4 文档版本管理

**FR-4.4-1** WHEN 管理员更新文档版本, THE 新平台 SHALL 支持增量重建对应文档的切片和向量索引。

**FR-4.4-2** WHEN 管理员删除文档, THE 新平台 SHALL 从向量存储中移除对应切片并更新知识库统计信息。

**FR-4.4-3** THE 新平台 SHALL 保留文档历史版本号，支持按版本回溯切片内容。

---

## 5 技能迁移需求

### 5.1 公文生成技能

**FR-5.1-1** THE 新平台 SHALL 将现有 official-doc-writer 技能迁移为 AgentScope FunctionTool，封装公文生成逻辑。

**FR-5.1-2** THE 新平台 SHALL 将公文生成的多轮对话交互映射为 AgentScope ReActAgent 的工具调用循环。

**FR-5.1-3** THE 新平台 SHALL 将公文 Word 文件生成和签名 URL 下载保持为现有实现。

### 5.2 文档摘要技能

**FR-5.2-1** THE 新平台 SHALL 将现有 document-summary 技能迁移为 AgentScope FunctionTool。

### 5.3 图片生成技能

**FR-5.3-1** THE 新平台 SHALL 将现有 image-generator 技能迁移为 AgentScope ExternalExecutionTool，通过异步任务系统执行。

**FR-5.3-2** WHEN 图片生成任务完成, THE 新平台 SHALL 通过 ExternalExecutionResultEvent 将结果注入 Agent 上下文。

### 5.4 音频转写技能

**FR-5.4-1** THE 新平台 SHALL 将现有 audio-transcription 技能迁移为 AgentScope ExternalExecutionTool。

### 5.5 邮件助手技能

**FR-5.5-1** THE 新平台 SHALL 将现有 email-helper 技能迁移为 AgentScope FunctionTool。

### 5.6 MCP 工具接入

**FR-5.6-1** THE 新平台 SHALL 支持通过 AgentScope MCPClient 接入外部 MCP 协议工具服务。

**FR-5.6-2** THE 新平台 SHALL 支持 Stateful（STDIO/HTTP）和 Stateless（HTTP）两种 MCP 连接模式。

### 5.7 Skill 指令集

**FR-5.7-1** THE 新平台 SHALL 支持将现有 SKILL.md 格式的技能直接作为 AgentScope Skill 注册到 Toolkit。

**FR-5.7-2** THE 新平台 SHALL 支持 LocalSkillLoader 扫描技能目录并自动注册。

---

## 6 非功能需求

### 6.1 并发容量需求

**NFR-6.1-1** THE 新平台 SHALL 在 8C16G 单机服务器部署条件下，支持同时处于技能执行中的在线用户数量大于 200 人。

**NFR-6.1-2** WHEN 200 个以上并发用户同时发起执行请求, THE 新平台 SHALL 通过队列、限流、连接池和异步执行机制保持服务可用。

**NFR-6.1-3** WHILE 系统处于 200+ 并发压力下, THE 新平台 SHALL 保持核心接口可访问且不会因单租户突发流量导致全局服务不可用。

**NFR-6.1-4** IF 实时负载超过安全阈值, THE 新平台 SHALL 启动限流、降级或排队策略并记录容量告警事件。

### 6.2 响应时间需求

**NFR-6.2-1** 普通聊天回复 P95 延迟 SHALL 小于 3 秒（不含 LLM 服务延迟）。

**NFR-6.2-2** 知识库检索 P95 延迟 SHALL 小于 500 毫秒。

**NFR-6.2-3** 工具调用从 ToolCallStartEvent 到 ToolResultEndEvent 的 P95 延迟 SHALL 小于 5 秒（不含外部服务延迟）。

### 6.3 可用性需求

**NFR-6.3-1** THE 新平台 SHALL 支持单进程崩溃后自动恢复会话状态（通过 RedisStorage AgentState 持久化）。

**NFR-6.3-2** THE 新平台 SHALL 支持前端 SSE 断线重连和事件回放（利用 AgentScope SessionManager 的 buffered replay）。

**NFR-6.3-3** THE 新平台 SHALL 在 Redis 不可用时限制新任务接入并保留只读后台能力。

### 6.4 安全需求

**NFR-6.4-1** 所有 API 接口 SHALL 经过 JWT 认证和 RBAC 权限校验。

**NFR-6.4-2** 跨租户数据访问 SHALL 被严格阻止。

**NFR-6.4-3** 模型供应商 API Key SHALL 加密存储在 Credential 中。

**NFR-6.4-4** 工具调用 SHALL 经过 AgentScope Permission System 校验。

### 6.5 可观测性需求

**NFR-6.5-1** THE 新平台 SHALL 输出 Prometheus 格式的核心指标。

**NFR-6.5-2** THE 新平台 SHALL 输出结构化执行日志到 MongoDB。

**NFR-6.5-3** THE 新平台 SHALL 支持按 tenant_id + session_id 追踪完整执行链路。

---

## 7 迁移策略需求

**FR-7-1** THE 新平台 SHALL 支持分阶段迁移，一期覆盖核心会话与技能执行，二期接入知识库和长期记忆，三期完成容量压测和旧链路下线。

**FR-7-2** WHILE 迁移仍在进行中, THE 新平台 SHALL 支持旧能力与新能力并行验证。

**FR-7-3** IF 新架构验证结果不满足关键性能指标, THE 新平台 SHALL 保留回切到兼容执行链路的能力。

**FR-7-4** THE 新平台 SHALL 提供迁移清单、兼容策略和回滚方案。

---

## 8 约束与假设

### 8.1 约束

- 后端只能使用 Docker 容器部署，不能使用 `python run.py` 直接启动
- 数据必须采用 MySQL 或 Redis 存储
- AgentScope v2 要求 Python 3.11+
- 向量存储使用 Qdrant（AgentScope RAG 官方支持）
- 单机部署，8C16G

### 8.2 假设

- LLM 服务（阿里云百炼等）为外部托管服务，不计入 8C16G 资源预算
- Qdrant 可部署在同一台服务器或使用内存模式
- 现有前端 Vue3 管理台代码可复用和扩展
