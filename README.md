# qaitest 智测平台

企业级AI测试用例生成系统，通过多智能体协作自动分析需求文档、提取功能点并生成高质量测试用例。

## 功能特性

### 核心功能

#### AI用例生成（核心模块）

- **用例生成**：上传需求文档（本地/飞书/手动输入），AI 自动提取功能点并生成测试用例
  - 支持 PDF、Word、Markdown、飞书云文档等多种格式
  - 多文档批量处理，并行分析提速 83%
  - 实时推送 Agent 推理过程，流式输出
  - 智能评审和定稿，自动优化用例质量

- **需求管理**：管理从需求中提取的功能点
  - 查看功能点详情和关联需求片段
  - 批量选择功能点生成测试用例
  - 支持 RAG 检索关联需求上下文

- **测试用例**：测试用例的全生命周期管理
  - 查看、编辑、删除测试用例
  - 导出为 Excel 或 Markdown 格式
  - 按项目、模块、优先级筛选

#### 其他功能模块

- **AI任务**：统一管理需求分析和用例生成任务，支持任务取消/重试/删除、查看实时进度
- **项目管理**：创建、编辑、删除、查看测试项目
- **版本管理**：项目版本管理、基线管理、版本对比、版本回溯
- **测试计划**：创建测试计划，关联用例，管理执行状态
- **测试报告**：生成测试报告，统计执行结果，支持多格式导出

### 技术亮点

- **多智能体协作**：基于 AutoGen 0.7.5 实现多智能体流水线，四阶段生成流程（生成→评审→定稿→保存）
- **RAG增强**：LlamaIndex 0.14.18 + Milvus 实现智能知识检索，检索关联需求片段辅助用例生成
- **多格式文档解析**：支持 PDF（PyMuPDF）、Word、Markdown、飞书云文档
- **语义分块**：基于 SentenceSplitter 的智能语义分块，提升检索精度
- **实时输出**：WebSocket 实时推送 Agent 推理过程
- **灵活模型配置**：支持 DeepSeek（生成）、Qwen（评审）、Moonshot 等多种模型，可自定义模型
- **现代UI**：Vue 3 + TypeScript + Element Plus + TailwindCSS，响应式设计

## 技术栈

### 后端

- **框架**：FastAPI 0.115.0 (异步模式)
- **数据库**：MySQL 8.0+
- **ORM**：Tortoise ORM 0.22.0 (全异步)
- **向量数据库**：Milvus 2.5.0
- **多智能体框架**：AutoGen 0.7.5 (autogen-agentchat、autogen-core、autogen-ext)
- **RAG框架**：LlamaIndex 0.14.18
- **LLM**：DeepSeek API（需求分析和用例生成）+ Qwen API（用例评审），支持自定义模型
- **嵌入模型**：Qwen text-embedding-v3 (1024维)
- **文档解析**：PyMuPDF 1.25.0 + docx2txt

### 前端

- **框架**：Vue 3 (Composition API)
- **构建工具**：Vite 5.x
- **语言**：TypeScript 5.x
- **UI组件库**：Element Plus + TailwindCSS
- **状态管理**：Pinia
- **路由**：Vue Router 4
- **图表**：ECharts
- **工具库**：axios、xlsx、marked、dompurify、lucide-vue-next

## 快速开始

### 1. 环境要求

- Python 3.11+
- Node.js 18+
- MySQL 8.0+
- Milvus 2.x（或使用远程Milvus）

### 2. 克隆项目

```bash
git clone <repository-url>
cd qaitest
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑.env文件，配置数据库、Milvus、API密钥等
```

### 4. 创建数据库

```bash
# 本地数据库
mysql -u root -p

# 远程数据库（例如：mysql -h 192.168.1.100 -u root -p）
mysql -h <数据库地址> -u root -p

# 创建数据库
CREATE DATABASE qaitest CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 5. 启动 Milvus 向量数据库

```bash
# 方式一：Docker 启动（推荐，每次重启后需重新执行）
docker-compose -f docker-compose-milvus.yml up -d

# 验证 Milvus 运行状态
docker ps --filter "name=milvus"
```

> **注意**：Milvus 是 Docker 部署的，每次重启电脑后需要重新执行上述命令启动 Milvus。

### 6. 后端启动

```bash
cd backend
pip install -r requirements.txt
python init_db.py  # 首次运行，初始化数据表
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. 前端启动

