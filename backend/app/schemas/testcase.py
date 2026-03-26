"""
测试用例相关Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from app.schemas.model_config import ModelConfigRequest


class TestStepBase(BaseModel):
    """测试步骤基础Schema"""
    step_number: int = Field(..., description="步骤序号")
    description: str = Field(..., description="步骤描述")
    expected_result: Optional[str] = Field(None, description="预期结果")


class TestStepCreate(TestStepBase):
    """创建测试步骤Schema"""
    pass


class TestStepResponse(TestStepBase):
    """测试步骤响应Schema"""
    id: int
    test_case_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class TestCaseBase(BaseModel):
    """测试用例基础Schema"""
    title: str = Field(..., max_length=500, description="用例标题")
    description: Optional[str] = Field(None, description="用例描述")
    priority: Optional[str] = Field(None, max_length=20, description="优先级")
    status: Optional[str] = Field(None, max_length=20, description="状态")
    test_type: Optional[str] = Field(None, max_length=50, description="测试类型")
    preconditions: Optional[str] = Field(None, description="前置条件")
    test_data: Optional[str] = Field(None, description="测试数据")


class TestCaseCreate(TestCaseBase):
    """创建测试用例Schema"""
    project_id: Optional[int] = Field(None, description="项目ID")
    requirement_id: Optional[int] = Field(None, description="功能点ID")
    version_id: Optional[int] = Field(None, description="版本ID")
    steps: Optional[List[TestStepCreate]] = Field(None, description="测试步骤")


class TestCaseUpdate(BaseModel):
    """更新测试用例Schema"""
    title: Optional[str] = Field(None, max_length=500, description="用例标题")
    description: Optional[str] = Field(None, description="用例描述")
    priority: Optional[str] = Field(None, max_length=20, description="优先级")
    status: Optional[str] = Field(None, max_length=20, description="状态")
    test_type: Optional[str] = Field(None, max_length=50, description="测试类型")
    preconditions: Optional[str] = Field(None, description="前置条件")
    test_data: Optional[str] = Field(None, description="测试数据")


class TestCaseResponse(TestCaseBase):
    """测试用例响应Schema"""
    id: int
    project_id: Optional[int]
    requirement_id: Optional[int]
    requirement_name: Optional[str] = Field(None, description="需求名称")
    version_id: Optional[int]
    creator: Optional[str] = Field(None, description="创建者")
    created_at: datetime
    steps: Optional[List[TestStepResponse]] = None
    
    class Config:
        from_attributes = True


class TestCaseListResponse(BaseModel):
    """测试用例列表响应"""
    total: int
    items: List[TestCaseResponse]


class TestCaseGenerateRequest(BaseModel):
    """测试用例生成请求Schema"""
    project_id: Optional[int] = Field(None, description="项目ID")
    requirement_ids: List[int] = Field(..., description="功能点ID列表")
    version_id: Optional[int] = Field(None, description="版本ID")
    task_id: Optional[str] = Field(None, description="任务ID（可选，不传则生成新ID，用于复用WebSocket连接）")

    # LLM配置
    llm_config: Optional[ModelConfigRequest] = Field(
        None,
        description="模型配置，不填则使用系统默认配置"
    )


# ============ 评审结论Schema ============
class ReviewIssue(BaseModel):
    """评审问题"""
    severity: str = Field(..., description="严重程度: high/medium/low")
    testcase_index: int = Field(..., description="用例索引")
    issue: str = Field(..., description="问题描述")
    suggestion: str = Field(..., description="改进建议")


class ReviewConclusion(BaseModel):
    """评审结论"""
    approved: bool = Field(..., description="是否通过")
    summary: str = Field(..., description="一句话总结")
    total_testcases: int = Field(..., description="测试用例总数")
    coverage_rate: str = Field(..., description="覆盖率")
    issues: List[ReviewIssue] = Field(default_factory=list, description="问题列表")
    suggestions: List[str] = Field(default_factory=list, description="整体建议")
