---
name: qaitest智测平台开发计划(v5-完整版)
overview: 从零构建企业级AI测试用例生成系统，使用LlamaIndex+qwen3-embedding实现RAG，集成AutoGen多智能体，实现需求分析→功能点提取→测试用例生成→测试计划管理→测试报告生成的全流程智能化。
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
    fontFamily: PingFang SC
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
    content: 搭建后端项目结构，配置FastAPI、Tortoise ORM、Loguru，创建数据库表结构
    status: pending
  - id: setup-frontend
    content: 搭建前端项目结构，配置Vue3、Vite、TypeScript、Element Plus、Pinia、Vue Router
    status: pending
  - id: implement-projects
    content: 实现项目管理模块（前后端CRUD）
    status: pending
    dependencies:
      - setup-backend
      - setup-frontend
  - id: implement-rag
    content: 实现LlamaIndex RAG模块：qwen3-embedding配置、文档加载、Milvus向量索引
    status: pending
    dependencies:
      - setup-backend
  - id: implement-requirement-agents
    content: 实现需求分析多智能体流水线（RequirementAcquireAgent -> RequirementAnalysisAgent -> RequirementOutputAgent）
    status: pending
    dependencies:
      - implement-rag
  - id: implement-websocket
    content: 实现WebSocket实时通信，将Agent推理过程实时推送到前端Terminal组件
    status: pending
    dependencies:
      - setup-backend
      - setup-frontend
  - id: implement-requirement-analysis
    content: 实现需求分析界面（文档上传、实时输出、功能点提取）
    status: pending
    dependencies:
      - implement-requirement-agents
      - implement-websocket
  - id: implement-requirement-management
    content: 实现功能点管理模块（列表展示、编辑、删除）
    status: pending
    dependencies:
      - implement-requirement-analysis
  - id: implement-testcase-agents
    content: 实现用例生成多智能体流水线（TestCaseGenerateAgent -> TestCaseReviewAgent -> TestCaseFinalizeAgent -> TestCaseInDatabaseAgent）
    status: pending
    dependencies:
      - implement-requirement-agents
  - id: implement-testcase-generation
    content: 实现用例生成界面（功能点选择、实时输出）
    status: pending
    dependencies:
      - implement-testcase-agents
      - implement-websocket
  - id: implement-testcase-management
    content: 实现用例管理模块（列表展示、详情查看、导出Excel/Markdown）
    status: pending
    dependencies:
      - implement-testcase-generation
  - id: implement-testplan-management
    content: 实现测试计划管理模块（计划CRUD、用例关联、执行跟踪、统计展示）
    status: pending
    dependencies:
      - implement-testcase-management
  - id: implement-testreport-management
    content: 实现测试报告管理模块（报告生成、多格式导出、可视化图表、模板管理、版本管理）
    status: pending
    dependencies:
      - implement-testplan-management
  - id: integration-test
    content: 系统集成测试，优化用户体验，编写部署文档
    status: pending
    dependencies:
      - implement-testreport-management
---

## 产品概述

「qaitest 智测平台」是一个企业级的AI测试用例生成系统，通过多智能体协作自动分析需求文档、提取功能点并生成高质量测试用例，并提供测试计划管理、执行跟踪和测试报告生成功能，实现从需求到报告的全流程智能化。

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
- 测试计划关联到项目

### 7. 测试报告管理（新增）

- 基于测试计划自动生成测试报告
- 测试报告包含：执行概况、统计图表、用例详情、缺陷分析
- 支持多种格式导出（PDF/HTML/Word）
- 测试报告模板管理
- 测试报告历史版本管理
- 可视化图表展示（饼图、柱状图、趋势图）
- 报告在线预览功能

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
- **报告生成**: WeasyPrint (PDF), Jinja2 (模板引擎)

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

#### 测试报告相关表

```sql
-- 测试报告表
CREATE TABLE test_reports (
    id INT PRIMARY KEY AUTO_INCREMENT,
    test_plan_id INT NOT NULL,
    project_id INT NOT NULL,
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
    version INT DEFAULT 1,
    created_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_plan (test_plan_id),
    INDEX idx_project (project_id),
    FOREIGN KEY (test_plan_id) REFERENCES test_plans(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- 测试报告模板表
CREATE TABLE report_templates (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    template_content TEXT NOT NULL,
    template_type VARCHAR(20) DEFAULT 'HTML',
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 测试报告附件表
CREATE TABLE report_attachments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    report_id INT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_type VARCHAR(20),
    file_size INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_report (report_id),
    FOREIGN KEY (report_id) REFERENCES test_reports(id) ON DELETE CASCADE
);
```

### API接口设计

#### 测试报告相关接口