```bash
cd frontend
npm install
npm run dev
```

### 7. 访问应用

- 前端：<http://localhost:5173>
- 后端API文档：<http://localhost:8000/docs>

***

## 生产环境部署（Docker方式）

> 推荐使用Docker部署，无需安装Python、Node.js等运行环境。

### 1. 安装Docker

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# macOS
brew install --cask docker
```

### 2. 克隆项目

```bash
git clone <repository-url>
cd qaitest
```

### 3. 配置环境变量（唯一需要修改的文件）

```bash
cp .env.example .env
```

编辑 `.env` 文件，根据文件内注释配置数据库、API密钥、域名等信息。

### 4. 创建数据库

确保MySQL数据库已创建：

```bash
# 本地数据库
mysql -u root -p

# 远程数据库（例如：mysql -h 192.168.1.100 -u root -p）
mysql -h <数据库地址> -u root -p

# 创建数据库
CREATE DATABASE qaitest CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

> 如果使用远程数据库，请联系数据库管理员创建数据库。

### 5. 一键启动

**无域名/IP访问（推适合内部部署）：**

```bash
docker-compose --profile dev up -d
```

**有域名（自动SSL，适合对外服务）：**

```bash
docker-compose --profile prod up -d
```

### 6. 初始化数据表（首次部署）

> 后端容器启动后，执行此步骤创建数据库表。

```bash
docker exec -it qaitest-backend python init_db.py
```

### 7. 访问应用

| 部署方式     | 前端地址                      | 后端API                          | 适用场景 |
| -------- | ------------------------- | ------------------------------ | ---- |
| IP访问（推荐） | `http://your-ip`          | `http://your-ip/docs`          | 内部部署 |
| 有域名      | `https://your-domain.com` | `https://your-domain.com/docs` | 对外服务 |

### 8. 常用命令

```bash
# 停止服务
docker-compose --profile prod down
# 或
docker-compose --profile dev down

# 重启服务
docker-compose --profile prod restart
# 或
docker-compose --profile dev restart

# 查看日志
docker-compose logs -f
```

## 生产环境部署（传统方式）

> 需要自行安装Python、Node.js、Nginx等运行环境。

### 环境要求

- Python 3.11+
- Node.js 18+
- Nginx（用于前端静态文件部署和反向代理）
- MySQL 8.0+（或使用远程数据库）
- Milvus 2.x（或使用远程Milvus）

### 1. 后端部署

**步骤1：克隆项目**

```bash
git clone <repository-url>
cd qaitest
```

**步骤2：配置环境变量**

```bash
cp .env.example .env
# 编辑.env文件，配置生产环境的数据库、Milvus、API密钥等
```

**步骤3：安装依赖**

```bash
cd backend
pip install -r requirements.txt
```

**步骤4：创建MySQL数据库**（首次部署）

```bash
mysql -u root -p
CREATE DATABASE qaitest CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

**步骤5：初始化数据表**（首次部署）

```bash
python init_db.py
```

**步骤6：使用Gunicorn启动后端服务**

```bash
# 安装Gunicorn（如未安装）
pip install gunicorn

# 启动服务（4个工作进程）
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

或使用Systemd管理服务：

```bash
# 创建服务文件 /etc/systemd/system/qaitest.service
[Unit]
Description=qaitest智测平台
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/qaitest/backend
ExecStart=/path/to/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target

# 启动服务
sudo systemctl daemon-reload
sudo systemctl start qaitest
sudo systemctl enable qaitest
```

### 2. 前端部署

**步骤1：配置生产环境API地址**

编辑 `frontend/src/api/index.ts`：

```typescript
baseURL: 'https://your-domain.com/api'
```

**步骤2：构建生产版本**

```bash
cd frontend
npm install
npm run build
```

**步骤3：使用Nginx部署静态文件**

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /path/to/qaitest/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # 后端API代理
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket代理
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 环境变量配置

> 详细配置请参考 `.env.example` 文件，以下为主要配置项说明。

### 后端环境变量 (.env)

