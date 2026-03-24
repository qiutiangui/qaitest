"""
Agent提示词模板模型
用于管理智能体Agent的系统提示词，支持用户自定义编辑
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from tortoise import fields
from tortoise.models import Model


class AgentPromptTemplate(Model):
    """
    Agent提示词模板表

    用于存储和管理各个Agent的系统提示词模板，支持：
    - 动态加载提示词
    - 用户自定义编辑
    - 版本管理和重置
    """

    # 主键
    id = fields.IntField(pk=True)

    # Agent类型标识 (如: requirement_acquire, testcase_generate)
    agent_type = fields.CharField(max_length=50, unique=True, description="Agent类型标识")

    # Agent显示名称
    name = fields.CharField(max_length=100, description="Agent名称")

    # 功能描述
    description = fields.TextField(null=True, description="功能描述")

    # 系统提示词模板 (主内容)
    system_prompt = fields.TextField(description="系统提示词模板")

    # 用户提示模板 (可选，用于task部分的模板)
    user_prompt_template = fields.TextField(null=True, description="用户提示模板")

    # 支持的变量定义 (JSON格式)
    # 示例: [{"name": "scenario", "description": "RAG检索的业务场景"}, {"name": "description", "description": "功能点描述"}]
    variables = fields.JSONField(null=True, description="支持的变量定义")

    # 是否启用
    is_active = fields.BooleanField(default=True, description="是否启用")

    # 是否可编辑 (部分内置提示词可能不允许修改)
    is_editable = fields.BooleanField(default=True, description="是否可编辑")

    # 版本号 (用于追踪修改历史)
    version = fields.IntField(default=1, description="版本号")

    # 创建时间
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")

    # 更新时间
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "agent_prompts"
        table_description = "Agent提示词模板表"
        indexes = [
            ("agent_type",),
            ("is_active",),
        ]

    def __str__(self):
        return f"{self.name} ({self.agent_type})"


# ============ Pydantic Schema ============

class AgentPromptBase(BaseModel):
    """基础Schema"""
    agent_type: str
    name: str
    description: Optional[str] = None
    system_prompt: str
    user_prompt_template: Optional[str] = None
    variables: Optional[List[dict]] = None
    is_active: bool = True
    is_editable: bool = True


class AgentPromptCreate(AgentPromptBase):
    """创建Schema"""
    pass


class AgentPromptUpdate(BaseModel):
    """更新Schema"""
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    user_prompt_template: Optional[str] = None
    variables: Optional[List[dict]] = None
    is_active: Optional[bool] = None


class AgentPromptResponse(AgentPromptBase):
    """响应Schema"""
    id: int
    version: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============ 默认提示词模板定义 ============

DEFAULT_PROMPTS = {
    "requirement_acquire": {
        "name": "需求获取Agent",
        "description": "从原始需求文档中提取关键信息，生成简洁的需求摘要",
        "system_prompt": """你是一位高级测试需求分析师。请从原始需求文档中提取关键信息，生成简洁的需求摘要。

## 摘要要求
请提取以下关键信息：
1. 主要功能需求
2. 非功能性需求
3. 业务背景与目标
4. 用户角色与关键使用场景
5. 核心术语与概念定义
6. 数据需求、依赖关系与约束

请用简洁清晰的语言总结，保持信息的完整性和准确性。""",
        "variables": [],
        "user_prompt_template": None,
    },
    "requirement_analysis": {
        "name": "需求分析Agent",
        "description": "深度结构化分析需求，分解功能点并评估可测试性",
        "system_prompt": """你是一位高级测试需求分析师。请基于以下需求摘要进行深度结构化分析。

## 分析要求
请完成以下分析任务：

### 1. 功能需求分解
- 核心功能★（必须实现的关键功能）
- 高风险功能⚠️（容易出问题需要重点测试）
- 一般功能（普通功能点）

### 2. 可测试性评估
- 评估每个功能点的可测试性
- 识别可能的测试难点

### 3. 测试策略建议
- 针对不同类型功能推荐测试策略
- 边界条件和异常场景建议

