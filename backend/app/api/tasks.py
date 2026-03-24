"""
任务管理API - 查询异步任务历史和状态
"""
from fastapi import APIRouter, Query
from typing import List, Optional
from loguru import logger
from app.models import AITestTask

router = APIRouter(tags=["任务管理"])


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
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": task.id,
                "task_id": task.task_id,
                "project_id": task.project_id,
                "task_name": task.task_name,
                "status": task.status,
                "progress": task.progress,
                "current_phase": task.current_phase,
                "error_message": task.error_message,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "updated_at": task.updated_at.isoformat() if task.updated_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            }
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
    
    return {
        "id": task.id,
        "task_id": task.task_id,
        "project_id": task.project_id,
        "task_name": task.task_name,
        "status": task.status,
        "progress": task.progress,
        "current_phase": task.current_phase,
        "requirement_phase_status": task.requirement_phase_status,
        "testcase_phase_status": task.testcase_phase_status,
        "error_message": task.error_message,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
    }


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
