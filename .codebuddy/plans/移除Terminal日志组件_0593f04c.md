---
name: 移除Terminal日志组件
overview: 从3个页面移除AI Agent Terminal日志组件，使用任务状态API轮询替代WebSocket实时通信，保留进度条和流式输出结果展示
todos:
  - id: create-ai-tasks-api
    content: 新建aiTasks.ts API文件，封装任务状态查询接口
    status: completed
  - id: modify-generate-vue
    content: 修改Generate.vue，移除Terminal组件，添加HTTP轮询逻辑
    status: completed
    dependencies:
      - create-ai-tasks-api
  - id: modify-testcase-generate-vue
    content: 修改TestCaseGenerate.vue，移除Terminal组件，添加HTTP轮询逻辑
    status: completed
    dependencies:
      - create-ai-tasks-api
  - id: modify-requirement-analysis-vue
    content: 修改RequirementAnalysis.vue，移除Terminal组件，添加HTTP轮询逻辑
    status: completed
    dependencies:
      - create-ai-tasks-api
  - id: delete-terminal-component
    content: 删除Terminal.vue组件文件
    status: completed
    dependencies:
      - modify-generate-vue
      - modify-testcase-generate-vue
      - modify-requirement-analysis-vue
---

## 用户需求

移除"AI Agent Terminal"日志组件界面，保留进度条和流式打印输出功能点和最终测试用例。

## 功能说明

- 移除Terminal组件的日志显示界面
- 保留现有的进度条UI（显示"需求分析→功能点提取→测试用例生成"步骤）
- 保留流式输出展示（功能点列表、测试用例列表）
- 使用HTTP轮询替代WebSocket获取任务状态

## 涉及页面

1. AI用例生成页面（Generate.vue）
2. 测试用例生成页面（TestCaseGenerate.vue）
3. 需求分析页面（RequirementAnalysis.vue）

## 技术方案

### 1. 轮询替代WebSocket

后端已有任务状态API：

- `GET /api/ai-tasks/requirement-analysis/{task_id}` - 返回status、saved_ids、progress等
- `GET /api/ai-tasks/testcase-generation/{task_id}` - 返回status、saved_ids、progress等

前端使用`setInterval`每2秒轮询任务状态，任务完成后清除轮询并处理结果。

### 2. 新建API文件

创建`/frontend/src/api/aiTasks.ts`封装任务状态查询API。

### 3. 组件修改策略

每个页面移除Terminal后：

- 移除Terminal组件导入和模板引用
- 移除terminalRef引用
- 添加pollTaskStatus轮询函数
- 任务完成后调用现有的complete处理逻辑

## 目录结构

```
frontend/src/
├── api/
│   └── aiTasks.ts          # [NEW] AI任务状态查询API
├── components/
│   └── Terminal.vue        # [DELETE] 移除日志组件
└── views/
    ├── AICaseGeneration/
    │   └── Generate.vue    # [MODIFY] 移除Terminal，添加轮询
    ├── TestCaseGenerate.vue  # [MODIFY] 移除Terminal，添加轮询
    └── RequirementAnalysis.vue # [MODIFY] 移除Terminal，添加轮询
```

## 关键代码结构

```typescript
// aiTasks.ts API接口定义
interface TaskStatusResponse {
  task_id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  saved_ids?: number[]
  saved_count?: number
  error_message?: string
}

// 轮询逻辑示例
const pollInterval = ref<number | null>(null)

const startPolling = (taskId: string) => {
  pollInterval.value = window.setInterval(async () => {
    const result = await aiTasksApi.getRequirementTask(taskId)
    if (result.status === 'completed') {
      stopPolling()
      handleComplete(result)
    } else if (result.status === 'failed') {
      stopPolling()
      handleError(result.error_message)
    }
  }, 2000)
}

const stopPolling = () => {
  if (pollInterval.value) {
    clearInterval(pollInterval.value)
    pollInterval.value = null
  }
}
```