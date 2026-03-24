# 用例生成效率优化计划

## 📊 当前问题

```
现有流程（4个Agent串联）：
文档 → RequirementAcquireAgent（摘要）→ RequirementAnalysisAgent（分析报告）
        → RequirementOutputAgent（提取功能点）→ 保存到数据库

用例生成：
功能点 → 检索历史用例 → RAG检索 → LLM生成 → 评审 → 入库
```

**问题**：
1. **Agent 过多**：3个Agent串联处理文档
2. **不必要的中间步骤**：摘要、分析报告 → 功能点
3. **RAG 落库开销**：文档分块、向量化、存储（单文档场景价值不大）
4. **评审作用不明显**：维度少，前端只显示summary，无人工确认

---

## 🎯 优化目标

| 指标 | 当前 | 优化后 |
|------|------|--------|
| Agent数量 | 3个串联 | 1个完成 |
| 文档处理 | 摘要→分析报告→功能点 | 一步到位 |
| RAG落库 | 文档分块→向量化→存储 | 可选/跳过 |
| 评审 | 单维度+无确认 | 多维度+人工确认 |
| Token消耗 | 较高 | 降低30%+ |

---

## 📝 优化方案

### 1. 合并文档处理Agent（3→1）

**当前流程**：
```
RequirementAcquireAgent（摘要）
    ↓
RequirementAnalysisAgent（分析报告）
    ↓
RequirementOutputAgent（提取功能点+保存）
```

**优化后**：
```
SingleRequirementAgent（一步完成）
    - 读取文档
    - 直接提取功能点JSON
    - 保存到数据库
```

**优化效果**：
- LLM调用：3次 → 1次
- Token消耗：大幅减少
- 延迟：减少2次网络开销

---

### 2. 优化Prompt设计

**当前Prompt（3个分离的Agent）**：
```python
# Agent1: 摘要
"请分析以下需求文档，输出结构化摘要..."

# Agent2: 分析报告
"根据摘要，进行深度分析，输出风险评估..."

# Agent3: 功能点提取
"根据分析报告，生成JSON格式的功能点..."
```

**优化Prompt（1个Agent）**：
```python
SYSTEM_PROMPT = """
你是一个专业的软件测试需求分析师。请直接从原始需求文档中提取功能点。

## 输入
- 需求文档内容（可能包含需求名称、描述、功能点列表等）

## 任务
1. 理解需求文档的核心功能
2. 提取所有可测试的功能点
3. 为每个功能点生成结构化的JSON

## 输出要求
必须输出一个有效的JSON对象，不要包含任何解释或前导文本：

{
  "requirements": [
    {
      "name": "功能点名称",
      "description": "明确的功能点描述",
      "category": "功能/性能/安全/接口/体验/改进/其它",
      "module": "所属模块",
      "priority": "高/中/低",
      "acceptance_criteria": "验收标准",
      "keywords": "关键词,逗号分隔"
    }
  ]
}

## 提取原则
- 功能点应该覆盖文档中所有可测试的需求
- 描述要具体、可操作
- 优先级根据功能重要性判断
- 一个需求可以拆分为多个功能点
"""
```

---

### 3. 去掉RAG落库（可选）

**当前流程**：
```
文档 → 分块(500字) → 向量化 → 存储到Milvus
```

**优化后**：
```
文档 → 直接传给LLM提取功能点（跳过RAG）
```

**适用场景**：
- ✅ 单个需求文档（<50K tokens）
- ✅ 不需要跨文档检索
- ❌ 多文档知识库（保留RAG）

**配置项**：
```python
# config.py
class Settings:
    skip_rag_indexing: bool = True  # 单文档跳过RAG落库
    rag_enabled_for_multidoc: bool = True  # 多文档仍使用RAG
```

---

### 4. 增强评审环节

**当前评审**：
```python
{
  "approved": true,
  "summary": "一句话总结",  # 只有一个摘要
  "coverage_rate": "100%"
}
```

**优化后评审**：
```python
{
  "approved": true,
  "summary": "一句话总结",
  "dimensions": {
    "coverage": {
      "score": 85,
      "issues": ["边界值覆盖不足", "异常场景缺失"]
    },
    "boundary": {
      "score": 70,
      "issues": ["未考虑空值情况"]
    },
    "specificity": {
      "score": 90,
      "issues": []
    }
  },
  "total_testcases": 15,
  "coverage_rate": "95%",
  "issues": [
    {
      "severity": "high",
      "testcase_index": 3,
      "issue": "前置条件不完整",
      "suggestion": "应补充登录状态的说明"
    }
  ],
  "suggestions": [
    "建议增加2个边界值测试用例",
    "异常场景需要补充"
  ]
}
```

**人工确认流程**：
```
评审完成 → 前端展示详细问题 → 用户选择：
  - 直接入库
  - 修改后入库
  - 补充要求后重新生成
```

---

## 🔧 实施步骤

### 阶段1：简化文档处理（高优先级）

1. 创建 `SingleRequirementAgent`
   - 合并3个Agent的逻辑
   - 单次LLM调用完成功能点提取
   - 直接保存到数据库

2. 修改API入口
   - `/api/requirements/analyze` 改用新Agent
   - 保持WebSocket输出兼容

### 阶段2：优化Prompt（高优先级）

1. 设计高效的提取Prompt
   - Few-shot示例
   - 清晰的输出格式要求
   - 避免过度分析的指令

2. 添加错误处理和降级策略
   - JSON解析失败时降级为文本提取
   - 部分成功时的容错处理

### 阶段3：RAG优化（中优先级）

1. 添加配置项控制
   - 小文档跳过RAG落库
   - 大文档可选择是否落库

2. 评估RAG价值
   - 对比有无RAG的生成效果
   - 决定是否完全移除

### 阶段4：增强评审（中优先级）

1. 多维度评分
   - 覆盖度、边界值、异常、数据具体性

2. 人工确认UI
   - 展示问题列表
   - 提供选择按钮

3. 修改迭代
   - 用户补充要求
   - AI重新生成

---

## 📁 需要修改的文件

| 文件 | 修改内容 |
|------|---------|
| `app/agents/requirement_agents.py` | 重构/新增SingleRequirementAgent |
| `app/agents/testcase_agents.py` | 增强评审逻辑 |
| `app/config.py` | 添加RAG配置项 |
| `app/api/requirements.py` | 适配新Agent |
| `app/schemas/requirement.py` | 更新输出格式 |

---

## ⏱️ 时间估算

| 阶段 | 任务 | 优先级 |
|------|------|--------|
| 阶段1 | 简化文档处理（3→1 Agent） | 🔴 高 |
| 阶段2 | 优化Prompt | 🔴 高 |
| 阶段3 | RAG优化 | 🟡 中 |
| 阶段4 | 增强评审 | 🟡 中 |

---

## ✅ 验收标准

- [ ] 文档处理从3次LLM调用减少到1次
- [ ] 功能点提取质量不下降
- [ ] Token消耗降低30%以上
- [ ] 评审展示多维度评分
- [ ] 支持人工确认流程
- [ ] 现有功能不受影响（向后兼容）
