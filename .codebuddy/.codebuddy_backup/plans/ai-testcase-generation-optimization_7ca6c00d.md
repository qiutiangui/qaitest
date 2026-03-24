---
name: ai-testcase-generation-optimization
overview: 优化AI测试用例生成流程：实现功能点并行生成（支持RAG）、简化实时日志输出、优化结果打印格式（功能点列表、第一版测试用例、评审结论、最终测试用例）
todos:
  - id: refactor-testcase-agents
    content: 重构 testcase_agents.py：实现并行RAG检索 + 用例生成 + 内存暂存
    status: completed
  - id: add-schema
    content: 添加评审结论结构化Schema定义
    status: completed
    dependencies:
      - refactor-testcase-agents
  - id: simplify-logging
    content: 简化日志输出：移除流式输出，添加结构化输出函数
    status: completed
    dependencies:
      - refactor-testcase-agents
  - id: update-frontend
    content: 更新前端 Generate.vue：解析结构化输出，优化日志渲染
    status: completed
    dependencies:
      - simplify-logging
  - id: test-integration
    content: 集成测试：验证并行生成、评审流程、日志输出
    status: completed
    dependencies:
      - update-frontend
---

## 产品概述

优化AI测试用例生成流程，解决功能点串行生成耗时长和实时日志过多的问题。

## 核心功能

- **并行生成重构**：多个功能点并行进行RAG检索和测试用例生成，大幅提升处理速度
- **日志输出优化**：保留关键进度提示，取消详细流式输出，改为完成后结构化打印
- **评审流程简化**：全部生成后一次性评审，只评审一次，评审意见处理后输出最终用例

## 输出内容规范

### 阶段1 - 功能点列表（从数据库查询）

- 字段：功能点名称、功能点描述、所属项目、所属需求、类别、优先级

### 阶段2 - 测试用例输出

1. **第一版测试用例**（内存中暂存，生成完成后打印）

- 字段：用例标题、所属需求、关联功能点、所属项目、类型、前置条件、操作步骤、预期结果

2. **评审结论**（结构化JSON）

- approved、summary、total_testcases、issues、suggestions

3. **最终测试用例**（评审优化后入库，从数据库查询打印）

- 字段：同第一版

## 技术约束

- 保持RAG功能不受影响，确保高质量生成
- 保持与其他模块的兼容性（需求管理、AI任务等）
- 评审必须执行且只评审一次

## 技术栈

- **后端**：FastAPI + AutoGen 0.7.5 + LlamaIndex 0.14.18 + Milvus
- **前端**：Vue 3 + TypeScript + Element Plus
- **实时通信**：WebSocket

## 实现方案

### 1. 并行生成架构重构

**核心流程**：

```
功能点列表 → 并行RAG检索 + 用例生成 → 内存暂存 → 合并评审 → 优化修改 → 入库保存
```

**关键设计**：

- 使用 `asyncio.gather()` 实现功能点级并行处理
- 每个功能点独立进行RAG检索（调用 `index_manager.search_for_testcase_generation`）
- 生成结果暂存在内存字典中，不入库
- 评审Agent处理所有测试用例，输出结构化JSON结论
- 定稿Agent根据评审意见优化后批量入库

### 2. 日志输出优化策略

**保留的日志**：

- 流程启动/完成提示
- 并行处理进度（如"正在处理 5/10 个功能点"）
- 关键阶段切换提示
- 错误信息

**取消的日志**：

- StreamBuffer 详细流式输出
- Agent 内部思考过程
- 中间状态输出

**新增的结构化输出**：

- 功能点列表（完成后查询数据库）
- 第一版测试用例（从内存打印）
- 评审结论（结构化JSON）
- 最终测试用例（入库后查询数据库）

### 3. 评审结论结构化格式

```
{
  "approved": true,
  "summary": "评审通过，发现2个需优化问题",
  "total_testcases": 15,
  "coverage_rate": "100%",
  "issues": [
    {"severity": "high", "testcase_index": 3, "issue": "缺少边界值测试", "suggestion": "添加边界条件用例"}
  ],
  "suggestions": ["建议增加异常场景覆盖"]
}
```

### 4. 目录结构

```
backend/app/agents/
├── testcase_agents.py          # [MODIFY] 核心重构：并行生成 + RAG + 简化日志
├── runtime.py                  # [MODIFY] 添加结构化消息推送函数
└── messages.py                 # [MODIFY] 添加评审结论消息类型

backend/app/schemas/
└── testcase.py                 # [MODIFY] 添加评审结论Schema

frontend/src/views/AICaseGeneration/
└── Generate.vue                # [MODIFY] 解析结构化输出，优化日志渲染

backend/app/api/
└── testcases.py                # [MODIFY] 调用新的生成函数
```

## 实现要点

### RAG并行检索

每个功能点在生成测试用例前，独立调用RAG检索：

```python
async def generate_with_rag(req_id: int, project_id: int) -> Dict:
    # 1. RAG检索
    rag_results = await index_manager.search_for_testcase_generation(
        requirement=description,
        project_id=project_id,
        top_k=5
    )
    # 2. 生成测试用例
    # 3. 返回结果（不入库）
```

### 性能优化

- 并行数控制：使用 `asyncio.Semaphore` 限制并发数，避免API限流
- 错误隔离：单个功能点失败不影响其他功能点
- 进度反馈：每完成一个功能点推送进度更新

### 兼容性保障

- 保持 `run_testcase_generation` 函数签名不变
- 保持数据库模型不变
- 保持前端WebSocket连接逻辑不变