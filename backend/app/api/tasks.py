"""
任务管理API - 查询异步任务历史和状态
"""
from fastapi import APIRouter, Query
from typing import List, Optional
from loguru import logger
from app.models import AITestTask, Project

router = APIRouter(tags=["任务管理"])


def _serialize_task(task: AITestTask, project_name: str = None) -> dict:
    """统一序列化单个任务"""
    # 计算 saved_count / total_count（按阶段映射）
    if task.requirement_phase_status and task.requirement_phase_status != "pending":
        saved_count = task.saved_requirements or 0
        total_count = task.total_requirements or 0
    else:
        saved_count = task.saved_testcases or 0
        total_count = task.total_testcases or 0

    # 汇总 phases_summary（从 task.phases 转换）
    phases_summary = []
    phases = []
    if task.phases and isinstance(task.phases, list):
        for phase in task.phases:
            phases_summary.append({
                "code": phase.get("code", ""),
                "name": phase.get("name", ""),
                "status": phase.get("status", "pending"),
                "progress": phase.get("progress", 0),
            })
            phases.append(phase)
    elif task.current_phase:
        # 兜底：至少显示当前阶段
        phases_summary.append({
            "code": task.current_phase_code or "",
            "name": task.current_phase,
            "status": task.status,
            "progress": task.progress,
        })

    # 从 task.result 读取耗时和文档分块
    duration_seconds = 0
    doc_chunk_count = 0
    if task.result and isinstance(task.result, dict):
        duration_seconds = task.result.get("duration", 0)
        doc_chunk_count = task.result.get("doc_chunk_count", 0)

    return {
        "id": task.id,
        "task_id": task.task_id,
        "project_id": task.project_id,
        "project_name": project_name,
        "task_name": task.task_name,
        "requirement_name": task.task_name,
        "status": task.status,
        "progress": task.progress,
        "current_phase": task.current_phase,
        "phases_summary": phases_summary,
        "phases": phases,
        "total_count": total_count,
        "saved_count": saved_count,
        "doc_chunk_count": doc_chunk_count,
        "stats": {
            "duration_seconds": duration_seconds,
        },
        "error_message": task.error_message,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
    }


@router.get("/list")
async def list_tasks(
    user_id: Optional[str] = None,
    task_type: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
):
    """
    获取任务列表
    """
    query = AITestTask.all()

    if status:
        query = query.filter(status=status)

    total = await query.count()
    tasks = await query.offset((page - 1) * page_size).limit(page_size).order_by("-created_at")

    # 批量查询项目名称
    project_ids = {t.project_id for t in tasks if t.project_id}
    project_map = {}
    if project_ids:
        projects = await Project.filter(id__in=project_ids)
        project_map = {p.id: p.name for p in projects}

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            _serialize_task(task, project_map.get(task.project_id))
            for task in tasks
        ]
    }


@router.get("/{task_id}")
async def get_task(task_id: str):
    """
    获取单个任务详情
    """
    task = await AITestTask.get_or_none(task_id=task_id)
    if not task:
        return {"error": "任务不存在"}

    project_name = None
    if task.project_id:
        project = await Project.get_or_none(id=task.project_id)
        if project:
            project_name = project.name

    return _serialize_task(task, project_name)


@router.post("/{task_id}/retry")
async def retry_task(task_id: str):
    """
    重试失败的任务
    """
    task = await AITestTask.get_or_none(task_id=task_id)
    if not task:
        return {"error": "任务不存在"}
    
    task.status = "pending"
    task.error_message = None
    await task.save()
    
    return {"message": "任务已重新排队"}


@router.delete("/{task_id}")
async def delete_task(task_id: str):
    """
    删除任务记录
    """
    task = await AITestTask.get_or_none(task_id=task_id)
    if not task:
        return {"error": "任务不存在"}
    
    # 不允许删除正在运行的任务
    if task.status == "running":
        return {"error": "无法删除正在运行的任务"}
    
    await task.delete()
    return {"message": "任务已删除"}
