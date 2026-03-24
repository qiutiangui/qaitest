---
name: 删除旧表-统一使用AITestTask
overview: 删除两个旧表（RequirementAnalysisTask、TestCaseGenerationTask），统一使用新表AITestTask。由于用户已删除所有数据，无需数据迁移。
todos:
  - id: modify-models-init
    content: 修改 models/__init__.py，移除 RequirementAnalysisTask 和 TestCaseGenerationTask 的导出
    status: completed
  - id: delete-task-models
    content: 删除 models/task.py 中的旧表类定义（保留文件结构）
    status: completed
    dependencies:
      - modify-models-init
  - id: modify-requirements-api
    content: 修改 requirements.py，创建任务改用 AITestTask，更新进度使用 update_requirement_progress
    status: completed
    dependencies:
      - delete-task-models
  - id: modify-testcases-api
    content: 修改 testcases.py，创建任务改用 AITestTask，更新进度使用 update_testcase_progress
    status: completed
    dependencies:
      - delete-task-models
  - id: modify-agents
    content: 修改 requirement_agents.py 和 testcase_agents.py，日志持久化改用 AITestTask
    status: completed
    dependencies:
      - delete-task-models
  - id: cleanup-ai-test-tasks
    content: 清理 ai_test_tasks.py 中的旧表查询代码，只保留新表查询
    status: completed
    dependencies:
      - delete-task-models
  - id: delete-legacy-apis
    content: 删除 ai_tasks.py 和 ai_tasks_unified.py（已被 ai_test_tasks.py 替代）
    status: completed
    dependencies:
      - modify-requirements-api
      - modify-testcases-api
  - id: test-verification
    content: 测试验证：创建任务、需求分析、用例生成全流程
    status: completed
    dependencies:
      - cleanup-ai-test-tasks
      - delete-legacy-apis
---

## 用户需求

用户已删除所有历史数据，选择完全迁移到新表AITestTask，无需数据迁移步骤。

## 产品概述

将两个旧表（RequirementAnalysisTask、TestCaseGenerationTask）完全迁移到统一的新表（AITestTask），简化数据模型，降低维护成本。

## 核心功能

- 删除旧表模型定义和导出
- 修改所有使用旧表的API和Agent代码
- 统一使用AITestTask管理任务生命周期（需求分析+用例生成）

## 技术栈

- 后端框架：FastAPI + Tortoise ORM
- 数据库：MySQL
- 表迁移：删除旧表，统一使用AITestTask

## 实现方案

由于历史数据已清空，无需数据迁移脚本，直接修改代码即可。

### 字段映射关系

**需求分析阶段**：

| 旧表字段 | 新表字段 |
| --- | --- |
| RequirementAnalysisTask.status | requirement_phase_status |
| RequirementAnalysisTask.progress | requirement_phase_progress |
| RequirementAnalysisTask.total_requirements | total_requirements |
| RequirementAnalysisTask.saved_count | saved_requirements |
| RequirementAnalysisTask.saved_ids | saved_requirement_ids |


**用例生成阶段**：

| 旧表字段 | 新表字段 |
| --- | --- |
| TestCaseGenerationTask.status | testcase_phase_status |
| TestCaseGenerationTask.progress | testcase_phase_progress |
| TestCaseGenerationTask.total_testcases | total_testcases |
| TestCaseGenerationTask.saved_count | saved_testcases |
| TestCaseGenerationTask.saved_ids | saved_testcase_ids |


### 目录结构

**修改文件列表**：

```
backend/app/
├── models/
│   ├── __init__.py          # [MODIFY] 移除旧表导出
│   └── task.py              # [MODIFY] 删除 RequirementAnalysisTask 和 TestCaseGenerationTask 类定义
├── api/
│   ├── requirements.py      # [MODIFY] 改用 AITestTask
│   ├── testcases.py         # [MODIFY] 改用 AITestTask
│   ├── ai_tasks.py          # [DELETE] 删除（已被 ai_test_tasks.py 替代）
│   ├── ai_tasks_unified.py  # [DELETE] 删除（已被 ai_test_tasks.py 替代）
│   ├── ai_test_tasks.py     # [MODIFY] 移除旧表查询逻辑
│   └── tasks.py             # [MODIFY] 改用 AITestTask
└── agents/
    ├── requirement_agents.py # [MODIFY] 日志持久化改用 AITestTask
    └── testcase_agents.py   # [MODIFY] 日志持久化改用 AITestTask
```

## 实现注意事项

1. AITestTask 已有 `add_log`、`update_requirement_progress`、`update_testcase_progress` 等方法，直接使用即可
2. 创建任务时需要设置 `task_name` 字段（新表特有）
3. 进度计算：需求分析占40%，用例生成占60%