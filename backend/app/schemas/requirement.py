"""
功能点（需求）相关Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class RequirementBase(BaseModel):
    """功能点基础Schema"""
    requirement_name: Optional[str] = Field(None, max_length=200, description="需求名称")
    name: str = Field(..., max_length=500, description="功能点名称")
    description: Optional[str] = Field(None, description="功能点描述")
    category: Optional[str] = Field(None, max_length=50, description="类别")
    module: Optional[str] = Field(None, max_length=100, description="所属模块")
    priority: Optional[str] = Field(None, max_length=10, description="优先级")
    acceptance_criteria: Optional[str] = Field(None, description="验收标准")
    keywords: Optional[str] = Field(None, max_length=500, description="关键词")


class RequirementCreate(RequirementBase):
    """创建功能点Schema"""
    project_id: Optional[int] = Field(None, description="项目ID")
    version_id: Optional[int] = Field(None, description="版本ID")


class RequirementUpdate(BaseModel):
    """更新功能点Schema"""
    requirement_name: Optional[str] = Field(None, max_length=200, description="需求名称")
    name: Optional[str] = Field(None, max_length=500, description="功能点名称")
    description: Optional[str] = Field(None, description="功能点描述")
    category: Optional[str] = Field(None, max_length=50, description="类别")
    module: Optional[str] = Field(None, max_length=100, description="所属模块")
    priority: Optional[str] = Field(None, max_length=10, description="优先级")
    acceptance_criteria: Optional[str] = Field(None, description="验收标准")
    keywords: Optional[str] = Field(None, max_length=500, description="关键词")


class RequirementResponse(RequirementBase):
    """功能点响应Schema"""
    id: int
    project_id: Optional[int]
    version_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class RequirementListResponse(BaseModel):
    """功能点列表响应"""
    total: int
    items: List[RequirementResponse]


class RequirementGroupResponse(BaseModel):
    """需求分组响应Schema"""
    requirement_name: Optional[str]
    project_id: Optional[int]
    version_id: Optional[int]
    count: int
    created_at: datetime