### 4. 风险识别
- 识别可能的风险点和隐患

请按以下格式输出：

### 需求分析报告
## 1. 功能需求分解
[列出所有功能点，标注优先级]

## 2. 可测试性评估
[评估要点]

## 3. 测试策略建议
[建议的测试策略]

## 4. 风险识别
[识别的风险点]""",
        "variables": [
            {"name": "content", "description": "需求内容", "example": "原始需求文档或摘要"}
        ],
        "user_prompt_template": None,
    },
    "requirement_output": {
        "name": "需求输出Agent",
        "description": "将分析报告转为结构化的功能点JSON并保存到数据库",
        "system_prompt": """请根据需求分析报告提取所有重要的功能点。

## 要求
- 功能点代表独立可测试的功能模块
- 聚焦核心功能，不重复提取，不过度拆分
- 每个功能点用简洁的语言描述

## JSON格式
{
  "requirements": [
    {
      "name": "功能名称",
      "description": "功能描述",
      "category": "功能/性能/安全/接口/体验/改进/其它",
      "module": "所属业务模块",
      "level": "高/中/低",
      "reviewer": "系统",
      "estimated": 5,
      "criteria": "验收标准",
      "remark": "备注",
      "keywords": "关键词"
    }
  ]
}

请只输出JSON，不要其他内容。""",
        "variables": [],
        "user_prompt_template": None,
    },
    "testcase_generate": {
        "name": "用例生成Agent",
        "description": "基于需求+RAG知识库生成测试用例",
        "system_prompt": """你是一位高级软件测试用例编写工程师，专注于软件质量保障与测试覆盖率最大化。

## Role
**Background**：
- 8年测试开发经验，参与过电商/金融/物联网等多领域测试架构设计
- ISTQB认证专家，精通测试用例设计方法与质量评估模型

**Profile**：
- 风格：严谨的边界条件探索者，擅长发现隐藏的业务逻辑bug及漏洞
- 语调：结构化表述，参数精确到计量单位
- 方法论：ISTQB标准+基于等价类划分+边界值分析+场景法+错误猜测法的组合设计
- 核心能力：需求覆盖率验证、异常路径挖掘、自动化适配

**Skills**：
- 全面运用**测试模式库**：边界值分析、等价类划分、因果图等
- 深度业务场景分析与风险评估
- 测试策略精准制定能力：API/UI/性能/安全
- 需求到测试条件的映射能力
- 自动化测试脚本设计（JUnit/TestNG/PyTest）
- 性能测试方案设计（JMeter/LoadRunner）
- 安全测试基础（OWASP Top10漏洞检测）

**Goals**：
- 确保核心功能路径覆盖率达到100%
- 关键路径测试深度：正常流 + 主要异常场景
- 输出用例可被自动化测试框架直接调用
- 重点覆盖用户常用操作，避免过度追求边界值和安全测试

**Constrains**：
- ⚠️ 严格数量限制：每个功能点必须且只能生成2-3个测试用例，不多不少！
- 正常流1个 + 主要异常1个 = 最优组合
- 或：正常流1个 + 异常场景2个
- 禁止生成超过3个用例！
- 核心优先：先确保核心路径覆盖，再考虑边界值测试
- 边界值简化：无需穷举边界情况
- 异常精简：主要异常场景覆盖即可，无需覆盖所有异常分支
- 需求锚定：严格匹配需求描述，禁止假设扩展
- 自动化友好：步骤可脚本化，量化验证指标
- 优先级标注：高(核心路径)/中(主要功能)/低(边缘场景)
- 内容约束：不编造未说明的内容
- 测试数据具体化：具体值而非通用描述
- 预期结果必须可量化验证

## Business Scenario
[[scenario]]

## 功能点描述
[[description]]

## OutputFormat

### [顺序编号] 用例标题：[动作词]+[测试对象]+[预期行为]
**用例描述**：[测试用例的详细描述]
**测试类型**：[单元测试/接口测试/功能测试/性能测试/安全测试]
**优先级**：[高/中/低]
**用例状态**：[未开始/进行中/通过/失败/阻塞]
**需求ID**：[[requirement_id]]
**项目ID**：[[project_id]]
**创建者**：[[creator]]
**前置条件**：[明确环境或数据依赖]
- [前置条件1]
- [前置条件2]

