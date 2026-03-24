---
name: qaitest智测平台开发计划(v6)
overview: 企业级AI测试用例生成系统，含版本管理功能，实现需求分析→用例生成→测试计划→测试报告的全流程智能化。
design:
  architecture:
    framework: vue
  styleKeywords:
    - Modern
    - Enterprise
    - Professional
    - Blue Theme
    - Clean Layout
  fontSystem:
    fontFamily: system-ui
    heading:
      size: 24px
      weight: 600
    subheading:
      size: 18px
      weight: 500
    body:
      size: 14px
      weight: 400
  colorSystem:
    primary:
      - "#409EFF"
      - "#66B1FF"
      - "#79BBFF"
    background:
      - "#FFFFFF"
      - "#F5F7FA"
      - "#001529"
    text:
      - "#303133"
      - "#606266"
      - "#909399"
    functional:
      - "#67C23A"
      - "#F56C6C"
      - "#E6A23C"
      - "#409EFF"
todos:
  - id: setup-backend
    content: 搭建后端项目结构，配置FastAPI、Tortoise ORM、Loguru，创建数据库表结构（含版本管理表）
    status: completed
  - id: setup-frontend
    content: 搭建前端项目结构，配置Vue3、Vite、TypeScript、Element Plus、Pinia、Vue Router
    status: completed
  - id: implement-projects
    content: 实现项目管理模块（前后端CRUD）
    status: completed
    dependencies:
      - setup-backend
      - setup-frontend
  - id: implement-versions
    content: 实现版本管理模块（版本CRUD、基线管理、快照功能）
    status: completed
    dependencies:
      - implement-projects
  - id: implement-rag
    content: 实现LlamaIndex RAG模块：qwen3-embedding配置、文档加载、Milvus向量索引
    status: completed
    dependencies:
      - setup-backend
  - id: implement-requirement-agents
    content: 实现需求分析多智能体流水线（RequirementAcquireAgent -> RequirementAnalysisAgent -> RequirementOutputAgent）
    status: completed
    dependencies:
      - implement-rag
  - id: implement-websocket
    content: 实现WebSocket实时通信，将Agent推理过程实时推送到前端Terminal组件
    status: completed
    dependencies:
      - setup-backend
      - setup-frontend
  - id: implement-requirement-analysis
    content: 实现需求分析界面（文档上传、实时输出、功能点提取、版本关联）
    status: completed
    dependencies:
      - implement-requirement-agents
      - implement-websocket
  - id: implement-requirement-management
    content: 实现功能点管理模块（列表展示、编辑、删除、版本关联）
    status: completed
    dependencies:
      - implement-requirement-analysis
  - id: implement-testcase-agents
    content: 实现用例生成多智能体流水线（TestCaseGenerateAgent -> TestCaseReviewAgent -> TestCaseFinalizeAgent -> TestCaseInDatabaseAgent）
    status: completed
    dependencies:
      - implement-requirement-agents
  - id: implement-testcase-generation
    content: 实现用例生成界面（功能点选择、实时输出、版本关联）
    status: completed
    dependencies:
      - implement-testcase-agents
      - implement-websocket
  - id: implement-testcase-management
    content: 实现用例管理模块（列表展示、详情查看、导出Excel/Markdown、版本关联）
    status: completed
    dependencies:
      - implement-testcase-generation
  - id: implement-testplan-management
    content: 实现测试计划管理模块（计划CRUD、用例关联、执行跟踪、统计展示、版本关联）
    status: completed
    dependencies:
      - implement-testcase-management
  - id: implement-testreport-management
    content: 实现测试报告管理模块（报告生成、多格式导出、可视化图表、版本关联）
    status: completed
    dependencies:
      - implement-testplan-management
  - id: implement-version-compare
    content: 实现版本对比和版本回溯功能
    status: completed
    dependencies:
      - implement-versions
      - implement-testreport-management
  - id: integration-test
    content: 系统集成测试，优化用户体验，编写部署文档
    status: completed
    dependencies:
      - implement-version-compare
---

## 产品概述

「qaitest 智测平台」是一个企业级的AI测试用例生成系统，通过多智能体协作自动分析需求文档、提取功能点并生成高质量测试用例，并提供测试计划管理、执行跟踪、测试报告生成和版本管理功能，实现从需求到报告的全流程智能化。

## 核心功能模块

### 1. 项目管理

- 创建、编辑、删除、查看测试项目
- 项目列表展示与搜索
- 项目详情页面

### 2. 需求分析（核心界面）

