SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `sys_tenant` (
    `id` varchar(36) NOT NULL COMMENT '租户ID',
    `name` varchar(100) NOT NULL COMMENT '租户名称',
    `status` char(1) NOT NULL DEFAULT '0' COMMENT '状态 0正常 1停用',
    `skills_dir` varchar(255) DEFAULT NULL COMMENT '技能目录',
    `work_dir` varchar(255) DEFAULT NULL COMMENT '工作目录',
    `max_skills` int NOT NULL DEFAULT 100 COMMENT '最大技能数',
    `max_concurrent_executions` int NOT NULL DEFAULT 50 COMMENT '最大并发执行数',
    `metadata` json DEFAULT NULL COMMENT '元数据',
    `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `del_flag` char(1) NOT NULL DEFAULT '0',
    PRIMARY KEY (`id`),
    KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='租户表';

CREATE TABLE IF NOT EXISTS `sys_user` (
    `id` varchar(36) NOT NULL COMMENT '用户ID',
    `tenant_id` varchar(36) NOT NULL COMMENT '租户ID',
    `username` varchar(50) NOT NULL COMMENT '用户名',
    `password_hash` varchar(255) NOT NULL COMMENT '密码哈希',
    `nickname` varchar(50) DEFAULT NULL COMMENT '昵称',
    `email` varchar(100) DEFAULT NULL COMMENT '邮箱',
    `phone` varchar(20) DEFAULT NULL COMMENT '手机号',
    `avatar` varchar(255) DEFAULT NULL COMMENT '头像',
    `status` char(1) NOT NULL DEFAULT '0' COMMENT '状态 0正常 1停用',
    `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `del_flag` char(1) NOT NULL DEFAULT '0',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_tenant_username` (`tenant_id`, `username`),
    KEY `idx_tenant_id` (`tenant_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

CREATE TABLE IF NOT EXISTS `sys_role` (
    `id` varchar(36) NOT NULL COMMENT '角色ID',
    `tenant_id` varchar(36) NOT NULL COMMENT '租户ID',
    `role_name` varchar(50) NOT NULL COMMENT '角色名称',
    `role_code` varchar(50) NOT NULL COMMENT '角色编码',
    `description` varchar(500) DEFAULT NULL COMMENT '描述',
    `status` char(1) NOT NULL DEFAULT '0' COMMENT '状态 0正常 1停用',
    `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `del_flag` char(1) NOT NULL DEFAULT '0',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_tenant_role_code` (`tenant_id`, `role_code`),
    KEY `idx_tenant_id` (`tenant_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色表';

CREATE TABLE IF NOT EXISTS `sys_permission` (
    `id` varchar(36) NOT NULL COMMENT '权限ID',
    `permission_code` varchar(100) NOT NULL COMMENT '权限编码',
    `permission_name` varchar(100) NOT NULL COMMENT '权限名称',
    `resource_type` varchar(50) DEFAULT NULL COMMENT '资源类型',
    `action` varchar(50) DEFAULT NULL COMMENT '操作',
    `description` varchar(500) DEFAULT NULL COMMENT '描述',
    `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_permission_code` (`permission_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='权限表';

CREATE TABLE IF NOT EXISTS `sys_user_role` (
    `id` bigint NOT NULL AUTO_INCREMENT,
    `user_id` varchar(36) NOT NULL COMMENT '用户ID',
    `role_id` varchar(36) NOT NULL COMMENT '角色ID',
    `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_role` (`user_id`, `role_id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_role_id` (`role_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户角色关联表';

CREATE TABLE IF NOT EXISTS `sys_role_permission` (
    `id` bigint NOT NULL AUTO_INCREMENT,
    `role_id` varchar(36) NOT NULL COMMENT '角色ID',
    `permission_id` varchar(36) NOT NULL COMMENT '权限ID',
    `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_role_permission` (`role_id`, `permission_id`),
    KEY `idx_role_id` (`role_id`),
    KEY `idx_permission_id` (`permission_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色权限关联表';

CREATE TABLE IF NOT EXISTS `chat_provider` (
    `id` varchar(36) NOT NULL COMMENT '供应商ID',
    `tenant_id` varchar(36) NOT NULL COMMENT '租户ID',
    `provider_name` varchar(100) NOT NULL COMMENT '供应商名称',
    `provider_code` varchar(50) NOT NULL COMMENT '供应商编码',
    `api_base` varchar(255) DEFAULT NULL COMMENT 'API基础地址',
    `api_key` varchar(255) DEFAULT NULL COMMENT 'API密钥',
    `config` json DEFAULT NULL COMMENT '配置',
    `credential_schema` json DEFAULT NULL COMMENT 'AgentScope Credential Schema',
    `status` char(1) NOT NULL DEFAULT '0' COMMENT '状态 0正常 1停用',
    `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `del_flag` char(1) NOT NULL DEFAULT '0',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_tenant_provider_code` (`tenant_id`, `provider_code`),
    KEY `idx_tenant_id` (`tenant_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='模型供应商表';

CREATE TABLE IF NOT EXISTS `chat_model` (
    `id` varchar(36) NOT NULL COMMENT '模型ID',
    `tenant_id` varchar(36) NOT NULL COMMENT '租户ID',
    `provider_id` varchar(36) NOT NULL COMMENT '供应商ID',
    `model_name` varchar(100) NOT NULL COMMENT '模型名称',
    `model_code` varchar(100) NOT NULL COMMENT '模型编码',
    `model_type` varchar(20) NOT NULL DEFAULT 'chat' COMMENT '模型类型 chat/embedding',
    `context_size` int DEFAULT NULL COMMENT '上下文窗口大小',
    `output_size` int DEFAULT NULL COMMENT '最大输出token',
    `input_types` json DEFAULT NULL COMMENT '接受的MIME类型列表',
    `output_types` json DEFAULT NULL COMMENT '输出的MIME类型列表',
    `price_per_1k_input` decimal(10,6) DEFAULT NULL COMMENT '每1k输入token价格',
    `price_per_1k_output` decimal(10,6) DEFAULT NULL COMMENT '每1k输出token价格',
    `config` json DEFAULT NULL COMMENT '配置',
    `credential_type` varchar(50) DEFAULT NULL COMMENT 'AgentScope Credential类型',
    `status` char(1) NOT NULL DEFAULT '0' COMMENT '状态 0正常 1停用',
    `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `del_flag` char(1) NOT NULL DEFAULT '0',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_tenant_model_code` (`tenant_id`, `model_code`),
    KEY `idx_tenant_id` (`tenant_id`),
    KEY `idx_provider_id` (`provider_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='模型表';

CREATE TABLE IF NOT EXISTS `chat_session` (
    `id` varchar(36) NOT NULL COMMENT '会话ID',
    `tenant_id` varchar(36) NOT NULL COMMENT '租户ID',
    `user_id` varchar(36) NOT NULL COMMENT '用户ID',
    `agent_id` varchar(36) DEFAULT NULL COMMENT '智能体ID',
    `title` varchar(255) DEFAULT NULL COMMENT '会话标题',
    `active_skill_names` json DEFAULT NULL COMMENT '激活的技能名称',
    `metadata` json DEFAULT NULL COMMENT '元数据',
    `status` char(1) NOT NULL DEFAULT '0' COMMENT '状态 0正常 1结束',
    `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `del_flag` char(1) NOT NULL DEFAULT '0',
    PRIMARY KEY (`id`),
    KEY `idx_tenant_id` (`tenant_id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_agent_id` (`agent_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='会话表';

CREATE TABLE IF NOT EXISTS `chat_message` (
    `id` varchar(36) NOT NULL COMMENT '消息ID',
    `session_id` varchar(36) NOT NULL COMMENT '会话ID',
    `tenant_id` varchar(36) NOT NULL COMMENT '租户ID',
    `role` varchar(20) NOT NULL COMMENT '角色 user/assistant/system/tool',
    `content` text NOT NULL COMMENT '消息内容',
    `content_type` varchar(50) DEFAULT 'text' COMMENT '内容类型 text/image/audio/file',
    `skill_name` varchar(100) DEFAULT NULL COMMENT '技能名称',
    `tool_call_id` varchar(100) DEFAULT NULL COMMENT '工具调用ID',
    `tool_name` varchar(100) DEFAULT NULL COMMENT '工具名称',
    `tool_args` json DEFAULT NULL COMMENT '工具参数',
    `tool_result` json DEFAULT NULL COMMENT '工具结果',
    `total_tokens` int DEFAULT NULL COMMENT '总token数',
    `input_tokens` int DEFAULT NULL COMMENT '输入token数',
    `output_tokens` int DEFAULT NULL COMMENT '输出token数',
    `model_name` varchar(100) DEFAULT NULL COMMENT '模型名称',
    `metadata` json DEFAULT NULL COMMENT '元数据',
    `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `del_flag` char(1) NOT NULL DEFAULT '0',
    PRIMARY KEY (`id`),
    KEY `idx_session_id` (`session_id`),
    KEY `idx_tenant_id` (`tenant_id`),
    KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='消息表';

CREATE TABLE IF NOT EXISTS `agent_definition` (
    `id` varchar(36) NOT NULL COMMENT '智能体ID',
    `tenant_id` varchar(36) NOT NULL COMMENT '租户ID',
    `name` varchar(100) NOT NULL COMMENT '智能体名称',
    `agent_type` varchar(20) NOT NULL DEFAULT 'react' COMMENT '类型 react/conversational/workflow',
    `description` varchar(500) DEFAULT NULL COMMENT '描述',
    `sys_prompt` text NOT NULL COMMENT '系统提示词',
    `model_id` varchar(36) DEFAULT NULL COMMENT '绑定模型ID',
    `credential_id` varchar(36) DEFAULT NULL COMMENT '绑定凭证ID',
    `tool_group_config` json DEFAULT NULL COMMENT '工具组绑定配置',
    `kb_binding_config` json DEFAULT NULL COMMENT '知识库绑定配置',
    `context_config` json DEFAULT NULL COMMENT '上下文配置',
    `react_config` json DEFAULT NULL COMMENT 'React配置',
    `memory_policy` varchar(20) NOT NULL DEFAULT 'session' COMMENT '内存策略 session/persistent',
    `workspace_type` varchar(20) NOT NULL DEFAULT 'local' COMMENT '工作空间类型 local/docker',
    `avatar` varchar(255) DEFAULT NULL COMMENT '头像',
    `status` char(1) NOT NULL DEFAULT '0' COMMENT '状态 0正常 1停用',
    `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `del_flag` char(1) NOT NULL DEFAULT '0',
    PRIMARY KEY (`id`),
    KEY `idx_tenant_id` (`tenant_id`),
    KEY `idx_model_id` (`model_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='智能体定义表';

CREATE TABLE IF NOT EXISTS `tool_group_definition` (
    `id` varchar(36) NOT NULL COMMENT '工具组ID',
    `tenant_id` varchar(36) NOT NULL COMMENT '租户ID',
    `group_code` varchar(50) NOT NULL COMMENT '组编码',
    `group_name` varchar(100) NOT NULL COMMENT '组名称',
    `description` varchar(500) DEFAULT NULL COMMENT '描述',
    `instructions` text DEFAULT NULL COMMENT '激活时返回给Agent的指令',
    `is_active` tinyint(1) NOT NULL DEFAULT 1 COMMENT '默认是否激活',
    `status` char(1) NOT NULL DEFAULT '0' COMMENT '状态',
    `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `del_flag` char(1) NOT NULL DEFAULT '0',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_tenant_group_code` (`tenant_id`, `group_code`),
    KEY `idx_tenant_id` (`tenant_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工具组定义表';

CREATE TABLE IF NOT EXISTS `tool_definition` (
    `id` varchar(36) NOT NULL COMMENT '工具ID',
    `tenant_id` varchar(36) NOT NULL COMMENT '租户ID',
    `group_id` varchar(36) DEFAULT NULL COMMENT '所属工具组ID',
    `tool_code` varchar(100) NOT NULL COMMENT '工具编码',
    `tool_name` varchar(100) NOT NULL COMMENT '工具名称',
    `description` varchar(500) DEFAULT NULL COMMENT '工具描述',
    `runtime_type` varchar(20) NOT NULL COMMENT '运行类型 function/external/mcp/skill',
    `entrypoint` text DEFAULT NULL COMMENT '入口 Python函数路径/MCP URL/Skill路径',
    `schema_json` json DEFAULT NULL COMMENT 'JSON Schema',
    `is_concurrency_safe` tinyint(1) NOT NULL DEFAULT 1 COMMENT '是否并发安全',
    `is_read_only` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否只读',
    `permission_behavior` varchar(10) NOT NULL DEFAULT 'ask' COMMENT '权限行为 allow/ask/deny',
    `config` json DEFAULT NULL COMMENT '配置',
    `status` char(1) NOT NULL DEFAULT '0' COMMENT '状态',
    `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `del_flag` char(1) NOT NULL DEFAULT '0',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_tenant_tool_code` (`tenant_id`, `tool_code`),
    KEY `idx_tenant_id` (`tenant_id`),
    KEY `idx_group_id` (`group_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工具定义表';

CREATE TABLE IF NOT EXISTS `knowledge_base` (
    `id` varchar(36) NOT NULL COMMENT '知识库ID',
    `tenant_id` varchar(36) NOT NULL COMMENT '租户ID',
    `name` varchar(100) NOT NULL COMMENT '知识库名称',
    `description` varchar(500) DEFAULT NULL COMMENT '描述',
    `embedding_model` varchar(100) NOT NULL DEFAULT 'text-embedding-v4' COMMENT 'Embedding模型',
    `embedding_api_key` varchar(255) DEFAULT NULL COMMENT 'Embedding API Key',
    `dimensions` int NOT NULL DEFAULT 1024 COMMENT '向量维度',
    `qdrant_url` varchar(255) DEFAULT NULL COMMENT 'Qdrant地址',
    `qdrant_collection` varchar(100) DEFAULT NULL COMMENT 'Qdrant Collection名称',
    `retrieval_strategy` varchar(20) NOT NULL DEFAULT 'auto' COMMENT '检索策略 auto/agent_controlled',
    `chunk_size` int NOT NULL DEFAULT 512 COMMENT '切片大小',
    `top_k` int NOT NULL DEFAULT 5 COMMENT '默认检索数量',
    `score_threshold` float NOT NULL DEFAULT 0.5 COMMENT '置信阈值',
    `visibility` varchar(20) NOT NULL DEFAULT 'tenant' COMMENT '可见性 private/tenant/public',
    `allowed_roles` json DEFAULT NULL COMMENT '允许访问的角色',
    `status` char(1) NOT NULL DEFAULT '0' COMMENT '状态',
    `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `del_flag` char(1) NOT NULL DEFAULT '0',
    PRIMARY KEY (`id`),
    KEY `idx_tenant_id` (`tenant_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识库表';

CREATE TABLE IF NOT EXISTS `knowledge_document` (
    `id` varchar(36) NOT NULL COMMENT '文档ID',
    `kb_id` varchar(36) NOT NULL COMMENT '知识库ID',
    `tenant_id` varchar(36) NOT NULL COMMENT '租户ID',
    `filename` varchar(255) NOT NULL COMMENT '文件名',
    `original_filename` varchar(255) DEFAULT NULL COMMENT '原始文件名',
    `content_type` varchar(100) DEFAULT NULL COMMENT 'MIME类型',
    `storage_path` varchar(500) NOT NULL COMMENT 'MinIO存储路径',
    `file_size` bigint DEFAULT NULL COMMENT '文件大小',
    `parse_status` varchar(20) NOT NULL DEFAULT 'pending' COMMENT '解析状态 pending/parsing/chunking/embedding/completed/failed',
    `chunk_count` int NOT NULL DEFAULT 0 COMMENT '切片数量',
    `version` int NOT NULL DEFAULT 1 COMMENT '版本号',
    `error_message` text DEFAULT NULL COMMENT '失败原因',
    `metadata` json DEFAULT NULL COMMENT '元数据',
    `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_kb_id` (`kb_id`),
    KEY `idx_tenant_id` (`tenant_id`),
    KEY `idx_parse_status` (`parse_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识文档表';

CREATE TABLE IF NOT EXISTS `knowledge_chunk` (
    `id` varchar(36) NOT NULL COMMENT '切片ID',
    `document_id` varchar(36) NOT NULL COMMENT '文档ID',
    `kb_id` varchar(36) NOT NULL COMMENT '知识库ID',
    `tenant_id` varchar(36) NOT NULL COMMENT '租户ID',
    `chunk_index` int NOT NULL COMMENT '切片序号',
    `content` text NOT NULL COMMENT '切片内容',
    `metadata_json` json DEFAULT NULL COMMENT '元数据',
    `vector_id` varchar(100) DEFAULT NULL COMMENT 'Qdrant向量ID',
    `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_document_id` (`document_id`),
    KEY `idx_kb_id` (`kb_id`),
    KEY `idx_tenant_id` (`tenant_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识切片表';

CREATE TABLE IF NOT EXISTS `execution_trace` (
    `id` varchar(36) NOT NULL COMMENT '追踪ID',
    `tenant_id` varchar(36) NOT NULL COMMENT '租户ID',
    `session_id` varchar(36) NOT NULL COMMENT '会话ID',
    `agent_id` varchar(36) DEFAULT NULL COMMENT '智能体ID',
    `reply_id` varchar(36) DEFAULT NULL COMMENT 'AgentScope reply_id',
    `stage` varchar(30) NOT NULL COMMENT '阶段 reply/reasoning/acting/tool_call/knowledge_retrieval',
    `event_type` varchar(50) NOT NULL COMMENT 'AgentScope事件类型',
    `tool_name` varchar(100) DEFAULT NULL COMMENT '工具名称',
    `status` varchar(20) NOT NULL COMMENT '状态 started/completed/failed',
    `duration_ms` int DEFAULT NULL COMMENT '耗时',
    `input_tokens` int DEFAULT NULL COMMENT '输入token',
    `output_tokens` int DEFAULT NULL COMMENT '输出token',
    `payload_json` json DEFAULT NULL COMMENT '事件负载',
    `created_at` datetime NOT NULL COMMENT '创建时间',
    PRIMARY KEY (`id`),
    KEY `idx_tenant_id` (`tenant_id`),
    KEY `idx_session_id` (`session_id`),
    KEY `idx_agent_id` (`agent_id`),
    KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='执行追踪表';

SET FOREIGN_KEY_CHECKS = 1;