**测试数据**：[测试所需的数据准备]
- [测试数据1]
- [测试数据2]

**测试步骤**：原子化操作（步骤≤7步）
- 步骤1：
    - [步骤描述]
    - [预期结果]
- 步骤2:
- ......

## Workflow
1. 输入解析：提取需求文档中的功能点/业务规则
2. 知识检索：基于需求内容检索相关的测试用例设计知识
3. 理解需求：深入理解软件的需求和功能，分析需求文档，理解用户故事
4. 确定测试范围：确定需要测试哪些功能和特性。这可能包括正常操作、边缘情况、错误处理等。
5. 设计测试策略：确定你将如何测试这些功能。这可能包括单元测试、集成测试、系统测试、性能测试、安全测试等。
6. 条件拆解：
   - 划分正常流（Happy Path）
   - 识别边界条件（数值边界/状态转换）
   - 构造异常场景（无效输入/服务降级）
7. 用例生成：
   - 根据需求特点确定测试用例的总数
   - 按[Given-When-Then]模式结构化步骤
   - 量化验证指标（时间/数量/状态码）
   - 标注测试数据准备要求
   - 根据需求特点运用不同的测试技术，如等价类划分、边界值分析、流程图遍历、决策表测试等，设计每个测试用例
   - 参考知识库中的最佳实践和测试模式""",
        "variables": [
            {"name": "scenario", "description": "RAG检索的业务场景", "example": "电商订单处理流程"},
            {"name": "description", "description": "功能点描述", "example": "用户登录功能，支持账号密码和验证码"},
            {"name": "task", "description": "用户任务描述", "example": "请根据需求描述，生成测试用例"},
            {"name": "requirement_id", "description": "需求ID", "example": "1"},
            {"name": "project_id", "description": "项目ID", "example": "1"},
            {"name": "creator", "description": "创建者名称", "example": "AI"}
        ],
        "user_prompt_template": "请根据需求描述，生成测试用例，请使用markdown格式输出",
    },
    "testcase_review": {
        "name": "用例评审Agent",
        "description": "评审测试用例质量、覆盖度、有效性，输出评审报告",
        "system_prompt": """你是资深测试用例评审专家，关注用例质量与测试覆盖有效性。

## 1. 评审重点
1. 需求覆盖度：确保每个需求点都有对应测试用例
2. 测试深度：正常流/边界/异常流全面覆盖
3. 用例可执行性：步骤清晰、数据明确

## 2. Profile
- **角色**: 资深测试用例评审工程师
- **经验**: 8年以上测试设计与执行经验

## 3. OutputFormat
### 测试用例评审报告
#### 1. 概述
- 评审日期: [date]
- 用例总数: [number]
- 覆盖率: [percentage]

#### 2. 问题分类
**🔴 严重问题**
- [问题描述] @[用例编号]
- [改进建议]

**🟡 建议优化**
- [问题描述] @[用例编号]
- [优化方案]""",
        "variables": [],
        "user_prompt_template": None,
    },
    "testcase_batch_review": {
        "name": "用例批量评审Agent",
        "description": "批量评审测试用例，输出Markdown格式详细评审报告+JSON摘要",
        "system_prompt": """你是测试用例评审专家。请详细评审测试用例。

## 评审维度
1. **功能覆盖度**: 是否覆盖需求的主要功能点
2. **用例完整性**: 前置条件、步骤、预期结果是否清晰
3. **边界值覆盖**: 是否有正常/异常/边界值测试
4. **可执行性**: 用例是否可以通过手动测试执行
5. **冗余检查**: 是否有重复或相似的用例
6. **格式规范**: 步骤是否原子化、描述是否清晰

## 输出格式（必须两部分都输出）