- 项目选择下拉框
- 需求文档上传（支持txt/pdf/md格式）
- 需求描述文本输入
- "开始分析"按钮触发Agent流水线
- 实时显示区域（类似Terminal/对话框）：通过WebSocket实时展示AutoGen智能体的推理、对话、执行过程
- 自动提取功能点并存储

### 3. 功能点管理

- 展示从需求中提取的功能点列表
- 支持编辑、删除功能点
- 按项目、类别、关键词筛选

### 4. 用例生成

- 选择功能点触发用例生成
- 基于RAG检索相关测试知识和最佳实践
- 自动生成测试用例
- 智能评审环节：自动评审用例质量（覆盖率、可执行性、逻辑正确性）
- 根据评审报告优化用例
- 实时显示Agent生成和评审过程

### 5. 用例管理

- 测试用例列表展示（表格形式）
- 用例详情查看（步骤、预期结果等）
- 支持导出为Excel和Markdown格式

### 6. 测试计划管理

- 创建、编辑、删除、查看测试计划
- 测试计划列表展示与搜索
- 批量添加测试用例到计划
- 测试计划状态管理（未开始/进行中/已完成/已归档）
- 测试计划执行进度跟踪
- 测试用例执行状态更新（通过/失败/阻塞/未执行）
- 执行情况统计和可视化展示

### 7. 测试报告管理

- 基于测试计划自动生成测试报告
- 测试报告包含：执行概况、统计图表、用例详情、缺陷分析
- 支持多种格式导出（PDF/HTML/Word）
- 测试报告模板管理
- 可视化图表展示（饼图、柱状图、趋势图）

### 8. 版本管理（新增核心功能）

- **项目版本管理**：创建、编辑、查看项目版本（v1.0.0, v1.1.0, v2.0.0等）
- **版本基线管理**：保存每个版本的需求基线、用例基线、计划基线、报告基线
- **版本对比功能**：对比任意两个版本的差异（需求变更、用例增删、执行结果对比）
- **版本回溯功能**：恢复到历史版本的完整状态
- **版本快照**：保存版本完整状态快照（包含所有关联数据）
- **版本状态流转**：开发中→测试中→已发布→已归档
- **版本关联策略**：通过测试计划关联版本（用例独立设计，执行时通过计划绑定版本）
- **版本发布说明**：自动生成版本变更日志和发布说明

## 技术栈

### 后端技术栈

- **框架**: FastAPI (异步模式)
- **数据库**: MySQL 8.0+
- **ORM**: Tortoise ORM (全异步)
- **数据验证**: Pydantic v2
- **日志**: Loguru
- **向量数据库**: Milvus 2.x
- **RAG框架**: LlamaIndex (llama-index-core, llama-index-vector-stores-milvus)
- **嵌入模型**: qwen3-embedding (通过DashScope API)
- **多智能体框架**: AutoGen 0.7.5 (autogen-agentchat, autogen-core, autogen-ext)
- **LLM**: DeepSeek API
- **实时通信**: WebSocket (FastAPI原生支持)
- **报告生成**: WeasyPrint (PDF), Jinja2 (模板引擎), python-docx (Word)

### 前端技术栈

- **框架**: Vue 3 (Composition API, `<script setup>`语法)
- **构建工具**: Vite 5.x
- **语言**: TypeScript 5.x
- **UI组件库**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router 4
- **HTTP客户端**: Axios
- **实时通信**: 原生WebSocket API
- **图表库**: ECharts / vue-echarts

## 系统架构设计

### 数据库设计

#### 核心表结构