```
GET    /api/testreports                        # 获取测试报告列表（支持分页、搜索）
POST   /api/testreports                        # 创建测试报告
GET    /api/testreports/{id}                   # 获取测试报告详情
PUT    /api/testreports/{id}                   # 更新测试报告
DELETE /api/testreports/{id}                   # 删除测试报告
POST   /api/testreports/generate/{plan_id}     # 基于测试计划生成报告
GET    /api/testreports/{id}/export/pdf        # 导出PDF格式
GET    /api/testreports/{id}/export/html       # 导出HTML格式
GET    /api/testreports/{id}/export/word       # 导出Word格式
GET    /api/testreports/{id}/preview           # 在线预览报告
GET    /api/reporttemplates                    # 获取报告模板列表
POST   /api/reporttemplates                    # 创建报告模板
GET    /api/reporttemplates/{id}               # 获取模板详情
PUT    /api/reporttemplates/{id}               # 更新模板
DELETE /api/reporttemplates/{id}               # 删除模板
GET    /api/testreports/{id}/statistics        # 获取报告统计数据
GET    /api/testreports/{id}/versions          # 获取报告历史版本
POST   /api/testreports/{id}/version           # 创建新版本
```

### 目录结构

```
qaitest/
├── backend/
│   ├── app/
│   │   ├── models/
│   │   │   ├── testplan.py
│   │   │   └── testreport.py         # [NEW] 测试报告模型
│   │   ├── schemas/
│   │   │   ├── testplan.py
│   │   │   └── testreport.py         # [NEW] 测试报告Schema
│   │   ├── api/
│   │   │   ├── testplans.py
│   │   │   ├── testreports.py        # [NEW] 测试报告API
│   │   │   └── reporttemplates.py    # [NEW] 报告模板API
│   │   ├── services/
│   │   │   ├── testplan_service.py
│   │   │   ├── testreport_service.py # [NEW] 测试报告服务
│   │   │   └── report_export_service.py  # [NEW] 报告导出服务
│   │   └── templates/
│   │       └── reports/              # [NEW] 报告模板目录
│   │           ├── default.html
│   │           └── executive.html
│
├── frontend/
│   ├── src/
│   │   ├── stores/
│   │   │   ├── testplan.ts
│   │   │   └── testreport.ts         # [NEW] 测试报告状态管理
│   │   ├── views/
│   │   │   ├── TestPlanList.vue
│   │   │   ├── TestPlanDetail.vue
│   │   │   ├── TestReportList.vue    # [NEW] 测试报告列表页
│   │   │   ├── TestReportDetail.vue  # [NEW] 测试报告详情页
│   │   │   └── TestReportPreview.vue # [NEW] 报告预览页
│   │   ├── components/
│   │   │   ├── TestPlanStatistics.vue
│   │   │   ├── ReportChart.vue       # [NEW] 报告图表组件
│   │   │   └── ReportExport.vue      # [NEW] 报告导出组件
│   │   ├── api/
│   │   │   ├── testplan.ts
│   │   │   └── testreport.ts         # [NEW] 测试报告API
│   │   └── types/
│   │       ├── testplan.ts
│   │       └── testreport.ts         # [NEW] 测试报告类型定义
```

## 核心依赖包

```
# 后端 requirements.txt (新增)
weasyprint>=60.0        # PDF生成
jinja2>=3.1.0          # 模板引擎
python-docx>=0.8.11    # Word文档生成
matplotlib>=3.5.0      # 图表生成
pillow>=9.0.0          # 图像处理
```

## 实施要点

### 测试报告功能关键实践

1. **自动生成报告**: 基于测试计划执行数据自动统计并生成报告
2. **多格式导出**: 支持PDF、HTML、Word三种格式导出
3. **可视化图表**: 使用ECharts展示饼图、柱状图、趋势图
4. **模板管理**: 支持自定义报告模板
5. **版本管理**: 支持报告历史版本管理
6. **在线预览**: 支持报告在线预览功能

## 设计风格

采用现代简约的企业级设计风格，以专业、高效、易用为核心理念。使用蓝色系为主色调，体现科技感和专业性。界面布局清晰，信息层级分明。

## 页面规划

### 8. 测试报告列表页（新增）

- 顶部区域：新建报告按钮、项目筛选器、状态筛选器、搜索框
- 主内容区：测试报告卡片列表
- 报告名称、测试计划名称、创建时间
- 执行概况：用例总数、通过率、失败率
- 状态标签：草稿/已发布/已归档
- 版本号
- 操作按钮：查看详情、导出PDF/HTML/Word、编辑、删除
- 分页组件

### 9. 测试报告详情页（新增）

- 顶部区域：
- 报告标题、状态、创建时间、版本号
- 操作按钮：导出、编辑、生成新版本
- 左侧区域：
- 执行概况卡片：总用例数、通过率、失败率、阻塞率
- 执行状态分布图（饼图）
- 每日执行趋势图（折线图）
- 模块覆盖情况（柱状图）
- 右侧区域：
- 用例执行详情列表（可折叠）
- 失败用例详情
- 缺陷分析
- 底部区域：
- 报告摘要（Markdown编辑器）
- 测试结论与建议

### 10. 报告预览页面（新增）

- 全屏预览模式
- 支持缩放
- 支持打印
- 支持下载

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