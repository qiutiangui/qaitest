"""
项目相关Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ProjectBase(BaseModel):
    """项目基础Schema"""
    name: str = Field(..., max_length=200, description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    status: str = Field(default="活跃", max_length=20, description="状态")


class ProjectCreate(ProjectBase):
    """创建项目Schema"""
    pass


class ProjectUpdate(BaseModel):
    """更新项目Schema"""
    name: Optional[str] = Field(None, max_length=200, description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    status: Optional[str] = Field(None, max_length=20, description="状态")


class ProjectResponse(ProjectBase):
    """项目响应Schema"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """项目列表响应"""
    total: int
    items: List[ProjectResponse]


class ProjectStatsResponse(BaseModel):
    """项目统计响应"""
    project_id: int
    version_count: int = Field(..., description="版本数量")
    requirement_count: int = Field(..., description="功能点数量")
    requirement_group_count: int = Field(..., description="需求数量（按requirement_name分组）")
    testcase_count: int = Field(..., description="测试用例数量")
    testplan_count: int = Field(..., description="测试计划数量")
