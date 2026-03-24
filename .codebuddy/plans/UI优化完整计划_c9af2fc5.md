---
name: UI优化完整计划
overview: 菜单结构优化（5个菜单）+ 项目管理卡片化 + 向量数据多维度删除
design:
  architecture:
    framework: vue
    component: tdesign
  styleKeywords:
    - Minimalism
    - Clean
    - Modern
    - Card-based
  fontSystem:
    fontFamily: PingFang SC
    heading:
      size: 18px
      weight: 600
    subheading:
      size: 14px
      weight: 500
    body:
      size: 14px
      weight: 400
  colorSystem:
    primary:
      - "#3B82F6"
    background:
      - "#FFFFFF"
      - "#F9FAFB"
    text:
      - "#1F2937"
      - "#6B7280"
    functional:
      - "#3B82F6"
todos:
  - id: modify-layout-menu
    content: 修改 Layout.vue 菜单配置，精简为5个菜单项
    status: completed
  - id: enhance-project-card
    content: 增强 ProjectList.vue 项目卡片化，增加统计数据和快捷入口
    status: completed
    dependencies:
      - modify-layout-menu
  - id: add-backend-stats
    content: 后端增加项目统计接口 GET /api/projects/{id}/stats，返回版本/需求/功能点/用例/计划数量
    status: completed
  - id: modify-requirement-analysis
    content: 修改 RequirementAnalysis.vue，增加Tab切换（需求分析、需求列表、功能点管理）
    status: completed
    dependencies:
      - modify-layout-menu
  - id: modify-testcase-generate
    content: 修改 TestCaseGenerate.vue，增加Tab切换（用例生成、用例管理）
    status: completed
    dependencies:
      - modify-layout-menu
  - id: add-requirement-name-filter
    content: 修改 RequirementList.vue，增加"所属需求"筛选列
    status: completed
  - id: enhance-rag-delete
    content: 增强向量数据删除能力：索引存储requirement_name，新增按版本/需求删除方法和API
    status: completed
---

## 产品概述

优化 qaitest智测平台 的菜单结构和交互体验，使AI功能更易识别，整合相关功能模块，增强项目管理能力，并扩展向量数据删除维度。

## 核心功能

### 1. 菜单结构优化

**优化前（8个扁平菜单）：**
项目管理、需求分析、功能点管理、用例生成、用例管理、测试计划、测试报告、版本管理

**优化后（5个菜单）：**

- 项目管理（卡片化，含统计数据和快捷入口）
- AI需求分析（Tab化：需求分析、需求列表、功能点管理）
- AI用例生成（Tab化：用例生成、用例管理）
- 测试计划
- 测试报告

### 2. 项目管理卡片化增强

- 项目卡片展示：项目名称、描述、状态
- 统计数据：版本数、需求数、功能点数、用例数、测试计划数
- 快捷入口：AI需求分析、AI用例生成、测试计划、测试报告、详情
- 最近活动展示

### 3. AI需求分析页面Tab化

- Tab1：需求分析（原有功能，AI提取功能点）
- Tab2：需求列表（按requirement_name分组展示）
- Tab3：功能点管理（原有功能点列表，增加"所属需求"筛选）

### 4. AI用例生成页面Tab化

- Tab1：用例生成（原有功能，AI生成测试用例）
- Tab2：用例管理（原有用例列表）

### 5. 向量数据删除增强（级联删除）

**删除入口整合到业务操作中，自动触发向量数据清理：**

| 业务操作 | 触发位置 | 调用的向量删除方法 |
| --- | --- | --- |
| 删除项目 | 项目管理页面 | `delete_by_project(project_id)` |
| 删除版本 | 项目管理 → 版本Tab | `delete_by_version(project_id, version_id)` |
| 删除需求 | AI需求分析 → 需求列表Tab | `delete_by_requirement(project_id, requirement_name, version_id?)` |


**向量删除方法参数：**

| 删除方式 | 所需参数 | 说明 |
| --- | --- | --- |
| 按项目删除 | 项目ID | 删除整个项目的向量数据（已有） |
| 按版本删除 | 项目ID + 版本ID | 在项目集合中筛选 version_id 删除 |
| 按需求删除 | 项目ID + 版本ID(可选) + 需求名称 | 在项目集合中按需求名称删除 |


**元数据要求：**

- 索引时存储 requirement_name 元数据
- 版本级需求：version_id 有值
- 项目级需求：version_id 为空

**用户体验：** 用户只需删除业务数据，向量数据自动清理，无需额外操作

## 技术栈

- 前端：Vue 3 + TypeScript + Lucide Vue Next + Tailwind CSS
- 后端：FastAPI + Tortoise ORM
- 向量存储：Milvus

## 实现方案

### 1. 菜单结构调整

修改 `Layout.vue` 的 menuItems 配置：

