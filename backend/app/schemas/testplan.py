"""
测试计划相关Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class TestPlanBase(BaseModel):
    """测试计划基础Schema"""
    name: str = Field(..., max_length=200, description="计划名称")
    description: Optional[str] = Field(None, description="计划描述")
    status: Optional[str] = Field(None, max_length=20, description="状态")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")


class TestPlanCreate(TestPlanBase):
    """创建测试计划Schema"""
    project_id: int = Field(..., description="项目ID")
    version_id: Optional[int] = Field(None, description="版本ID")


class TestPlanUpdate(BaseModel):
    """更新测试计划Schema"""
    name: Optional[str] = Field(None, max_length=200, description="计划名称")
    description: Optional[str] = Field(None, description="计划描述")
    status: Optional[str] = Field(None, max_length=20, description="状态")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")


class TestPlanCaseResponse(BaseModel):
    """测试计划用例关联响应Schema"""
    id: int
    test_plan_id: int
    test_case_id: int
    execution_status: str
    executed_at: Optional[datetime]
    executor: Optional[str]
    notes: Optional[str]
    
    class Config:
        from_attributes = True


class TestPlanResponse(TestPlanBase):
    """测试计划响应Schema"""
    id: int
    project_id: int
    version_id: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


class TestPlanDetailResponse(TestPlanResponse):
    """测试计划详情响应Schema"""
    test_plan_cases: Optional[List[TestPlanCaseResponse]] = None
    total_cases: int = 0
    passed_cases: int = 0
    failed_cases: int = 0
    blocked_cases: int = 0
    not_executed_cases: int = 0
    pass_rate: float = 0.0


class TestPlanListResponse(BaseModel):
    """测试计划列表响应"""
    total: int
    items: List[TestPlanResponse]


class ExecutionStatusUpdate(BaseModel):
    """执行状态更新Schema"""
    execution_status: str = Field(..., description="执行状态：未执行/通过/失败/阻塞")
    executor: Optional[str] = Field(None, max_length=50, description="执行人")
    notes: Optional[str] = Field(None, description="备注")