```sql
-- 项目表
CREATE TABLE projects (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT '活跃',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 项目版本表（新增）
CREATE TABLE project_versions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    project_id INT NOT NULL,
    version_number VARCHAR(20) NOT NULL,           -- 版本号：v1.0.0
    version_name VARCHAR(200),                      -- 版本名称
    description TEXT,                               -- 版本描述
    status VARCHAR(20) DEFAULT '开发中',            -- 开发中/测试中/已发布/已归档
    release_notes TEXT,                             -- 发布说明
    is_baseline BOOLEAN DEFAULT FALSE,              -- 是否为基线版本
    created_by VARCHAR(50),
    released_at DATETIME,                           -- 发布时间
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_project (project_id),
    INDEX idx_status (status),
    UNIQUE KEY uk_project_version (project_id, version_number),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- 版本快照表（新增）
CREATE TABLE version_snapshots (
    id INT PRIMARY KEY AUTO_INCREMENT,
    version_id INT NOT NULL,
    snapshot_type VARCHAR(50) NOT NULL,             -- 需求快照/用例快照/计划快照/报告快照
    snapshot_data JSON NOT NULL,                    -- 快照数据（JSON格式）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_version (version_id),
    INDEX idx_type (snapshot_type),
    FOREIGN KEY (version_id) REFERENCES project_versions(id) ON DELETE CASCADE
);

-- 功能点表
CREATE TABLE requirements (
    id INT PRIMARY KEY AUTO_INCREMENT,
    project_id INT NOT NULL,
    version_id INT,                                 -- 关联版本（可选，用于版本对比）
    name VARCHAR(500) NOT NULL,
    description TEXT,
    category VARCHAR(50),
    module VARCHAR(100),
    priority VARCHAR(10),
    acceptance_criteria TEXT,
    keywords VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_project (project_id),
    INDEX idx_version (version_id),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (version_id) REFERENCES project_versions(id) ON DELETE SET NULL
);

-- 测试用例表
CREATE TABLE test_cases (
    id INT PRIMARY KEY AUTO_INCREMENT,
    project_id INT NOT NULL,
    requirement_id INT,
    version_id INT,                                 -- 关联版本（可选，不强制绑定，通过测试计划关联版本）
    title VARCHAR(500) NOT NULL,
    description TEXT,
    priority VARCHAR(20),
    status VARCHAR(20) DEFAULT '未开始',
    test_type VARCHAR(50),
    preconditions TEXT,
    postconditions TEXT,
    creator VARCHAR(50) DEFAULT 'AI',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_project (project_id),
    INDEX idx_version (version_id),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (version_id) REFERENCES project_versions(id) ON DELETE SET NULL
);

-- 测试步骤表
CREATE TABLE test_steps (
    id INT PRIMARY KEY AUTO_INCREMENT,
    test_case_id INT NOT NULL,
    step_number INT NOT NULL,
    description TEXT NOT NULL,
    expected_result TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_testcase (test_case_id),
    FOREIGN KEY (test_case_id) REFERENCES test_cases(id) ON DELETE CASCADE
);

-- 测试计划表（版本关联的主要入口）
CREATE TABLE test_plans (
    id INT PRIMARY KEY AUTO_INCREMENT,
    project_id INT NOT NULL,
    version_id INT,                                 -- 关联版本（核心关联点，计划绑定版本，用例通过计划间接关联）
    name VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT '未开始',
    start_time DATETIME,
    end_time DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_project (project_id),
    INDEX idx_version (version_id),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (version_id) REFERENCES project_versions(id) ON DELETE SET NULL
);

-- 测试计划用例关联表
CREATE TABLE test_plan_cases (
    id INT PRIMARY KEY AUTO_INCREMENT,
    test_plan_id INT NOT NULL,
    test_case_id INT NOT NULL,
    execution_status VARCHAR(20) DEFAULT '未执行',
    executed_at DATETIME,
    executor VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_plan (test_plan_id),
    INDEX idx_case (test_case_id),
    FOREIGN KEY (test_plan_id) REFERENCES test_plans(id) ON DELETE CASCADE,
    FOREIGN KEY (test_case_id) REFERENCES test_cases(id) ON DELETE CASCADE
);

-- 测试报告表
CREATE TABLE test_reports (
    id INT PRIMARY KEY AUTO_INCREMENT,
    test_plan_id INT NOT NULL,
    project_id INT NOT NULL,
    version_id INT,                                 -- 关联版本（新增）
    title VARCHAR(200) NOT NULL,
    report_type VARCHAR(20) DEFAULT '执行报告',
    summary TEXT,
    total_cases INT DEFAULT 0,
    passed_cases INT DEFAULT 0,
    failed_cases INT DEFAULT 0,
    blocked_cases INT DEFAULT 0,
    not_executed_cases INT DEFAULT 0,
    pass_rate DECIMAL(5,2) DEFAULT 0.00,
    start_time DATETIME,
    end_time DATETIME,
    status VARCHAR(20) DEFAULT '草稿',
    created_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_plan (test_plan_id),
    INDEX idx_project (project_id),
    INDEX idx_version (version_id),
    FOREIGN KEY (test_plan_id) REFERENCES test_plans(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (version_id) REFERENCES project_versions(id) ON DELETE SET NULL
);
```

### API接口设计

#### 版本管理接口（新增）

