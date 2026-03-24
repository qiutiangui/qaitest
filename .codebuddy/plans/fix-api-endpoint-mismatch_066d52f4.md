---
name: fix-api-endpoint-mismatch
overview: 修复前端 TaskRecords.vue 与后端 API 路径不匹配导致的 422 错误
todos:
  - id: fix-frontend-api
    content: 修改 TaskRecords.vue 中的 API 调用路径和参数
    status: completed
  - id: add-backend-retry
    content: 为 ai_tasks.py 添加重试接口
    status: completed
  - id: add-project-name
    content: 后端返回数据补充 project_name 字段
    status: completed
---

## 问题概述

前端 TaskRecords.vue 页面调用 `/api/requirements/analysis-records` 等 API 返回 422 错误，原因是前后端 API 路径不匹配。

## 核心问题

1. **API 路径不匹配**：前端调用的路径与后端定义的路由不一致
2. **后端缺少接口**：缺少任务重试接口
3. **参数格式差异**：删除接口使用 `id` vs `task_id` 参数不同

## 具体对比

| 前端调用 | 后端实际路由 |
| --- | --- |
| `GET /api/requirements/analysis-records` | `GET /api/ai-tasks/requirement-analysis/list` |
| `GET /api/testcases/generation-records` | `GET /api/ai-tasks/testcase-generation/list` |
| `DELETE /api/requirements/analysis-records/${id}` | `DELETE /api/ai-tasks/requirement-analysis/${task_id}` |
| `DELETE /api/testcases/generation-records/${id}` | `DELETE /api/ai-tasks/testcase-generation/${task_id}` |
| `POST /api/requirements/analysis/retry` | 不存在 |
| `POST /api/testcases/generate/retry` | 不存在 |


## 技术方案

修改前端 API 调用路径以匹配后端路由，同时为后端添加重试接口。

## 修改文件

```
frontend/src/views/AICaseGeneration/TaskRecords.vue  # [MODIFY] 修复 API 调用路径和参数
backend/app/api/ai_tasks.py                          # [MODIFY] 添加重试接口
```

## 实现要点

1. **前端修改**：

- 将 `/requirements/analysis-records` 改为 `/ai-tasks/requirement-analysis/list`
- 将 `/testcases/generation-records` 改为 `/ai-tasks/testcase-generation/list`
- 删除接口参数从 `id` 改为 `task_id`（使用 `record.task_id` 而非 `record.id`）
- 添加项目名称到返回数据处理（后端需要补充 project_name 字段）

2. **后端修改**：

- 添加 `POST /requirement-analysis/retry` 接口
- 添加 `POST /testcase-generation/retry` 接口
- 返回数据补充 `project_name` 字段