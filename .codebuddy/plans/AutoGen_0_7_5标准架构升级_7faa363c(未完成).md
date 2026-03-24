---
name: AutoGen 0.7.5标准架构升级
overview: 将AutoGen多智能体代码升级为0.7.5标准写法，引入Topic订阅、Runtime机制、AssistantAgent、Memory管理等特性，实现松耦合的智能体间通信。
todos:
  - id: update-messages
    content: 更新消息定义：使用Pydantic BaseModel替代dataclass，添加序列化支持
    status: pending
  - id: create-topics
    content: 创建Topic常量文件：定义需求分析和用例生成流水线的Topic
    status: pending
    dependencies:
      - update-messages
  - id: update-llm-client
    content: 更新LLM客户端：集成OpenAIChatCompletionClient支持DeepSeek API
    status: pending
  - id: create-runtime-manager
    content: 创建Runtime管理器：封装SingleThreadedAgentRuntime，实现Agent注册和消息发布
    status: pending
    dependencies:
      - update-llm-client
  - id: update-requirement-agents
    content: 重构需求分析Agent：添加@type_subscription、Topic订阅、AssistantAgent、ListMemory、流式处理
    status: pending
    dependencies:
      - create-runtime-manager
      - create-topics
  - id: update-testcase-agents
    content: 重构用例生成Agent：添加@type_subscription、Topic订阅、AssistantAgent、ListMemory、流式处理
    status: pending
    dependencies:
      - create-runtime-manager
      - create-topics
  - id: update-api-integration
    content: 更新API集成：修改run_requirement_analysis和run_testcase_generation使用Runtime模式
    status: pending
    dependencies:
      - update-requirement-agents
      - update-testcase-agents
  - id: test-integration
    content: 测试集成：验证流水线完整性和向后兼容性
    status: pending
    dependencies:
      - update-api-integration
---

## 用户需求

1. **AutoGen版本升级检查**：确保代码符合AutoGen 0.7.5标准写法
2. **智能体间信息交互优化**：

- Topic订阅机制（`@type_subscription`装饰器）
- Runtime注册机制（`register()`方法）
- AssistantAgent集成
- ListMemory对话历史管理
- 流式处理（`run_stream()`）

## 核心差异分析

| 特性 | 参考代码（0.7.5标准） | 当前代码 |
| --- | --- | --- |
| Topic订阅 | `@type_subscription(topic_type="xxx")` | 缺失 |
| 消息传递 | `publish_message()` + `TopicId` | 直接方法调用 |
| Runtime | `SingleThreadedAgentRuntime` 注册Agent | 绕过Runtime |
| LLM调用 | `AssistantAgent` + `OpenAIChatCompletionClient` | 自定义LLMClient |
| Memory | `ListMemory` 存储对话历史 | 缺失 |
| 流式处理 | `run_stream()` + 事件类型判断 | 直接调用 |


## 功能目标

- 实现智能体间松耦合通信
- 支持流式输出到前端WebSocket
- 支持对话历史管理和上下文保持
- 完全符合AutoGen 0.7.5标准
- 保持API向后兼容

## 技术栈

- AutoGen 0.7.5：`autogen-agentchat`, `autogen-core`, `autogen-ext`
- LLM：DeepSeek API（通过OpenAIChatCompletionClient）
- 消息格式：Pydantic BaseModel
- 内存管理：ListMemory + MemoryContent
- 流式处理：`run_stream()` + 事件类型判断

## 实现方案

### 1. Topic订阅机制

定义Topic常量和消息流向：

```python
# 需求分析流水线Topic
REQUIREMENT_ACQUIRE = "requirement_acquire"
REQUIREMENT_ANALYSIS = "requirement_analysis"
REQUIREMENT_OUTPUT = "requirement_output"

# 用例生成流水线Topic
CASE_GENERATE = "case_generate"
CASE_REVIEW = "case_review"
CASE_FINALIZE = "testcase_finalize"
CASE_DATABASE = "case_in_database"
```

### 2. Runtime集成

创建`AgentRuntimeManager`封装`SingleThreadedAgentRuntime`：

