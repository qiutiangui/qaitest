---
name: fix-websocket-message-type
overview: 修复WebSocket完成消息类型不匹配问题：将后端发送的message_type从"testcase_generation_complete"改为"complete"，使前端能正确识别任务完成状态
todos:
  - id: fix-message-type
    content: 修改 testcase_agents.py 第1551行，将 message_type 改为 "complete"
    status: pending
---

## 问题描述

前端进度条显示100%后，仍然显示"AI正在工作中..."，没有正确切换到"生成完成"状态。

## 问题原因

后端发送的WebSocket消息类型不匹配：

- 后端发送：`type = "testcase_generation_complete"`
- 前端期望：`type === 'complete'`

导致前端无法触发完成处理函数 `handleStepComplete`。

## 解决方案

修改后端 `testcase_agents.py` 第1551行，将 `message_type` 参数从 `"testcase_generation_complete"` 改为 `"complete"`。

## 修改内容

**文件**：`backend/app/agents/testcase_agents.py`

**修改位置**：第1547-1553行

**修改前**：

```python
await push_to_websocket(
    task_id,
    "step5_review",
    "complete",
    "testcase_generation_complete",  # ❌ 消息类型不匹配
    {"saved_ids": saved_ids, "count": len(saved_ids)}
)
```

**修改后**：

```python
await push_to_websocket(
    task_id,
    "step5_review",
    "complete",
    "complete",  # ✅ 改为"complete"，匹配前端期望
    {"saved_ids": saved_ids, "count": len(saved_ids)}
)
```

## 消息格式说明

`push_to_websocket` 参数顺序：

1. `task_id`: 任务ID
2. `agent_name`: Agent名称（前端用此判断具体完成事件）
3. `content`: 消息内容
4. `message_type`: 消息类型（必须是 thinking/response/error/complete 之一）
5. `extra_data`: 额外数据

修复后，前端收到的消息：

```javascript
{
  type: "complete",  // ✅ 匹配前端条件
  agent: "step5_review",
  content: "complete",
  data: {saved_ids: [...], count: 41}
}
```

前端会在 `handleStepComplete` 中根据 `agent === 'step5_review'` 设置 `generationComplete = true`。