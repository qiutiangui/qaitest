---
name: Runtime模式+并行处理+完整评审流程
overview: 需求分析使用 Runtime 模式，测试用例生成保持直接调用模式（保留完善的并行处理和评审逻辑）。确保 LlamaIndex 0.14.18 + AutoGen 0.7.5 架构标准。
todos:
  - id: enhance-rag-in-agent
    content: 在 RequirementAcquireAgent.handle_message 方法中补充完整的 RAG 索引逻辑（第477-490行），参考直接调用模式实现
    status: completed
  - id: switch-requirements-api
    content: 修改 requirements.py 第367行和第378行，切换到 run_requirement_analysis_with_runtime
    status: completed
    dependencies:
      - enhance-rag-in-agent
  - id: switch-batch-api
    content: 修改 requirements.py 第502行和第542行，批量分析 API 切换到 Runtime 模式
    status: completed
    dependencies:
      - enhance-rag-in-agent
  - id: switch-retry-api
    content: 修改 ai_tasks.py 第291行和第301行，需求分析重试 API 切换到 Runtime 模式
    status: completed
    dependencies:
      - enhance-rag-in-agent
  - id: delete-direct-mode
    content: 删除需求分析直接调用模式函数 run_requirement_analysis（第971-1283行），保留测试用例生成的并行优化版本
    status: completed
    dependencies:
      - switch-requirements-api
      - switch-batch-api
      - switch-retry-api
  - id: verify-no-references
    content: 使用 [subagent:code-explorer] 搜索所有 run_requirement_analysis 引用，确认彻底删除（不包括 run_testcase_generation）
    status: completed
    dependencies:
      - delete-direct-mode
  - id: restart-and-test
    content: 重启后端服务，测试完整流程：创建项目 → 上传文档 → 验证 RAG 索引日志 → 并行生成测试用例 → 验证评审流程
    status: completed
    dependencies:
      - verify-no-references
---

## 用户需求

用户发现日志显示"直接调用模式"，期望使用 AutoGen 0.7.5 的"Runtime模式"，并要求：

1. **确保技术栈版本正确**：LlamaIndex 0.14.18 + AutoGen 0.7.5
2. **保持测试用例生成的并行处理能力**
3. **保留完整的评审逻辑**：并行生成 → 汇总 → AI评审一次 → 修改一次 → 保存入库
4. **统一架构标准**：需求分析使用 Runtime 模式

## 产品概述

一个基于 LlamaIndex 0.14.18 + AutoGen 0.7.5 的混合架构系统：

- **需求分析流水线**：Runtime 模式（Agent 协作流程清晰）
- **测试用例生成流水线**：直接调用模式（性能优化，并行处理 + 完整评审流程）

## 核心功能

- **Runtime 模式架构**：需求分析使用 AutoGen 0.7.5 的 SingleThreadedAgentRuntime，消息驱动的 Agent 协作
- **RAG 索引集成**：在 RequirementAcquireAgent 中执行文档向量化，支持有项目和无项目两种情况
- **并行处理优化**：测试用例生成保留完善的并行处理逻辑（RAG 检索并行 + 生成并行）
- **完整评审流程**：测试用例生成保留完整的评审流程（AI评审一次 → 修改问题用例 → 保存入库）
- **API 端点分离**：需求分析 API 切换到 Runtime 模式，测试用例生成 API 保持直接调用模式

## Tech Stack

- **Backend Framework**: FastAPI 0.115.0
- **Multi-Agent Framework**: AutoGen 0.7.5 (autogen-agentchat, autogen-core, autogen_ext)
- **RAG Framework**: LlamaIndex 0.14.18 (llama-index-core, llama-index-readers-file, llama-index-vector-stores-milvus)
- **Vector Database**: Milvus 2.4.0+
- **Database**: Tortoise ORM + MySQL
- **LLM**: DeepSeek (via OpenAI-compatible API) + Qwen (via DashScope)
- **Logging**: Loguru 0.7.2

## Implementation Approach

### 混合架构方案

**需求分析 → Runtime 模式**：

- 切换到 `run_requirement_analysis_with_runtime`
- 在 RequirementAcquireAgent 中补充完整的 RAG 索引逻辑
- 删除需求分析的直接调用模式函数 `run_requirement_analysis`

**测试用例生成 → 直接调用模式（保留）**：

- 保留 `run_testcase_generation` 函数（第1068-1550行）
- 保留完整的评审流程：
- 阶段2：并行生成测试用例（asyncio.gather + Semaphore控制并发）
- 阶段3：AI评审一次（结构化JSON输出）
- 阶段4：修改有问题的用例（根据评审结果逐个修改）
- 阶段6：保存到数据库

### 关键技术决策

**为什么不统一使用 Runtime 模式？**

AutoGen 0.7.5 的 Runtime 架构适合 Agent 协作流程，但**不适合并行批处理**：