```env
# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=qaitest

# Milvus配置
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_COLLECTION=qaitest_knowledge

# DeepSeek API (用例生成)
DEEPSEEK_API_KEY=your_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat

# Moonshot API (可选)
MOONSHOT_API_KEY=your_api_key
MOONSHOT_BASE_URL=https://api.moonshot.cn/v1
MOONSHOT_MODEL=moonshot-v1-32k

# DashScope API (Qwen嵌入模型 + 用例评审)
DASHSCOPE_API_KEY=your_api_key
QWEN_MODEL=qwen-plus

# 模型选择配置
GENERATE_MODEL_PROVIDER=deepseek    # 生成模型：deepseek/qwen/moonshot
REVIEW_MODEL_PROVIDER=qwen          # 评审模型：qwen/deepseek/moonshot

# LlamaIndex RAG配置
LLAMAINDEX_CHUNK_SIZE=500
LLAMAINDEX_CHUNK_OVERLAP=100
LLAMAINDEX_ENABLE_RERANKER=false
LLAMAINDEX_RERANKER_MODEL=BAAI/bge-reranker-base
LLAMAINDEX_EMBED_BATCH_SIZE=10

# 飞书配置（可选）
FEISHU_APP_ID=your_app_id
FEISHU_APP_SECRET=your_app_secret

# Docker部署配置
# 有域名时填写，用于自动申请SSL证书
# 无域名时留空即可（如：DOMAIN= 和 SSL_EMAIL=），使用IP访问
DOMAIN=your-domain.com
SSL_EMAIL=your-email@example.com

# 应用配置
APP_ENV=development
APP_DEBUG=true
APP_PORT=8000
```

## API文档

启动后端服务后，访问以下地址查看API文档：

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>

## 目录结构

```
qaitest/
├── backend/                          # 后端代码
│   ├── app/
│   │   ├── agents/                  # 多智能体相关
│   │   │   ├── messages.py          # 消息定义
│   │   │   ├── requirement_agents.py # 需求分析Agent流水线
│   │   │   ├── testcase_agents.py   # 用例生成Agent流水线
│   │   │   └── runtime.py           # Agent运行时工具（模型客户端管理）
│   │   ├── api/                     # API路由
│   │   │   ├── requirements.py      # 需求管理（含多文档并行处理）
│   │   │   ├── testcases.py         # 测试用例管理
│   │   │   ├── projects.py          # 项目管理
│   │   │   ├── versions.py          # 版本管理
│   │   │   ├── testplans.py         # 测试计划
│   │   │   ├── testreports.py       # 测试报告
│   │   │   ├── ai_tasks.py          # AI任务记录（旧版）
│   │   │   ├── ai_tasks_unified.py  # 统一AI任务管理API
│   │   │   ├── custom_model.py      # 自定义模型管理
│   │   │   ├── rag.py               # RAG索引管理
│   │   │   └── websocket.py         # WebSocket实时通信
│   │   ├── models/                  # 数据模型
│   │   │   ├── project.py           # 项目模型
│   │   │   ├── requirement.py       # 功能点模型
│   │   │   ├── testcase.py          # 测试用例模型
│   │   │   ├── testplan.py          # 测试计划模型
│   │   │   ├── testreport.py        # 测试报告模型
│   │   │   ├── version.py           # 版本模型
│   │   │   ├── task.py              # AI任务模型
│   │   │   └── custom_model.py      # 自定义模型配置
│   │   ├── schemas/                 # Pydantic Schema
│   │   ├── services/                # 业务服务
│   │   ├── rag/                     # RAG相关（LlamaIndex 0.14.18）
│   │   │   ├── __init__.py          # 索引管理器入口
│   │   │   ├── llamaindex_manager.py # LlamaIndex索引管理器
│   │   │   ├── llama_embeddings.py  # Qwen嵌入模型适配器
│   │   │   ├── readers/             # 文档解析器
│   │   │   │   ├── __init__.py      # PDF/Word/Markdown通用解析器
│   │   │   │   └── feishu_reader.py # 飞书文档读取器
│   │   │   └── retrievers/          # 检索器
│   │   │       └── __init__.py      # 混合检索、查询增强、结果处理
│   │   ├── utils/                   # 工具函数
│   │   └── config.py                # 配置管理
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                         # 前端代码
│   ├── src/
│   │   ├── api/                     # API调用
│   │   │   ├── index.ts             # Axios实例配置
│   │   │   ├── project.ts           # 项目API
│   │   │   ├── requirement.ts       # 需求/功能点API
│   │   │   ├── testcase.ts          # 测试用例API
│   │   │   ├── testplan.ts          # 测试计划API
│   │   │   ├── testreport.ts        # 测试报告API
│   │   │   ├── version.ts           # 版本API
│   │   │   ├── aiTasks.ts           # AI任务API
│   │   │   ├── rag.ts               # RAG API
│   │   │   ├── websocket.ts         # WebSocket服务
│   │   │   ├── modelConfig.ts       # 模型配置API
│   │   │   └── customModel.ts       # 自定义模型API
│   │   ├── components/              # 通用组件
│   │   │   ├── Layout.vue           # 主布局
│   │   │   ├── ModelSelector.vue    # AI模型选择器
│   │   │   └── detail/              # 详情页组件
│   │   ├── stores/                  # Pinia状态管理
│   │   ├── types/                   # TypeScript类型
│   │   ├── views/                   # 页面
│   │   │   ├── AICaseGeneration/    # AI用例生成模块
│   │   │   │   ├── index.vue        # 模块入口
│   │   │   │   ├── Generate.vue     # 需求分析（支持多文档/飞书）
│   │   │   │   ├── FunctionPoints.vue # 功能点管理
│   │   │   │   └── TestCases.vue    # 测试用例列表
│   │   │   ├── AITasks/             # AI任务管理
│   │   │   │   ├── TaskListPage.vue # 任务列表
│   │   │   │   └── TaskDetailPage.vue # 任务详情
│   │   │   ├── ProjectList.vue      # 项目管理
│   │   │   ├── TestPlanList.vue     # 测试计划列表
│   │   │   ├── TestPlanDetail.vue   # 测试计划详情
│   │   │   ├── TestReportList.vue   # 测试报告列表
│   │   │   ├── TestReportDetail.vue # 测试报告详情
│   │   │   ├── VersionList.vue      # 版本管理
│   │   │   ├── VersionDetail.vue    # 版本详情
│   │   │   └── VersionCompare.vue   # 版本对比
│   │   ├── router/                  # 路由配置
│   │   └── main.ts                  # 入口文件
│   ├── package.json
│   └── vite.config.ts
│
└── README.md
```

