---
name: testcase-management-optimization
overview: 优化测试用例管理模块，包括列表新增所属需求字段、新增编辑功能、完善详情页显示、修复测试步骤格式、新增新建功能
todos:
  - id: backend-schema-extend
    content: 后端TestCaseResponse添加requirement_name字段
    status: completed
  - id: backend-api-join
    content: 后端API关联查询Requirement获取requirement_name
    status: completed
    dependencies:
      - backend-schema-extend
  - id: frontend-type-extend
    content: 前端TestCase类型添加requirement_name字段
    status: completed
  - id: frontend-list-column
    content: 列表新增所属需求列
    status: completed
    dependencies:
      - frontend-type-extend
      - backend-api-join
  - id: frontend-detail-complete
    content: 详情页补充缺失字段（描述、测试类型、项目、需求、后置条件、创建者）
    status: completed
  - id: frontend-steps-format
    content: 测试步骤格式化为带序号文本
    status: completed
  - id: frontend-edit-dialog
    content: 新增编辑功能（弹窗+表单+保存逻辑）
    status: completed
  - id: frontend-create-dialog
    content: 新增新建功能（按钮+弹窗+表单+保存逻辑）
    status: completed
---

## 产品概述

优化测试用例管理模块，新增所属需求字段显示、编辑功能、完善详情页字段、优化测试步骤格式、新增新建功能。

## 核心功能

### 1. 列表新增所属需求字段

- 列表表格新增"所属需求"列
- 显示关联功能点所属的需求名称（requirement_name）

### 2. 新增编辑功能

- 操作列添加编辑按钮
- 弹窗编辑测试用例基本信息
- 支持编辑标题、描述、优先级、状态、测试类型、前置条件、后置条件

### 3. 详情页字段完善

- 补充显示：用例描述、测试类型、所属项目、所属需求、后置条件、创建者
- 优化详情页布局

### 4. 测试步骤格式优化

- 将steps数组格式化为带序号的文本显示
- 格式示例：

```
1、进入申报类型配置页面
2、页面正常加载，显示现有的申报类型列表
```

### 5. 新增新建测试用例功能

- 页面顶部添加"新建用例"按钮
- 弹窗表单包含：标题、所属项目、关联功能点、描述、优先级、状态、测试类型、前置条件、测试步骤
- 支持动态添加/删除测试步骤

## 技术栈

- 前端：Vue 3 + TypeScript + Element Plus
- 后端：FastAPI + Tortoise ORM

## 实现方案

### 后端改动

#### 1. Schema扩展 (`backend/app/schemas/testcase.py`)

- `TestCaseResponse` 添加 `requirement_name` 字段

#### 2. API改动 (`backend/app/api/testcases.py`)

- 列表查询时关联查询Requirement表获取requirement_name
- 详情查询时同样关联Requirement表

### 前端改动

#### 1. 类型定义 (`frontend/src/types/testcase.ts`)

- `TestCase` 接口添加 `requirement_name?: string`

#### 2. 页面组件 (`frontend/src/views/AICaseGeneration/TestCases.vue`)

- 列表新增"所属需求"列
- 添加编辑弹窗组件和逻辑
- 完善详情弹窗字段
- 格式化测试步骤显示
- 添加新建弹窗组件和逻辑

## 目录结构

```
backend/app/
├── api/
│   └── testcases.py           # [MODIFY] 列表和详情查询关联Requirement表
├── schemas/
│   └── testcase.py            # [MODIFY] TestCaseResponse添加requirement_name

frontend/src/
├── types/
│   └── testcase.ts            # [MODIFY] 添加requirement_name字段
├── views/AICaseGeneration/
│   └── TestCases.vue          # [MODIFY] 新增编辑/新建弹窗、完善详情页、优化步骤格式
```

## 实现细节

### 后端TestCaseResponse扩展

```python
class TestCaseResponse(TestCaseBase):
    id: int
    project_id: Optional[int]
    requirement_id: Optional[int]
    requirement_name: Optional[str] = None  # 新增
    version_id: Optional[int]
    creator: str
    created_at: datetime
    steps: Optional[List[TestStepResponse]] = None
```

### 后端API关联查询

```python
# 获取测试用例详情时关联查询Requirement
testcase = await TestCase.get_or_none(id=testcase_id).prefetch_related("steps", "requirement")
if testcase.requirement:
    testcase_dict["requirement_name"] = testcase.requirement.requirement_name
```

### 前端测试步骤格式化函数

```typescript
function formatSteps(steps: TestStep[] | undefined): string {
  if (!steps || steps.length === 0) return '-'
  return steps
    .sort((a, b) => a.step_number - b.step_number)
    .map(s => `${s.step_number}、${s.description}`)
    .join('\n')
}
```

### 前端新建/编辑弹窗结构

- 表单字段：标题(必填)、所属项目、关联功能点、描述、优先级、状态、测试类型、前置条件、后置条件
- 测试步骤：动态列表，支持添加/删除步骤行