```python
from autogen_core import SingleThreadedAgentRuntime, TopicId, DefaultTopicId

class AgentRuntimeManager:
    def __init__(self):
        self.runtime = SingleThreadedAgentRuntime()
    
    async def register_agent(self, agent_class, agent_name: str, factory):
        await agent_class.register(self.runtime, agent_name, factory)
    
    async def publish_message(self, message, topic_type: str, source: str = "system"):
        await self.runtime.publish_message(
            message,
            topic_id=TopicId(type=topic_type, source=source)
        )
    
    def start(self):
        self.runtime.start()
    
    async def stop_when_idle(self):
        await self.runtime.stop_when_idle()
```

### 3. AssistantAgent集成

使用AutoGen的标准AssistantAgent替代自定义LLMClient：

```python
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

# 配置DeepSeek模型客户端
model_client = OpenAIChatCompletionClient(
    model="deepseek-chat",
    base_url="https://api.deepseek.com/v1",
    api_key=settings.deepseek_api_key,
    model_info={
        "vision": False,
        "function_calling": True,
        "json_output": True,
        "family": "unknown",
    }
)

# 创建AssistantAgent
agent = AssistantAgent(
    name="requirement_analyst",
    model_client=model_client,
    system_message="...",
    model_client_stream=True  # 启用流式输出
)
```

### 4. Memory管理

添加ListMemory支持对话历史：

```python
from autogen_core.memory import ListMemory, MemoryContent, MemoryMimeType

memory = ListMemory()

# 保存消息到内存
await memory.add(
    MemoryContent(
        content=msg.model_dump_json(),
        mime_type=MemoryMimeType.JSON
    )
)

# 在Agent中使用memory
agent = AssistantAgent(
    name="summarize_agent",
    model_client=model_client,
    memory=[memory],  # 传入记忆
    system_message="..."
)
```

### 5. 流式处理

使用`run_stream()`处理LLM响应：

```python
from autogen_agentchat.base import TaskResult
from autogen_agentchat.messages import ModelClientStreamingChunkEvent, TextMessage

stream = agent.run_stream(task=prompt)
async for msg in stream:
    if isinstance(msg, ModelClientStreamingChunkEvent):
        # 流式输出到前端
        await push_log(task_id, agent_name, msg.content, "streaming")
    elif isinstance(msg, TaskResult):
        # 最终结果
        result = msg.messages[-1].content
```

### 6. 向后兼容

保留便捷函数，内部使用Runtime机制：

```python
async def run_requirement_analysis(...) -> List[int]:
    """保持API兼容，内部使用Runtime"""
    runtime_manager = AgentRuntimeManager()
    
    # 注册所有Agent
    await runtime_manager.register_agent(
        RequirementAcquireAgent, 
        "requirement_acquire_agent",
        lambda: RequirementAcquireAgent()
    )
    # ... 注册其他Agent
    
    runtime_manager.start()
    
    # 发布初始消息
    await runtime_manager.publish_message(
        input_message,
        topic_type=REQUIREMENT_ACQUIRE
    )
    
    await runtime_manager.stop_when_idle()
    
    # 返回结果
    return saved_ids
```

## 目录结构

```
backend/app/agents/
├── __init__.py
├── messages.py          # [MODIFY] 使用Pydantic BaseModel
├── runtime.py           # [MODIFY] 添加AgentRuntimeManager
├── requirement_agents.py # [MODIFY] 添加@type_subscription
├── testcase_agents.py   # [MODIFY] 添加@type_subscription
├── topics.py            # [NEW] Topic常量定义
└── llm.py               # [NEW] LLM客户端配置
```

## 关键代码结构

### Topic定义（topics.py）

```python
# 需求分析流水线
REQUIREMENT_ACQUIRE = "requirement_acquire"
REQUIREMENT_ANALYSIS = "requirement_analysis"
REQUIREMENT_OUTPUT = "requirement_output"

# 用例生成流水线
CASE_GENERATE = "case_generate"
CASE_REVIEW = "case_review"
CASE_FINALIZE = "testcase_finalize"
CASE_DATABASE = "case_in_database"
```

### 消息基类（messages.py）

```python
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class RequirementMessage(BaseModel):
    """需求消息"""
    task_id: str
    project_id: int
    content: Any
    source: str
    
class TestCaseMessage(BaseModel):
    """测试用例消息"""
    task_id: str
    content: Any
    source: str
```

## Agent Extensions

### SubAgent

- **code-explorer**
- Purpose: 探索代码库结构，查找相关文件和依赖
- Expected outcome: 快速定位需要修改的文件和参考实现