```typescript
const menuItems = [
  { path: '/projects', name: '项目管理', icon: Folder },
  { path: '/requirements/analysis', name: 'AI需求分析', icon: FileText },
  { path: '/testcases/generate', name: 'AI用例生成', icon: TestTube },
  { path: '/testplans', name: '测试计划', icon: ClipboardList },
  { path: '/testreports', name: '测试报告', icon: FileBarChart },
]
```

### 2. 项目管理卡片化

增强 `ProjectList.vue`：

- 调用后端统计接口获取项目维度数据
- 卡片布局增加统计展示区域
- 增加快捷操作按钮

### 3. Tab化改造

**RequirementAnalysis.vue** 增加Tab切换：

- 使用 activeTab 状态管理当前Tab
- Tab1：原有需求分析表单
- Tab2：新增需求列表组件
- Tab3：嵌入功能点列表组件

**TestCaseGenerate.vue** 增加Tab切换：

- Tab1：原有用例生成表单
- Tab2：嵌入用例列表组件

### 4. 向量数据删除增强

**后端修改 (index_manager.py)**：

- 索引时增加 requirement_name 元数据
- 新增 `delete_by_version(project_id, version_id)` 方法
- 新增 `delete_by_requirement(project_id, requirement_name, version_id=None)` 方法

**后端修改 (rag.py)**：

- 新增 `DELETE /rag/index/project/{project_id}` 端点（已有）
- 新增 `DELETE /rag/index/version/{project_id}/{version_id}` 端点
- 新增 `DELETE /rag/index/requirement` 端点
- Body: `{ project_id, requirement_name, version_id? }`

**前端修改 (rag.ts)**：

- 增加 `deleteByProject(projectId)` 方法（已有）
- 增加 `deleteByVersion(projectId, versionId)` 方法
- 增加 `deleteByRequirement(projectId, requirementName, versionId?)` 方法

## 目录结构

```
frontend/src/
├── components/
│   └── Layout.vue              # [MODIFY] 菜单配置精简为5个
├── views/
│   ├── ProjectList.vue         # [MODIFY] 卡片化增强，统计数据，快捷入口
│   ├── RequirementAnalysis.vue # [MODIFY] 增加Tab切换（需求分析、需求列表、功能点管理）
│   ├── TestCaseGenerate.vue    # [MODIFY] 增加Tab切换（用例生成、用例管理）
│   ├── RequirementList.vue     # [MODIFY] 增加"所属需求"筛选列
│   └── RequirementGroupList.vue# [NEW] 需求列表组件（Tab内使用）
├── api/
│   └── rag.ts                  # [MODIFY] 增加按版本/需求删除API
└── types/
    └── requirement.ts          # [MODIFY] 添加 requirement_name 字段

backend/app/
├── api/
│   ├── rag.py                  # [MODIFY] 增加删除端点
│   └── requirements.py         # [MODIFY] 增加需求分组接口
└── rag/
    └── index_manager.py        # [MODIFY] 增加删除方法，索引存储requirement_name
```

## 设计风格

保持现有简约现代风格，采用卡片化布局突出项目概览。

## 项目卡片设计

```
+---------------------------------------------------------------+
|  项目名称                                              [编辑]  |
|  项目描述信息...                                               |
|                                                               |
|  +--------+--------+--------+--------+--------+              |
|  |  版本  |  需求  | 功能点 |  用例  | 测试计划 |              |
|  |   3    |   5    |   12   |   45   |    2    |              |
|  +--------+--------+--------+--------+--------+              |
|                                                               |
|  最近活动：2024-03-18 AI需求分析完成                           |
|                                                               |
|  [AI需求分析] [AI用例生成] [测试计划] [报告] [详情]            |
+---------------------------------------------------------------+
```

## Tab页面设计

AI需求分析页面：

```
+---------------------------------------------------------------+
|  AI需求分析                                                    |
+---------------------------------------------------------------+
|  [需求分析]  [需求列表]  [功能点管理]    <-- Tab栏             |
+---------------------------------------------------------------+
|                                                               |
|                    Tab内容区域                                 |
|                                                               |
+---------------------------------------------------------------+
```

## 布局结构

```
+---------------------------------------------------------------+
|  qaitest智测平台              [搜索框]           [主题切换]    |
+---------------+-----------------------------------------------+
|  折叠按钮    |                                               |
+---------------+                                               |
|  项目管理     |                                               |
+---------------+              主内容区                          |
|  AI需求分析   |                                               |
+---------------+                                               |
|  AI用例生成   |                                               |
+---------------+                                               |
|  测试计划     |                                               |
+---------------+                                               |
|  测试报告     |                                               |
+---------------+-----------------------------------------------+
```

## SubAgent

- **code-explorer**: 探索代码库中相关文件的实现细节，确保修改方案与现有架构一致