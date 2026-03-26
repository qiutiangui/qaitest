# qaitest 智测平台

企业级 AI 测试用例生成系统，通过多智能体协作自动分析需求文档、提取功能点并生成高质量测试用例。

## 功能特性

- **AI 用例生成**：上传需求文档（PDF/Word/Markdown），AI 自动提取功能点并生成测试用例
- **智能评审**：四阶段流水线（生成 → 评审 → 定稿 → 保存），保障用例质量
- **RAG 增强**：基于 Milvus + LlamaIndex 实现智能知识检索
- **实时输出**：WebSocket 推送 Agent 推理过程
- **多模型支持**：DeepSeek（生成）、Qwen（评审），支持自定义模型

## 技术栈

| 角色 | 技术 |
|------|------|
| 后端 | FastAPI + Tortoise ORM + MySQL |
| 前端 | Vue 3 + TypeScript + Element Plus |
| AI | AutoGen 0.7.5 + DeepSeek/Qwen API |
| 向量库 | Milvus 2.5 + LlamaIndex 0.14.18 |
| 嵌入 | Qwen text-embedding-v3 (1024 维) |

## Docker 部署

### 环境要求

| 软件 | 版本 | 说明 |
|------|------|------|
| Docker | 24.0+ | [安装指南](https://docs.docker.com/get-docker/) |
| Docker Compose | 2.20+ | 通常随 Docker 一起安装 |
| MySQL | 8.0+ | 本地或远程均可 |

### 部署模式

| 模式 | 命令 | 说明 |
|------|------|------|
| 基础 | `docker compose up -d` | 仅前后端（无 Nginx），适合本地开发 |
| 生产 | `docker compose --profile prod up -d` | 前后端 + Nginx + HTTPS |
| 完整 | `docker compose --profile milvus up -d` | 包含本地 Milvus 向量库 |
| 全量 | `docker compose --profile prod --profile milvus up -d` | 生产 + Milvus |

### 部署步骤

#### 1. 克隆项目

```bash
git clone <repository-url>
cd qaitest
```

#### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# 数据库（本地或远程）
DB_HOST=mysql        # 容器内访问用 mysql，宿主机访问用 localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=qaitest

# Milvus（使用本地 Milvus 时填 milvus，远程时填 IP）
MILVUS_HOST=milvus
MILVUS_PORT=19530

# DeepSeek API（用例生成）
DEEPSEEK_API_KEY=your_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# DashScope API（嵌入 + 评审）
DASHSCOPE_API_KEY=your_api_key
```

#### 3. 创建数据库

```bash
# 方式一：使用 Docker 启动 MySQL
docker run -d --name mysql \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=your_password \
  -e MYSQL_DATABASE=qaitest \
  mysql:8.0 \
  --character-set-server=utf8mb4 \
  --collation-server=utf8mb4_unicode_ci

# 方式二：连接已有 MySQL
mysql -h <host> -u root -p -e "CREATE DATABASE qaitest CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

#### 4. 启动服务

```bash
# 本地开发（无需 Nginx）
docker compose up -d backend frontend

# 生产部署（含 Nginx）
docker compose --profile prod up -d

# 完整部署（包含 Milvus）
docker compose --profile milvus up -d

# 生产 + Milvus
docker compose --profile prod --profile milvus up -d
```

#### 5. 配置域名（可选）

部署生产环境时，配置域名：

```bash
# 1. 编辑 nginx.conf，替换 server_name
sed -i 's/server_name localhost;/server_name your-domain.com;/g' nginx.conf

# 2. 获取 SSL 证书（Let's Encrypt）
mkdir -p ssl
certbot --nginx -d your-domain.com -d api.your-domain.com

# 3. 复制证书到 ssl 目录
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/
cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/

# 4. 重启 Nginx
docker compose restart nginx
```

#### 6. 初始化数据库

```bash
docker exec qaitest-backend python init_db.py
```

#### 7. 验证服务

```bash
# 查看容器状态
docker compose ps

# 查看日志
docker compose logs -f

# 检查端口
curl http://localhost            # 前端
curl http://localhost/docs        # API 文档
```

### 服务地址

| 部署模式 | 前端 | 后端 API | 说明 |
|----------|------|----------|------|
| 本地开发 | http://localhost:5173 | http://localhost:8000 | 直接访问 |
| 生产部署 | http://localhost | http://localhost/docs | Nginx 代理 |
| 有域名 | https://your-domain.com | https://your-domain.com/docs | HTTPS 访问 |

### 常用命令

```bash
# 停止服务
docker compose down

# 停止并删除数据卷（慎用）
docker compose down -v

# 重启服务
docker compose restart

# 重新构建镜像
docker compose build --no-cache
docker compose up -d

# 进入容器调试
docker exec -it qaitest-backend sh
docker exec -it qaitest-nginx sh

# 查看资源使用
docker stats
```

### 故障排查

```bash
# 1. 检查容器是否运行
docker compose ps

# 2. 查看错误日志
docker compose logs backend
docker compose logs frontend
docker compose logs nginx

# 3. 检查端口占用
lsof -i :80
lsof -i :3306
lsof -i :19530

# 4. 重置 Milvus（完整部署）
docker compose down -v milvus etcd minio
docker compose --profile milvus up -d
```

### 数据持久化

| 数据 | 位置 | 说明 |
|------|------|------|
| MySQL 数据 | 外部 MySQL 或 Docker 卷 | 需定期备份 |
| Milvus 数据 | Docker 卷 `milvus_data` | 仅完整部署 |
| 容器日志 | `docker compose logs` | 临时存储 |

## 本地开发

### 后端

```bash
cd backend
pip install -r requirements.txt
python init_db.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

## 目录结构

```
qaitest/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── agents/         # AutoGen 智能体
│   │   ├── api/            # API 路由
│   │   ├── models/          # 数据模型
│   │   ├── rag/             # LlamaIndex RAG
│   │   └── services/        # 业务服务
│   └── requirements.txt
│
├── frontend/               # Vue 3 前端
│   ├── src/
│   │   ├── api/            # API 调用
│   │   ├── components/      # 通用组件
│   │   ├── stores/          # Pinia 状态
│   │   └── views/           # 页面
│   └── package.json
│
├── docker-compose.yml      # Docker 部署配置（含 Milvus profile）
├── nginx.conf              # Nginx 反向代理
├── ssl/                    # SSL 证书目录（部署时创建）
├── .dockerignore           # Docker 构建忽略文件
└── .env.example            # 环境变量示例
```

## 环境变量

详细配置参考 `.env.example`，主要配置项：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DB_HOST` | 数据库地址（容器内用 `mysql`，宿主机用 `localhost`） | mysql |
| `DB_PORT` | 数据库端口 | 3306 |
| `DB_USER` | 数据库用户 | root |
| `DB_PASSWORD` | 数据库密码 | - |
| `DB_NAME` | 数据库名 | qaitest |
| `MILVUS_HOST` | Milvus 地址（容器内用 `milvus`，远程用 IP） | milvus |
| `MILVUS_PORT` | Milvus 端口 | 19530 |
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | - |
| `DASHSCOPE_API_KEY` | 阿里云 API 密钥 | - |

## 数据持久化

| 数据 | 位置 | 说明 |
|------|------|------|
| MySQL | 外部 MySQL 或 Docker 卷 | 需定期备份 |
| Milvus | Docker 卷 `milvus_data` | 仅完整部署 |
| SSL 证书 | `./ssl/` 目录 | 需定期续期 |
| 容器日志 | `docker compose logs` | 临时存储 |

## 许可证

MIT License