- Runtime 模式的测试用例生成（`run_testcase_generation_with_runtime`）是**串行处理**（第1027-1058行，逐个等待完成）
- Runtime 模式**缺少完整的评审流程**（评审、修改、定稿）
- 直接调用模式的测试用例生成有**完善的并行处理和评审流程**（第1068-1550行）

**为什么保留测试用例生成的直接调用模式？**

这不是代码冗余，而是**性能优化和功能完整性**的考虑：

- **并行处理**：RAG检索并行（最多2个并发）+ 生成并行（最多3个并发）
- **完整评审**：AI评审一次 → 修改问题用例 → 定稿入库
- **性能提升**：串行处理10分钟 → 并行处理2-3分钟

### 性能考虑

- **需求分析**：RAG索引在 RequirementAcquireAgent 中同步执行，不阻塞主流程
- **测试用例生成**：并行处理显著提升性能（RAG检索并行 + 生成并行）
- **文档分块参数**：chunk_size=500, overlap=100，平衡索引质量和性能
- **Milvus连接复用**：通过 `get_index_manager()` 单例模式复用连接

## Architecture Design

### 系统架构图

```mermaid
graph TB
    subgraph "API Layer"
        A[requirements.py]
        B[testcases.py]
        C[ai_tasks.py]
    end
    
    subgraph "Runtime Layer - 需求分析"
        D[SingleThreadedAgentRuntime]
        E[RequirementAcquireAgent]
        F[RequirementAnalysisAgent]
        G[RequirementOutputAgent]
    end
    
    subgraph "Direct Call Layer - 测试用例生成"
        H[run_testcase_generation]
        I[并行RAG检索]
        J[并行生成测试用例]
        K[AI评审一次]
        L[修改问题用例]
        M[保存入库]
    end
    
    subgraph "RAG Layer - LlamaIndex 0.14.18"
        N[get_index_manager]
        O[MilvusVectorStore]
        P[SentenceSplitter]
    end
    
    subgraph "External Services"
        Q[Milvus Vector DB]
        R[DeepSeek LLM]
        S[MySQL Database]
    end
    
    A -->|调用 Runtime| D
    C -->|调用 Runtime| D
    D -->|注册| E
    D -->|注册| F
    D -->|注册| G
    E -->|执行RAG索引| N
    N --> O
    O --> P
    O --> Q
    E -->|提取功能点| R
    G -->|保存功能点| S
    
    B -->|调用直接模式| H
    C -->|调用直接模式| H
    H --> I
    I --> J
    J --> K
    K --> L
    L --> M
    I --> N
    J --> R
    M -->|保存测试用例| S
```

### 测试用例生成完整流程

```mermaid
sequenceDiagram
    participant API as testcases.py
    participant Gen as run_testcase_generation
    participant RAG as 并行RAG检索
    participant LLM as 并行生成
    participant Review as AI评审
    participant Fix as 修改用例
    participant DB as MySQL
    
    API->>Gen: run_testcase_generation(requirement_ids)
    
    Note over Gen: 阶段1：输出功能点列表
    Gen->>Gen: 从数据库查询功能点
    
    Note over Gen,RAG: 阶段2：并行RAG检索
    Gen->>RAG: asyncio.gather(并行检索)
    RAG->>RAG: Semaphore(2) 控制并发
    RAG-->>Gen: 返回RAG上下文缓存
    
    Note over Gen,LLM: 阶段2：并行生成测试用例
    Gen->>LLM: asyncio.gather(并行生成)
    LLM->>LLM: Semaphore(3) 控制并发
    LLM-->>Gen: 返回所有测试用例
    
    Note over Gen,Review: 阶段3：AI评审一次
    Gen->>Review: 评审所有测试用例
    Review-->>Gen: 返回评审结论(JSON)
    
    Note over Gen,Fix: 阶段4：修改问题用例
    Gen->>Fix: 根据评审结果修改
    Fix-->>Gen: 返回修改后的用例
    
    Note over Gen,DB: 阶段6：保存入库
    Gen->>DB: 保存最终测试用例
    
    Gen-->>API: 返回 saved_ids
```

## Directory Structure

```
backend/
├── app/
│   ├── agents/
│   │   ├── requirement_agents.py  # [MODIFY] 增强 RequirementAcquireAgent RAG 索引逻辑，删除需求分析直接调用模式函数
│   │   ├── testcase_agents.py     # [KEEP] 保留直接调用模式（并行处理 + 完整评审流程）
│   │   └── runtime.py             # 无需修改
│   ├── api/
│   │   ├── requirements.py        # [MODIFY] 切换到 Runtime 模式（第367行、第378行、第502行、第542行）
│   │   ├── testcases.py           # [KEEP] 保持直接调用模式（第259行）
│   │   └── ai_tasks.py            # [MODIFY] 需求分析切换到 Runtime 模式（第291行、第301行）
│   ├── rag/
│   │   ├── llamaindex_manager.py  # 无需修改（已支持 project_id + task_id 双标识）
│   │   └── __init__.py            # 无需修改
│   └── models/
│       └── requirement.py         # 无需修改
└── requirements.txt               # 无需修改（已确认版本正确）
```