## 核心模块说明

### 1. RAG架构（LlamaIndex 0.14.18）

基于 LlamaIndex 0.14.18 的智能文档检索系统：

```
┌─────────────────────────────────────────┐
│          AutoGen 0.7.5 Agent层          │
│  (requirement_agents / testcase_agents) │
└─────────────────┬───────────────────────┘
                  │ 调用 get_index_manager()
┌─────────────────▼───────────────────────┐
│      LlamaIndexIndexManager（核心）      │
│  ┌────────────────────────────────────┐ │
│  │ QwenEmbeddingModel (1024维)        │ │
│  ├────────────────────────────────────┤ │
│  │ Document Readers（多格式支持）      │ │
│  │  - PyMuPDFReader (PDF表格提取)     │ │
│  │  - DocxReader (Word样式保留)       │ │
│  │  - MarkdownReader (代码块/表格)    │ │
│  ├────────────────────────────────────┤ │
│  │ SentenceSplitter（语义分块）        │ │
│  │  - chunk_size: 500                 │ │
│  │  - chunk_overlap: 100              │ │
│  ├────────────────────────────────────┤ │
│  │ Query Engine（检索引擎）            │ │
│  │  - 向量检索 (Milvus)               │ │
│  │  - BM25关键词检索（可选）           │ │
│  │  - BGE重排序（可选）                │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│            Milvus 向量存储               │
│  (collection: project_{id}_v{version})  │
└─────────────────────────────────────────┘
```

**关键特性**：

- **智能分块**：SentenceSplitter 基于语义边界分块，避免截断句子
- **多格式支持**：PDF（表格提取）、Word（样式保留）、Markdown（代码块识别）
- **混合检索**：向量检索 + BM25关键词检索，提升召回率
- **查询增强**：自动提取关键词，扩展查询语义
- **重排序**：可选的 BGE Reranker 提升排序精度
- **向后兼容**：支持通过配置切换新旧实现

### 2. 需求分析流水线（AutoGen 0.7.5）

需求分析采用三阶段 Agent 流水线，支持多文档并行处理：

```
前端上传需求文档（本地文件/飞书文档/手动输入）
  ↓
/analyze 或 /analyze-multiple API
  ↓
RequirementAcquireAgent (文档解析 + RAG索引)
  ↓
RequirementAnalysisAgent (需求分析，RAG增强，DeepSeek)
  ↓
RequirementOutputAgent (JSON格式化 + 数据库保存)
  ↓
RequirementCompleteMessage (任务完成通知)
```

