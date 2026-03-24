"""
项目管理API
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from loguru import logger
from tortoise.expressions import Q

from app.models import Project, Requirement, TestCase, TestPlan, ProjectVersion
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
    ProjectStatsResponse,
)

router = APIRouter()


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
):
    """获取项目列表"""
    query = Project.all()
    
    if keyword:
        query = query.filter(Q(name__contains=keyword) | Q(description__contains=keyword))
    
    total = await query.count()
    items = await query.offset((page - 1) * page_size).limit(page_size).order_by("-created_at")
    
    return ProjectListResponse(
        total=total,
        items=[ProjectResponse.model_validate(item) for item in items],
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int):
    """获取项目详情"""
    project = await Project.get_or_none(id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return ProjectResponse.model_validate(project)


@router.post("", response_model=ProjectResponse)
async def create_project(data: ProjectCreate):
    """创建项目"""
    project = await Project.create(**data.model_dump())
    return ProjectResponse.model_validate(project)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: int, data: ProjectUpdate):
    """更新项目"""
    project = await Project.get_or_none(id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)
    
    await project.save()
    return ProjectResponse.model_validate(project)


@router.delete("/{project_id}")
async def delete_project(project_id: int):
    """删除项目"""
    project = await Project.get_or_none(id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    await project.delete()
    return {"message": "删除成功"}


@router.get("/{project_id}/stats", response_model=ProjectStatsResponse)
async def get_project_stats(project_id: int):
    """获取项目统计信息"""
    from tortoise import Tortoise

    # 统计版本数量
    version_count = await ProjectVersion.filter(project_id=project_id).count()

    # 统计功能点数量
    requirement_count = await Requirement.filter(project_id=project_id).count()

    # 统计需求数量（按requirement_name分组）- 使用DISTINCT优化
    conn = Tortoise.get_connection("default")
    result = await conn.execute_query_dict(
        "SELECT COUNT(DISTINCT requirement_name) as cnt FROM `requirements` WHERE project_id = %s AND requirement_name IS NOT NULL",
        [project_id]
    )
    requirement_group_count = result[0]["cnt"] if result else 0

    # 统计测试用例数量
    testcase_count = await TestCase.filter(project_id=project_id).count()

    # 统计测试计划数量
    testplan_count = await TestPlan.filter(project_id=project_id).count()

    return ProjectStatsResponse(
        project_id=project_id,
        version_count=version_count,
        requirement_count=requirement_count,
        requirement_group_count=requirement_group_count,
        testcase_count=testcase_count,
        testplan_count=testplan_count,
    )