### 文件改动详情

#### 1. `backend/app/agents/requirement_agents.py` [MODIFY]

**改动1：增强 RequirementAcquireAgent 的 RAG 索引逻辑**

- **位置**：第477-490行
- **改动内容**：补充完整的 RAG 索引逻辑（参考直接调用模式第1055-1103行的实现）
- **功能**：
- 支持 project_id 和 task_id 双标识
- 执行文档分块和向量化
- 推送索引进度日志到前端
- 异常处理：RAG 索引失败不影响主流程

**改动2：删除需求分析直接调用模式函数**

- **位置**：第971-1283行
- **改动内容**：删除 `run_requirement_analysis` 函数（仅删除需求分析的直接调用模式）
- **注意**：保留 `run_testcase_generation` 函数（测试用例生成的并行优化版本）

#### 2. `backend/app/api/requirements.py` [MODIFY]

**改动1：单文档分析 API**

- **位置**：第367行、第378行
- **改动内容**：

```python
# 改前
from app.agents.requirement_agents import run_requirement_analysis
saved_ids = await run_requirement_analysis(...)

# 改后
from app.agents.requirement_agents import run_requirement_analysis_with_runtime
saved_ids = await run_requirement_analysis_with_runtime(...)
```

**改动2：批量分析 API**

- **位置**：第502行、第542行
- **改动内容**：同上，切换到 Runtime 模式

#### 3. `backend/app/api/ai_tasks.py` [MODIFY]

**改动：重试分析 API（仅需求分析部分）**

- **位置**：第291行、第301行（需求分析部分）
- **改动内容**：切换到 Runtime 模式
- **注意**：第376行（测试用例生成部分）保持直接调用模式

#### 4. `backend/app/api/testcases.py` [KEEP]

**保持不变**

- 第259行继续使用 `run_testcase_generation`（并行优化 + 完整评审流程）
- 不切换到 Runtime 模式（性能考虑）

## Key Code Structures

### RequirementAcquireAgent RAG 索引逻辑（参考实现）

```python
# backend/app/agents/requirement_agents.py
# RequirementAcquireAgent.handle_message 方法中，第477-490行之间插入

class RequirementAcquireAgent(RoutedAgent):
    async def handle_message(self, message: RequirementInputMessage, ctx: MessageContext):
        task_id = message.task_id
        
        # ========== 新增：RAG 索引步骤 ==========
        if message.document_content or message.description:
            try:
                await push_log(task_id, "RAGIndexAgent", "⏳ 正在创建文档向量索引...", "thinking")
                
                from app.rag import get_index_manager
                index_manager = await get_index_manager()
                
                rag_content = message.document_content if message.document_content else message.description
                index_result = await index_manager.index_requirement_document(
                    project_id=message.project_id,
                    task_id=task_id,  # 支持无项目情况
                    content=rag_content,
                    filename="requirement_document.md",
                    version_id=message.version_id,
                    requirement_name=message.requirement_name,
                    chunk_size=500,
                    overlap=100
                )
                
                if index_result.get("success"):
                    chunk_count = index_result.get('indexed', 0)
                    await push_log(
                        task_id, 
                        "RAGIndexAgent", 
                        f"✅ 文档索引完成：{chunk_count} 个文本块已存入向量数据库", 
                        "response"
                    )
                else:
                    await push_log(
                        task_id, 
                        "RAGIndexAgent", 
                        f"⚠️ 文档索引跳过：{index_result.get('error', '未知错误')}", 
                        "thinking"
                    )
            except Exception as e:
                logger.warning(f"RAG索引失败（不影响需求分析）: {e}")
                await push_log(task_id, "RAGIndexAgent", f"⚠️ RAG索引失败：{e}", "thinking")
        
        # 继续原有的需求获取流程...
```

### Runtime 模式调用方式（需求分析）

```python
# backend/app/api/requirements.py

from app.agents.requirement_agents import run_requirement_analysis_with_runtime

saved_ids = await run_requirement_analysis_with_runtime(
    task_id=task_id,
    project_id=project_id,
    requirement_name=requirement_name,
    document_content=document_content,
    description=description,
    version_id=version_id,
    input_func=input_func,  # 可选：用户输入函数（用于交互式模式）
)
```

### 直接调用模式调用方式（测试用例生成，保持不变）

```python
# backend/app/api/testcases.py

from app.agents.testcase_agents import run_testcase_generation

await run_testcase_generation(
    task_id=task_id,
    project_id=data.project_id,
    requirement_ids=data.requirement_ids,
    version_id=data.version_id,
    llm_config=data.llm_config,
)
```

### SubAgent

- **code-explorer**
- Purpose: 搜索所有引用 `run_requirement_analysis` 的位置（不包括 `run_testcase_generation`），确保需求分析切换到 Runtime 模式
- Expected outcome: 确认需求分析 API 端点都已切换到 Runtime 模式，测试用例生成 API 保持直接调用模式