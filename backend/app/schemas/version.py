"""
版本管理相关Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ProjectVersionBase(BaseModel):
    """版本基础Schema"""
    version_number: str = Field(..., max_length=20, description="版本号")
    version_name: Optional[str] = Field(None, max_length=200, description="版本名称")
    description: Optional[str] = Field(None, description="版本描述")
    status: str = Field(default="开发中", max_length=20, description="状态")
    release_notes: Optional[str] = Field(None, description="发布说明")


class ProjectVersionCreate(ProjectVersionBase):
    """创建版本Schema"""
    project_id: int = Field(..., description="项目ID")


class ProjectVersionUpdate(BaseModel):
    """更新版本Schema"""
    version_name: Optional[str] = Field(None, max_length=200, description="版本名称")
    description: Optional[str] = Field(None, description="版本描述")
    status: Optional[str] = Field(None, max_length=20, description="状态")
    release_notes: Optional[str] = Field(None, description="发布说明")


class ProjectVersionResponse(ProjectVersionBase):
    """版本响应Schema"""
    id: int
    project_id: int
    is_baseline: bool
    created_by: Optional[str]
    released_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class VersionSnapshotResponse(BaseModel):
    """版本快照响应Schema"""
    id: int
    version_id: int
    snapshot_type: str
    snapshot_data: Dict[str, Any]
    created_at: datetime
    
    class Config:
        from_attributes = True


class VersionCompareResponse(BaseModel):
    """版本对比响应Schema"""
    version_a: ProjectVersionResponse
    version_b: ProjectVersionResponse
    requirement_changes: Dict[str, Any]
    testcase_changes: Dict[str, Any]
    execution_changes: Dict[str, Any]