> **注意**：需求评审阶段已移除（AI评审价值有限，重点在用例评审）

**性能提升**：

- 单文档：10分钟 → 2-3分钟
- 多文档（3个）：30分钟 → 5分钟（提速83%）
- 多文档（5个）：50分钟 → 8分钟

### 3. 用例生成流水线（AutoGen 0.7.5）

用例生成采用四阶段 Agent 流水线：

```
TestCaseInputMessage (选择功能点)
  ↓
TestCaseGenerateAgent (DeepSeek/Qwen生成用例，RAG增强)
  ↓
TestCaseReviewAgent (Qwen评审用例质量)
  ↓
TestCaseFinalizeAgent (Qwen定稿用例格式)
  ↓
TestCaseInDatabaseAgent (保存到数据库)
```

**特性**：

- **流式推理输出**：实时推送 Agent 思考过程
- **智能评审**：自动检测用例质量问题
- **双模型协作**：DeepSeek 生成 + Qwen 评审（可配置）
- **RAG 增强**：检索相关需求片段辅助生成

### 4. 版本管理

版本管理采用以下关联策略：

- **测试计划**是版本关联的主要入口（必选关联版本）
- **测试用例**独立设计，不强制绑定版本
- **功能点**可选择性关联版本（用于需求变更追踪）
- **测试报告**继承测试计划的版本关联
- **RAG索引**支持版本隔离（project\_{id}\_v{version}）

## 开发指南

### 代码规范

- 后端：遵循PEP 8规范，使用Black格式化
- 前端：遵循Vue 3 Composition API风格，使用ESLint + Prettier

### 提交规范

使用语义化提交信息：

- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建/工具相关

## 已完成的优化

### ✅ 阶段一：Agent代码优化（已完成）

- 使用 AutoGen 0.7.5 标准 API（RoutedAgent + type\_subscription）
- 实现流式推理输出（StreamBuffer + WebSocket）
- 优化 Agent 协作模式（AssistantAgent + ListMemory）
- 移除需求评审阶段（聚焦用例评审）

### ✅ 阶段二：文档级并行优化（已完成）

- 前端支持多文件上传和批量处理
- 后端使用 asyncio.gather() 并行处理多个文档
- 实时推送每个文档的处理进度
- 性能提升：多文档处理提速83%

### ✅ 阶段三：LlamaIndex 0.14.18 升级（已完成）

- 升级 LlamaIndex 到 0.14.18
- 创建 LlamaIndexIndexManager 核心类
- 实现增强文档解析器（PDF/Word/Markdown）
- 集成 Qwen text-embedding-v3（1024维）
- 支持语义分块（SentenceSplitter）
- 支持混合检索和重排序策略
- 保持向后兼容，支持配置切换

### ✅ 阶段四：飞书文档与模型管理（已完成）

- 实现飞书文档读取器（FeishuReader）
- 支持飞书云文档直接导入需求
- 实现自定义模型配置功能
- 支持动态切换生成/评审模型
- 统一AI任务管理API
- 前端模型选择器组件

## 待优化项

- [ ] 启用 BM25 混合检索（需安装 llama-index-retrievers-bm25）
- [ ] 添加 BGE Reranker 提升检索精度
- [ ] 支持更多文档格式（HTML、Excel）
- [ ] 优化嵌入向量缓存策略
- [ ] 完善版本回溯的数据恢复逻辑
- [ ] 添加用户登录和权限管理
- [ ] 添加测试用例模板管理
- [ ] 添加测试执行记录管理
- [ ] 优化大规模文档索引性能
- [ ] AI评审自动补充功能点

## 待实现功能

### AI评审自动补充功能点

**功能描述**：
当前AI评审仅对提取的功能点进行评估并给出建议，但不会自动根据评审意见补充遗漏的功能点。

**当前行为**：
```
1. 生成功能点 → 保存到数据库 ✅
2. 评审（一句话建议）→ 显示给用户
3. 流程结束
```

**目标行为**：
```
1. 生成功能点
2. 评审（识别遗漏的功能点）
3. 根据评审意见 → 自动生成补充的功能点
4. 合并后保存到数据库
```

**实现思路**：
- 在评审阶段，让AI识别遗漏的功能点并输出JSON格式
- 新增补充功能点生成环节
- 合并原功能点与补充功能点，去重后统一保存

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交Issue或Pull Request。
