"""
版本管理API
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.models import ProjectVersion, VersionSnapshot
from app.schemas.version import (
    ProjectVersionCreate,
    ProjectVersionUpdate,
    ProjectVersionResponse,
    VersionSnapshotResponse,
)

router = APIRouter()


@router.get("")
async def list_versions(
    project_id: Optional[int] = Query(None, description="项目ID"),
    status: Optional[str] = Query(None, description="状态筛选"),
):
    """获取版本列表"""
    query = ProjectVersion.all()
    
    if project_id:
        query = query.filter(project_id=project_id)
    if status:
        query = query.filter(status=status)
    
    items = await query.order_by("-created_at")
    return {"items": [ProjectVersionResponse.model_validate(item) for item in items]}


@router.post("", response_model=ProjectVersionResponse)
async def create_version(data: ProjectVersionCreate):
    """创建版本"""
    version = await ProjectVersion.create(**data.model_dump())
    return ProjectVersionResponse.model_validate(version)


@router.get("/{version_id}", response_model=ProjectVersionResponse)
async def get_version(version_id: int):
    """获取版本详情"""
    version = await ProjectVersion.get_or_none(id=version_id).prefetch_related("project")
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")
    return ProjectVersionResponse.model_validate(version)


@router.put("/{version_id}", response_model=ProjectVersionResponse)
async def update_version(version_id: int, data: ProjectVersionUpdate):
    """更新版本"""
    version = await ProjectVersion.get_or_none(id=version_id)
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(version, key, value)
    
    await version.save()
    return ProjectVersionResponse.model_validate(version)


@router.delete("/{version_id}")
async def delete_version(version_id: int):
    """删除版本"""
    version = await ProjectVersion.get_or_none(id=version_id)
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")
    
    await version.delete()
    return {"message": "删除成功"}


@router.post("/{version_id}/release")
async def release_version(version_id: int):
    """发布版本"""
    version = await ProjectVersion.get_or_none(id=version_id)
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")
    
    version.status = "已发布"
    from datetime import datetime
    version.released_at = datetime.now()
    await version.save()
    
    return {"message": "发布成功", "version": ProjectVersionResponse.model_validate(version)}


@router.post("/{version_id}/archive")
async def archive_version(version_id: int):
    """归档版本"""
    version = await ProjectVersion.get_or_none(id=version_id)
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")
    
    version.status = "已归档"
    await version.save()
    
    return {"message": "归档成功", "version": ProjectVersionResponse.model_validate(version)}


@router.post("/{version_id}/snapshot", response_model=VersionSnapshotResponse)
async def create_snapshot(version_id: int, snapshot_type: str = Query(..., description="快照类型")):
    """创建版本快照"""
    version = await ProjectVersion.get_or_none(id=version_id)
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")
    
    # TODO: 实现快照数据生成逻辑
    snapshot = await VersionSnapshot.create(
        version_id=version_id,
        snapshot_type=snapshot_type,
        snapshot_data={},
    )
    
    return VersionSnapshotResponse.model_validate(snapshot)


@router.get("/{version_id}/snapshot")
async def get_snapshots(version_id: int):
    """获取版本快照列表"""
    snapshots = await VersionSnapshot.filter(version_id=version_id).order_by("-created_at")
    return {"items": [VersionSnapshotResponse.model_validate(s) for s in snapshots]}


@router.get("/compare/{version_a_id}/{version_b_id}")
async def compare_versions(version_a_id: int, version_b_id: int):
    """版本对比"""
    from app.services.version_service import VersionService
    
    try:
        result = await VersionService.compare_versions(version_a_id, version_b_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{version_id}/rollback")
async def rollback_version(version_id: int):
    """版本回溯"""
    from app.services.version_service import VersionService
    
    try:
        result = await VersionService.rollback_version(version_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{version_id}/changelog")
async def get_changelog(version_id: int):
    """获取版本变更日志"""
    version = await ProjectVersion.get_or_none(id=version_id)
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")
    
    # TODO: 实现变更日志生成逻辑
    changelog = {
        "version_id": version_id,
        "version_number": version.version_number,
        "entries": [
            {
                "type": "创建",
                "description": f"版本 {version.version_number} 已创建",
                "timestamp": version.created_at.isoformat() if version.created_at else None,
            }
        ]
    }
    
    return changelog


@router.post("/{version_id}/baseline")
async def create_baseline(version_id: int):
    """创建版本基线"""
    from app.services.version_service import VersionService
    
    try:
        snapshot = await VersionService.create_baseline(version_id)
        return VersionSnapshotResponse.model_validate(snapshot)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