```
GET    /api/versions                            # 获取版本列表
POST   /api/versions                            # 创建新版本
GET    /api/versions/{id}                       # 获取版本详情
PUT    /api/versions/{id}                       # 更新版本信息
DELETE /api/versions/{id}                       # 删除版本
POST   /api/versions/{id}/release               # 发布版本
POST   /api/versions/{id}/archive               # 归档版本

GET    /api/versions/{id}/baseline              # 获取版本基线
POST   /api/versions/{id}/baseline              # 创建版本基线
GET    /api/versions/{id}/snapshot              # 获取版本快照
POST   /api/versions/{id}/snapshot              # 创建版本快照

GET    /api/versions/compare/{id1}/{id2}        # 版本对比
POST   /api/versions/{id}/rollback              # 版本回溯
GET    /api/versions/{id}/changelog             # 获取版本变更日志
```

### 目录结构

```
qaitest/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── project.py
│   │   │   ├── version.py              # [NEW] 版本模型
│   │   │   ├── requirement.py
│   │   │   ├── testcase.py
│   │   │   ├── testplan.py
│   │   │   └── testreport.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── project.py
│   │   │   ├── version.py              # [NEW] 版本Schema
│   │   │   ├── requirement.py
│   │   │   ├── testcase.py
│   │   │   ├── testplan.py
│   │   │   └── testreport.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── projects.py
│   │   │   ├── versions.py             # [NEW] 版本API
│   │   │   ├── requirements.py
│   │   │   ├── testcases.py
│   │   │   ├── testplans.py
│   │   │   ├── testreports.py
│   │   │   └── websocket.py
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── runtime.py
│   │   │   ├── messages.py
│   │   │   ├── requirement_agents.py
│   │   │   └── testcase_agents.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── project_service.py
│   │   │   ├── version_service.py      # [NEW] 版本服务
│   │   │   ├── requirement_service.py
│   │   │   ├── testcase_service.py
│   │   │   ├── testplan_service.py
│   │   │   └── testreport_service.py
│   │   ├── rag/
│   │   │   ├── __init__.py
│   │   │   ├── embeddings.py
│   │   │   ├── document_loader.py
│   │   │   ├── vector_store.py
│   │   │   └── index_manager.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── logger.py
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── main.ts
│   │   ├── App.vue
│   │   ├── router/
│   │   │   └── index.ts
│   │   ├── stores/
│   │   │   ├── project.ts
│   │   │   ├── version.ts              # [NEW] 版本状态管理
│   │   │   ├── requirement.ts
│   │   │   ├── testcase.ts
│   │   │   ├── testplan.ts
│   │   │   └── testreport.ts
│   │   ├── views/
│   │   │   ├── ProjectList.vue
│   │   │   ├── VersionList.vue         # [NEW] 版本列表页
│   │   │   ├── VersionDetail.vue       # [NEW] 版本详情页
│   │   │   ├── VersionCompare.vue      # [NEW] 版本对比页
│   │   │   ├── RequirementAnalysis.vue
│   │   │   ├── RequirementList.vue
│   │   │   ├── TestCaseGenerate.vue
│   │   │   ├── TestCaseList.vue
│   │   │   ├── TestPlanList.vue
│   │   │   ├── TestPlanDetail.vue
│   │   │   ├── TestReportList.vue
│   │   │   └── TestReportDetail.vue
│   │   ├── components/
│   │   │   ├── Layout.vue
│   │   │   ├── Terminal.vue
│   │   │   ├── VersionSelector.vue     # [NEW] 版本选择器组件
│   │   │   ├── VersionDiff.vue         # [NEW] 版本差异展示组件
│   │   │   └── ReportChart.vue
│   │   ├── api/
│   │   │   ├── project.ts
│   │   │   ├── version.ts              # [NEW] 版本API
│   │   │   ├── requirement.ts
│   │   │   ├── testcase.ts
│   │   │   ├── testplan.ts
│   │   │   └── testreport.ts
│   │   ├── types/
│   │   │   ├── project.ts
│   │   │   ├── version.ts              # [NEW] 版本类型定义
│   │   │   ├── requirement.ts
│   │   │   ├── testcase.ts
│   │   │   ├── testplan.ts
│   │   │   └── testreport.ts
│   │   └── styles/
│   │       └── index.css
│   ├── vite.config.ts
│   └── package.json
│
└── README.md
```

## 实施要点

### 版本管理关键实践

1. **版本号规范**: 遵循语义化版本控制（主版本号.次版本号.修订号）
2. **基线管理**: 每个版本发布时自动创建基线快照
3. **版本对比**: 支持需求、用例、执行结果的差异对比
4. **版本回溯**: 支持一键恢复到历史版本状态
5. **关联策略**: 

