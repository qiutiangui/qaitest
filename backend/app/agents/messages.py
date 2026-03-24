"""
AutoGen 0.7.5 消息定义 - 使用Pydantic BaseModel

关键特性：
- 继承 BaseModel 以支持序列化和验证
- 使用 Field 增加字段描述
- 支持 AutoGen 消息传递协议
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


# ============ Topic 常量定义 ============
# 需求分析流水线 Topic
TOPIC_REQUIREMENT_INPUT = "requirement_input"
TOPIC_REQUIREMENT_ACQUIRE = "requirement_acquire"
TOPIC_REQUIREMENT_ANALYSIS = "requirement_analysis"
TOPIC_REQUIREMENT_OUTPUT = "requirement_output"

# 测试用例生成流水线 Topic
TOPIC_TESTCASE_INPUT = "testcase_input"
TOPIC_TESTCASE_GENERATE = "testcase_generate"
TOPIC_TESTCASE_REVIEW = "testcase_review"
TOPIC_TESTCASE_FINALIZE = "testcase_finalize"
TOPIC_TESTCASE_DATABASE = "testcase_database"


# ============ 需求分析消息类型 ============
class RequirementInputMessage(BaseModel):
    """需求分析输入消息"""
    task_id: str = Field(..., description="任务ID，用于WebSocket推送")
    project_id: Optional[int] = Field(None, description="项目ID")
    requirement_name: Optional[str] = Field(None, description="需求名称")
    document_content: str = Field(default="", description="文档内容")
    description: str = Field(default="", description="需求描述")
    version_id: Optional[int] = Field(default=None, description="版本ID")


class RequirementAcquiredMessage(BaseModel):
    """需求已获取消息"""
    task_id: str = Field(..., description="任务ID")
    project_id: Optional[int] = Field(None, description="项目ID")
    version_id: Optional[int] = Field(default=None, description="版本ID")
    requirement_name: Optional[str] = Field(default=None, description="需求名称")
    raw_content: str = Field(..., description="合并后的原始内容")
    document: str = Field(default="", description="文档内容")
    description: str = Field(default="", description="需求描述")
    stats: Dict[str, int] = Field(default_factory=dict, description="统计信息")
    chunk_count: int = Field(default=0, description="文档分块数量")


class RequirementAnalysisMessage(BaseModel):
    """需求分析消息"""
    task_id: str = Field(..., description="任务ID")
    project_id: Optional[int] = Field(None, description="项目ID")
    version_id: Optional[int] = Field(default=None, description="版本ID")
    requirement_name: Optional[str] = Field(default=None, description="需求名称")
    requirements: List[Dict[str, Any]] = Field(default_factory=list, description="提取的功能点列表")
    chunk_count: int = Field(default=0, description="文档分块数量")


class RequirementOutputMessage(BaseModel):
    """需求输出消息"""
    task_id: str = Field(..., description="任务ID")
    project_id: Optional[int] = Field(None, description="项目ID")
    version_id: Optional[int] = Field(default=None, description="版本ID")
    requirements: List[Dict[str, Any]] = Field(default_factory=list, description="功能点列表")
    chunk_count: int = Field(default=0, description="文档分块数量")


class RequirementCompleteMessage(BaseModel):
    """需求分析完成消息"""
    task_id: str = Field(..., description="任务ID")
    saved_ids: List[int] = Field(default_factory=list, description="保存成功的ID列表")
    failed_count: int = Field(default=0, description="失败数量")


# ============ 测试用例生成消息类型 ============
class TestCaseInputMessage(BaseModel):
    """测试用例生成输入消息"""
    task_id: str = Field(..., description="任务ID")
    project_id: Optional[int] = Field(None, description="项目ID")
    requirement_ids: List[int] = Field(..., description="功能点ID列表")
    version_id: Optional[int] = Field(default=None, description="版本ID")


class RequirementSelectMessage(BaseModel):
    """选中的需求消息（用于用例生成）"""
    task_id: str = Field(..., description="任务ID，用于WebSocket推送")
    id: int = Field(..., description="需求ID")
    name: str = Field(..., description="需求名称")
    description: str = Field(default="", description="需求描述")
    category: str = Field(default="", description="分类")
    module: str = Field(default="", description="所属模块")
    priority: str = Field(default="中", description="优先级")
    acceptance_criteria: str = Field(default="", description="验收标准")
    keywords: str = Field(default="", description="关键词")
    project_id: Optional[int] = Field(None, description="项目ID")
    task: str = Field(default="请根据需求描述生成测试用例", description="任务描述")


class TestCaseGeneratedMessage(BaseModel):
    """测试用例已生成消息"""
    task_id: str = Field(..., description="任务ID")
    requirement_id: int = Field(..., description="关联的需求ID")
    project_id: Optional[int] = Field(None, description="项目ID")
    test_cases: List[Dict[str, Any]] = Field(default_factory=list, description="生成的测试用例")
    creator: str = Field(default="AI", description="创建者，即生成测试用例的大模型名称")


class TestCaseReviewMessage(BaseModel):
    """测试用例评审消息"""
    task_id: str = Field(..., description="任务ID")
    project_id: Optional[int] = Field(None, description="项目ID")
    test_cases: str = Field(..., description="测试用例内容")
    review_report: str = Field(default="", description="评审报告")
    creator: str = Field(default="AI", description="创建者，即生成测试用例的大模型名称")


class TestCaseFinalizeMessage(BaseModel):
    """测试用例定稿消息"""
    task_id: str = Field(..., description="任务ID")
    project_id: Optional[int] = Field(None, description="项目ID")
    finalized_cases: str = Field(..., description="定稿后的测试用例JSON")
    creator: str = Field(default="AI", description="创建者，即生成测试用例的大模型名称")


class TestCaseCompleteMessage(BaseModel):
    """测试用例生成完成消息"""
    task_id: str = Field(..., description="任务ID")
    saved_ids: List[int] = Field(default_factory=list, description="保存成功的ID列表")
    total_count: int = Field(default=0, description="总用例数")


# ============ 通用消息类型 ============
class AgentLogMessage(BaseModel):
    """Agent日志消息（用于WebSocket推送）"""
    task_id: str = Field(..., description="任务ID")
    agent_name: str = Field(..., description="Agent名称")
    content: str = Field(..., description="消息内容")
    message_type: str = Field(default="thinking", description="消息类型: thinking/response/error/complete")
    extra_data: Optional[Dict[str, Any]] = Field(default=None, description="额外数据")
