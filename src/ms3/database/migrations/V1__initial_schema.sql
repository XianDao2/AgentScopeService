-- ============================================================
-- V1__initial_schema.sql
-- MS3 初始数据库架构
-- 字符集: utf8mb4 | 引擎: InnoDB
-- ============================================================

-- -----------------------------------------------------------
-- 第一部分：系统基础表（8 张）
-- -----------------------------------------------------------

CREATE TABLE sys_tenant (
    id              VARCHAR(36)   NOT NULL,
    name            VARCHAR(100)  DEFAULT NULL,
    status          CHAR(1)       DEFAULT '0',
    skills_dir      VARCHAR(255)  DEFAULT NULL,
    work_dir        VARCHAR(255)  DEFAULT NULL,
    max_skills      INT           DEFAULT 10,
    max_concurrent_executions INT DEFAULT 50,
    metadata        JSON          DEFAULT NULL,
    created_at      DATETIME      DEFAULT NULL,
    updated_at      DATETIME      DEFAULT NULL,
    del_flag        CHAR(1)       DEFAULT '0',
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE sys_user (
    id              VARCHAR(36)   NOT NULL,
    tenant_id       VARCHAR(36)   NOT NULL,
    username        VARCHAR(50)   NOT NULL,
    password_hash   VARCHAR(255)  NOT NULL,
    display_name    VARCHAR(100)  DEFAULT NULL,
    email           VARCHAR(100)  DEFAULT NULL,
    phone           VARCHAR(20)   DEFAULT NULL,
    avatar          VARCHAR(255)  DEFAULT NULL,
    is_active       TINYINT(1)    DEFAULT 1,
    created_at      DATETIME      DEFAULT NULL,
    updated_at      DATETIME      DEFAULT NULL,
    del_flag        CHAR(1)       DEFAULT '0',
    PRIMARY KEY (id),
    INDEX idx_tenant_id (tenant_id),
    UNIQUE INDEX idx_tenant_username (tenant_id, username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE sys_role (
    id              VARCHAR(36)   NOT NULL,
    tenant_id       VARCHAR(36)   NOT NULL,
    role_name       VARCHAR(50)   NOT NULL,
    description     VARCHAR(200)  DEFAULT NULL,
    status          CHAR(1)       DEFAULT '0',
    created_at      DATETIME      DEFAULT NULL,
    updated_at      DATETIME      DEFAULT NULL,
    del_flag        CHAR(1)       DEFAULT '0',
    PRIMARY KEY (id),
    INDEX idx_tenant_id (tenant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE sys_permission (
    id              VARCHAR(36)   NOT NULL,
    code            VARCHAR(50)   NOT NULL,
    name            VARCHAR(100)  NOT NULL,
    resource_type   VARCHAR(20)   DEFAULT NULL,
    action          VARCHAR(20)   DEFAULT NULL,
    description     VARCHAR(200)  DEFAULT NULL,
    created_at      DATETIME      DEFAULT NULL,
    PRIMARY KEY (id),
    UNIQUE INDEX code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE sys_user_role (
    id              VARCHAR(36)   NOT NULL,
    user_id         VARCHAR(36)   NOT NULL,
    role_id         VARCHAR(36)   NOT NULL,
    PRIMARY KEY (id),
    INDEX idx_user_id (user_id),
    INDEX idx_role_id (role_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE sys_role_permission (
    id              VARCHAR(36)   NOT NULL,
    role_id         VARCHAR(36)   NOT NULL,
    permission_id   VARCHAR(36)   NOT NULL,
    PRIMARY KEY (id),
    INDEX idx_role_id (role_id),
    INDEX idx_permission_id (permission_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE chat_session (
    id                  VARCHAR(36)   NOT NULL,
    tenant_id           VARCHAR(36)   NOT NULL,
    user_id             VARCHAR(36)   NOT NULL,
    title               VARCHAR(200)  DEFAULT NULL,
    active_skill_names  JSON          DEFAULT NULL,
    metadata            JSON          DEFAULT NULL,
    created_at          DATETIME      DEFAULT NULL,
    updated_at          DATETIME      DEFAULT NULL,
    del_flag            CHAR(1)       DEFAULT '0',
    PRIMARY KEY (id),
    INDEX idx_tenant_id (tenant_id),
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE chat_message (
    id              VARCHAR(36)   NOT NULL,
    session_id      VARCHAR(36)   NOT NULL,
    role            VARCHAR(20)   NOT NULL,
    content         TEXT          DEFAULT NULL,
    skill_name      VARCHAR(100)  DEFAULT NULL,
    total_tokens    INT           DEFAULT NULL,
    model_name      VARCHAR(100)  DEFAULT NULL,
    metadata        JSON          DEFAULT NULL,
    created_at      DATETIME      DEFAULT NULL,
    PRIMARY KEY (id),
    INDEX idx_session_id (session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------
-- 第二部分：升级表（2 张）
-- -----------------------------------------------------------

CREATE TABLE chat_provider (
    id                VARCHAR(36)   NOT NULL,
    tenant_id         VARCHAR(36)   NOT NULL,
    provider_code     VARCHAR(50)   NOT NULL,
    provider_name     VARCHAR(100)  NOT NULL,
    description       VARCHAR(500)  DEFAULT NULL,
    api_base          VARCHAR(255)  DEFAULT NULL,
    status            CHAR(1)       DEFAULT '0',
    created_at        DATETIME      DEFAULT NULL,
    updated_at        DATETIME      DEFAULT NULL,
    del_flag          CHAR(1)       DEFAULT '0',
    credential_schema JSON          DEFAULT NULL,
    PRIMARY KEY (id),
    INDEX idx_tenant_id (tenant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE chat_model (
    id              VARCHAR(36)   NOT NULL,
    tenant_id       VARCHAR(36)   NOT NULL,
    provider_id     VARCHAR(36)   DEFAULT NULL,
    model_code      VARCHAR(100)  NOT NULL,
    model_name      VARCHAR(100)  NOT NULL,
    description     VARCHAR(500)  DEFAULT NULL,
    api_key         VARCHAR(255)  DEFAULT NULL,
    api_base        VARCHAR(255)  DEFAULT NULL,
    is_default      TINYINT(1)    DEFAULT 0,
    status          CHAR(1)       DEFAULT '0',
    created_at      DATETIME      DEFAULT NULL,
    updated_at      DATETIME      DEFAULT NULL,
    del_flag        CHAR(1)       DEFAULT '0',
    credential_type VARCHAR(50)   DEFAULT NULL,
    context_size    INT           DEFAULT NULL,
    output_size     INT           DEFAULT NULL,
    input_types     JSON          DEFAULT NULL,
    output_types    JSON          DEFAULT NULL,
    PRIMARY KEY (id),
    INDEX idx_tenant_id (tenant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------
-- 第三部分：新增表（7 张）
-- -----------------------------------------------------------

CREATE TABLE agent_definition (
    id                  VARCHAR(36)   NOT NULL,
    tenant_id           VARCHAR(36)   NOT NULL,
    name                VARCHAR(100)  NOT NULL,
    agent_type          VARCHAR(20)   NOT NULL DEFAULT 'react',
    sys_prompt          TEXT          NOT NULL,
    model_id            VARCHAR(36)   DEFAULT NULL,
    credential_id       VARCHAR(36)   DEFAULT NULL,
    tool_group_config   JSON          DEFAULT NULL,
    kb_binding_config   JSON          DEFAULT NULL,
    context_config      JSON          DEFAULT NULL,
    react_config        JSON          DEFAULT NULL,
    memory_policy       VARCHAR(20)   NOT NULL DEFAULT 'session',
    workspace_type      VARCHAR(20)   NOT NULL DEFAULT 'local',
    status              CHAR(1)       NOT NULL DEFAULT '0',
    created_at          DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    del_flag            CHAR(1)       NOT NULL DEFAULT '0',
    PRIMARY KEY (id),
    INDEX idx_tenant_id (tenant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE tool_group_definition (
    id              VARCHAR(36)   NOT NULL,
    tenant_id       VARCHAR(36)   NOT NULL,
    group_code      VARCHAR(50)   NOT NULL,
    group_name      VARCHAR(100)  NOT NULL,
    description     VARCHAR(500)  DEFAULT NULL,
    instructions    TEXT          DEFAULT NULL,
    is_active       TINYINT(1)    NOT NULL DEFAULT 1,
    status          CHAR(1)       NOT NULL DEFAULT '0',
    created_at      DATETIME      NOT NULL,
    updated_at      DATETIME      NOT NULL,
    del_flag        CHAR(1)       NOT NULL DEFAULT '0',
    PRIMARY KEY (id),
    INDEX idx_tenant_id (tenant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE tool_definition (
    id                    VARCHAR(36)   NOT NULL,
    tenant_id             VARCHAR(36)   NOT NULL,
    group_id              VARCHAR(36)   DEFAULT NULL,
    tool_code             VARCHAR(100)  NOT NULL,
    tool_name             VARCHAR(100)  NOT NULL,
    description           VARCHAR(500)  DEFAULT NULL,
    runtime_type          VARCHAR(20)   NOT NULL,
    entrypoint            TEXT          DEFAULT NULL,
    schema_json           JSON          DEFAULT NULL,
    is_concurrency_safe   TINYINT(1)    NOT NULL DEFAULT 1,
    is_read_only          TINYINT(1)    NOT NULL DEFAULT 0,
    permission_behavior   VARCHAR(10)   NOT NULL DEFAULT 'ask',
    status                CHAR(1)       NOT NULL DEFAULT '0',
    created_at            DATETIME      NOT NULL,
    updated_at            DATETIME      NOT NULL,
    del_flag              CHAR(1)       NOT NULL DEFAULT '0',
    PRIMARY KEY (id),
    INDEX idx_tenant_id (tenant_id),
    INDEX idx_group_id (group_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE knowledge_base (
    id                  VARCHAR(36)   NOT NULL,
    tenant_id           VARCHAR(36)   NOT NULL,
    name                VARCHAR(100)  NOT NULL,
    description         VARCHAR(500)  DEFAULT NULL,
    embedding_model     VARCHAR(100)  NOT NULL DEFAULT 'text-embedding-v4',
    embedding_api_key   VARCHAR(255)  DEFAULT NULL,
    dimensions          INT           NOT NULL DEFAULT 1024,
    qdrant_url          VARCHAR(255)  DEFAULT NULL,
    qdrant_collection   VARCHAR(100)  DEFAULT NULL,
    retrieval_strategy  VARCHAR(20)   NOT NULL DEFAULT 'auto',
    chunk_size          INT           NOT NULL DEFAULT 512,
    top_k               INT           NOT NULL DEFAULT 5,
    score_threshold     FLOAT         NOT NULL DEFAULT 0.5,
    visibility          VARCHAR(20)   NOT NULL DEFAULT 'tenant',
    allowed_roles       JSON          DEFAULT NULL,
    status              CHAR(1)       NOT NULL DEFAULT '0',
    created_at          DATETIME      NOT NULL,
    updated_at          DATETIME      NOT NULL,
    del_flag            CHAR(1)       NOT NULL DEFAULT '0',
    PRIMARY KEY (id),
    INDEX idx_tenant_id (tenant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE knowledge_document (
    id              VARCHAR(36)   NOT NULL,
    kb_id           VARCHAR(36)   NOT NULL,
    tenant_id       VARCHAR(36)   NOT NULL,
    filename        VARCHAR(255)  NOT NULL,
    content_type    VARCHAR(100)  DEFAULT NULL,
    storage_path    VARCHAR(500)  NOT NULL,
    file_size       BIGINT        DEFAULT NULL,
    parse_status    VARCHAR(20)   NOT NULL DEFAULT 'pending',
    chunk_count     INT           NOT NULL DEFAULT 0,
    version         INT           NOT NULL DEFAULT 1,
    error_message   TEXT          DEFAULT NULL,
    created_at      DATETIME      NOT NULL,
    updated_at      DATETIME      NOT NULL,
    PRIMARY KEY (id),
    INDEX idx_kb_id (kb_id),
    INDEX idx_tenant_id (tenant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE knowledge_chunk (
    id              VARCHAR(36)   NOT NULL,
    document_id     VARCHAR(36)   NOT NULL,
    kb_id           VARCHAR(36)   NOT NULL,
    tenant_id       VARCHAR(36)   NOT NULL,
    chunk_index     INT           NOT NULL,
    content         TEXT          NOT NULL,
    metadata_json   JSON          DEFAULT NULL,
    vector_id       VARCHAR(100)  DEFAULT NULL,
    created_at      DATETIME      NOT NULL,
    PRIMARY KEY (id),
    INDEX idx_document_id (document_id),
    INDEX idx_kb_id (kb_id),
    INDEX idx_tenant_id (tenant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE execution_trace (
    id              VARCHAR(36)   NOT NULL,
    tenant_id       VARCHAR(36)   NOT NULL,
    session_id      VARCHAR(36)   NOT NULL,
    agent_id        VARCHAR(36)   DEFAULT NULL,
    reply_id        VARCHAR(36)   DEFAULT NULL,
    stage           VARCHAR(30)   NOT NULL,
    event_type      VARCHAR(50)   NOT NULL,
    tool_name       VARCHAR(100)  DEFAULT NULL,
    status          VARCHAR(20)   NOT NULL,
    duration_ms     INT           DEFAULT NULL,
    input_tokens    INT           DEFAULT NULL,
    output_tokens   INT           DEFAULT NULL,
    payload_json    JSON          DEFAULT NULL,
    created_at      DATETIME      NOT NULL,
    PRIMARY KEY (id),
    INDEX idx_tenant_id (tenant_id),
    INDEX idx_session_id (session_id),
    INDEX idx_agent_id (agent_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