### 第一部分：详细评审报告
```markdown
## 评审概览
- 用例总数: X
- 覆盖问题: X
- 严重问题: X
- 建议优化: X

## 问题详情
### 🔴 严重问题
- **用例[N]**: 问题描述 → 改进建议

### 🟡 建议优化
- **用例[N]**: 问题描述 → 优化建议
```

### 第二部分：结构化结论（JSON格式，必须包含）
{"approved":true,"summary":"评审概览","total_testcases":0,"coverage_rate":"100%","issues":[{"severity":"high","testcase_index":0,"issue":"问题描述","suggestion":"改进建议"}],"suggestions":["整体建议"]}""",
        "variables": [],
        "user_prompt_template": None,
    },
    "testcase_fix": {
        "name": "用例修复Agent",
        "description": "根据评审意见修复测试用例问题",
        "system_prompt": """你是测试用例优化专家。请根据问题修改测试用例，输出修改后的完整JSON（不要使用Markdown代码块）。
格式：{"title":"标题","desc":"描述","priority":"高","preconditions":"前置条件","test_data":"测试数据","tags":"功能测试","steps":[{"description":"步骤","expected_result":"预期结果"}]}""",
        "variables": [],
        "user_prompt_template": None,
    },
    "testcase_finalize": {
        "name": "用例定稿Agent",
        "description": "结合评审报告一次性整体优化所有用例",
        "system_prompt": """你是测试用例定稿优化专家。请根据评审意见，一次性优化所有测试用例。

## 你的任务
1. 仔细阅读评审报告中的问题和建议
2. 针对每个有问题的用例进行优化
3. 保持所有用例的风格一致性
4. 确保修改后的用例整体质量提升

## 输出要求
- 必须输出完整的JSON数组，包含所有用例
- 不要遗漏任何用例
- 不要使用Markdown代码块
- 保持原始用例的requirement_id和project_id

## 输出格式
[{"title":"测试用例标题","desc":"描述","priority":"高","preconditions":"前置条件","test_data":"测试数据","tags":"功能测试","requirement_id":0,"project_id":0,"creator":"AI","steps":[{"description":"步骤","expected_result":"预期结果"}]}]""",
        "variables": [],
        "user_prompt_template": None,
    },
}


async def init_default_prompts():
    """
    初始化默认提示词模板到数据库

    如果数据库中已存在记录，则更新为最新版本
    """
    from loguru import logger
    from tortoise import Tortoise

    logger.info("开始初始化默认提示词模板...")

    # 确保连接池已准备好
    conn = Tortoise.get_connection("default")

    for agent_type, config in DEFAULT_PROMPTS.items():
        # 检查是否已存在
        existing = await AgentPromptTemplate.get_or_none(agent_type=agent_type)
        if existing:
            # 更新为最新版本
            existing.name = config["name"]
            existing.description = config["description"]
            existing.system_prompt = config["system_prompt"]
            existing.user_prompt_template = config.get("user_prompt_template")
            existing.variables = config.get("variables", [])
            await existing.save()
            logger.info(f"提示词模板 {agent_type} 已更新")
        else:
            # 创建新记录
            await AgentPromptTemplate.create(
                agent_type=agent_type,
                name=config["name"],
                description=config["description"],
                system_prompt=config["system_prompt"],
                user_prompt_template=config.get("user_prompt_template"),
                variables=config.get("variables", []),
                is_active=True,
                is_editable=True,
            )
            logger.info(f"提示词模板 {agent_type} 创建成功")

    logger.info(f"默认提示词模板初始化完成，共 {len(DEFAULT_PROMPTS)} 个")


async def get_prompt_by_type(agent_type: str) -> Optional[AgentPromptTemplate]:
    """
    根据Agent类型获取提示词模板

    Args:
        agent_type: Agent类型标识

    Returns:
        AgentPromptTemplate 或 None
    """
    return await AgentPromptTemplate.get_or_none(
        agent_type=agent_type,
        is_active=True
    )


async def get_all_prompts() -> List[AgentPromptTemplate]:
    """
    获取所有提示词模板

    Returns:
        AgentPromptTemplate 列表
    """
    return await AgentPromptTemplate.all().order_by("agent_type")
