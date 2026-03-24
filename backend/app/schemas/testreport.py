"""
测试报告相关Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class TestReportBase(BaseModel):
    """测试报告基础Schema"""
    title: str = Field(..., max_length=200, description="报告标题")
    report_type: Optional[str] = Field(default="执行报告", max_length=20, description="报告类型")
    summary: Optional[str] = Field(None, description="摘要")


class TestReportCreate(TestReportBase):
    """创建测试报告Schema"""
    test_plan_id: int = Field(..., description="测试计划ID")


class TestReportUpdate(BaseModel):
    """更新测试报告Schema"""
    title: Optional[str] = Field(None, max_length=200, description="报告标题")
    summary: Optional[str] = Field(None, description="摘要")
    status: Optional[str] = Field(None, max_length=20, description="状态")


class TestReportResponse(TestReportBase):
    """测试报告响应Schema"""
    id: int
    test_plan_id: int
    project_id: int
    version_id: Optional[int]
    total_cases: int
    passed_cases: int
    failed_cases: int
    blocked_cases: int
    not_executed_cases: int
    pass_rate: float
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    status: str
    created_by: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class TestReportListResponse(BaseModel):
    """测试报告列表响应"""
    total: int
    items: List[TestReportResponse]


class TestReportDetailResponse(TestReportResponse):
    """测试报告详情响应Schema"""
    execution_details: Optional[List[Dict[str, Any]]] = None
