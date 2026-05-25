# AgentScope v2 多租户智能体平台

基于 AgentScope v2 的企业级多租户智能体平台，提供智能对话、知识库、工具管理等功能。

## 项目结构

```
/workspace
├── src/ms3/              # 后端服务
│   ├── api/            # API 路由和主应用
│   ├── auth/           # 认证和权限
│   ├── database/       # 数据库模块
│   ├── models/         # 数据模型
│   ├── common/         # 通用工具
│   └── scripts/        # 脚本
├── web/                # 前端 Vue 3 应用
│   ├── src/
│   │   ├── views/    # 页面组件
│   │   ├── store/    # Pinia 状态管理
│   │   ├── api/      # API 请求
│   │   └── utils/    # 工具函数
│   └── dist/         # 构建产物
├── pyproject.toml      # Python 依赖配置
├── Dockerfile           # Docker 镜像构建
├── docker-compose.yaml  # Docker Compose 编排
└── .env.example        # 环境变量示例
```

## 功能特性

- ✅ 多租户支持
- ✅ 用户认证和权限控制
- ✅ 智能对话（支持 SSE 流式响应）
- ✅ 会话管理
- ✅ 智能体定义
- 🚧 知识库（开发中）
- 🚧 工具管理（开发中）

## 快速开始

### 1. 环境准备

- Python 3.11+
- Docker 和 Docker Compose
- Node.js 18+ (前端开发)

### 2. 启动服务

使用 Docker Compose 启动所有服务：

```bash
# 复制环境变量
cp .env.example .env

# 启动服务
docker-compose up -d
```

### 3. 初始化数据库

在数据库初始化脚本将自动执行。

### 4. 访问应用

- 前端应用: http://localhost:8080
- API 文档: http://localhost:8080/docs

默认账户:
- 用户名: admin
- 密码: admin123

## 开发模式

### 后端开发

```bash
cd /workspace
pip install -e .
python -m src.ms3.api.app
```

### 前端开发

```bash
cd /workspace/web
npm install
npm run dev
```

### 前端构建

```bash
cd /workspace/web
npm install
npm run build
```

## 技术栈

### 后端

- FastAPI: Web 框架
- SQLAlchemy: ORM
- Redis: 缓存和状态存储
- MySQL: 关系型数据库
- AgentScope v2: 智能体框架

### 前端

- Vue 3: 前端框架
- Vite: 构建工具
- Element Plus: UI 组件库
- Pinia: 状态管理
- Vue Router: 路由管理
- Axios: HTTP 请求