- **测试计划**是版本关联的主要入口（必选关联版本）
- **测试用例**独立设计，不强制绑定版本（version_id可选）
- **功能点**可选择性关联版本（用于需求变更追踪）
- **测试报告**继承测试计划的版本关联
- 用例通过测试计划间接关联到版本，实现用例复用与版本管理的平衡

### AutoGen 0.7.5 关键实践

1. **严格使用异步API**: 所有Agent方法必须使用async/await
2. **RoutedAgent + message_handler**: 使用@message_handler装饰器处理消息
3. **Topic订阅发布**: 通过@type_subscription订阅Topic
4. **流式输出**: 使用run_stream()获取异步生成器

## 设计风格

采用现代简约的企业级设计风格，以专业、高效、易用为核心理念。使用蓝色系为主色调，体现科技感和专业性。界面布局清晰，信息层级分明。

## 版本迭代规划

### v1.0（当前版本）

- **登录/权限**：无登录功能，聚焦AI测试用例生成核心能力
- **预留字段**：所有实体预留 `created_by`、`executor` 字段，便于后续扩展
- **核心目标**：验证AI生成测试用例的可用性和质量

### v1.1（后续迭代）

- 增加简单登录功能（用户名/密码）
- 基础的用户管理

### v1.2（后续迭代）

- 增加角色权限管理（管理员/测试经理/测试工程师）
- 数据隔离与权限控制

## 页面规划

### 1. 项目列表页

- 顶部导航栏：Logo、系统名称、全局搜索、主题切换按钮
- 左侧菜单栏（按工作流顺序）：项目管理、需求分析、功能点管理、用例生成、用例管理、测试计划、测试报告、版本管理
- 主内容区：页面标题+新建项目按钮、项目卡片列表、搜索框和筛选器

### 2. 版本列表页（新增）

- 顶部区域：新建版本按钮、状态筛选器、搜索框
- 主内容区：版本卡片列表
- 版本号、版本名称、状态标签
- 发布时间、创建人
- 需求数、用例数、计划数、报告数
- 操作按钮：查看详情、创建基线、版本对比、发布、归档

### 3. 版本详情页（新增）

- 顶部区域：版本基本信息（版本号、状态、发布说明）
- Tab切换：概览、需求、用例、计划、报告、变更日志
- 概览Tab：统计数据、趋势图表
- 变更日志Tab：版本变更历史记录

### 4. 版本对比页（新增）

- 左侧：版本选择器（版本A）
- 右侧：版本选择器（版本B）
- 中间：差异展示区域
- 需求变更列表（新增/修改/删除）
- 用例变更列表
- 执行结果对比

### 5. 需求分析页

- 顶部区域：项目选择下拉框、版本选择下拉框（新增）
- 左侧区域：文件上传区域、需求描述文本框、"开始分析"按钮
- 右侧区域：Terminal风格实时输出区域
- 底部区域：分析完成后显示功能点预览

### 6. 用例生成页

- 左侧区域：功能点选择列表（多选）
- 右侧区域：Terminal风格实时输出区域
- 用例不强制绑定版本，可在测试计划中选择关联版本

### 7. 用例列表页

- 顶部区域：搜索框、筛选器、导出按钮
- 主内容区：表格展示、用例详情弹窗
- 用例独立管理，不按版本筛选

### 8. 测试计划列表页

- 顶部区域：新建计划按钮、版本筛选器、状态筛选器
- 主内容区：测试计划卡片列表、进度条、统计信息
- 创建计划时选择关联版本（必选），再从用例库中选择用例

### 9. 测试报告列表页

- 顶部区域：新建报告按钮、版本筛选器（新增）、状态筛选器
- 主内容区：测试报告卡片列表、导出按钮

## Agent Extensions

### SubAgent

- **code-explorer**
- Purpose: 在实现过程中探索代码库结构，确保架构一致性
- Expected outcome: 快速定位相关代码文件和依赖关系

### Skill

- **pdf**
- Purpose: 处理PDF格式的需求文档上传和解析，以及测试报告PDF导出
- Expected outcome: 从PDF文件中提取文本内容用于需求分析，生成PDF格式测试报告

- **docx**
- Purpose: 处理Word格式的需求文档上传和解析，以及测试报告Word导出
- Expected outcome: 从DOCX文件中提取文本内容用于需求分析，生成Word格式测试报告

- **xlsx**
- Purpose: 导出测试用例和测试计划执行报告为Excel格式
- Expected outcome: 生成格式规范的Excel文件