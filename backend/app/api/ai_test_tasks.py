"""
AI测试任务API - 统一的需求分析和用例生成
"""
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form, Body
from typing import Optional, List
from pydantic import BaseModel
import uuid
import asyncio
from datetime import datetime
from loguru import logger

from app.models import AITestTask, Project, Requirement, TestCase

router = APIRouter(tags=["AI测试任务"])


# ============ 请求/响应模型 ============

class AITestTaskCreate(BaseModel):
    """创建AI测试任务请求"""
    project_id: Optional[int] = None
    version_id: Optional[int] = None
    task_name: Optional[str] = None
    description: str = ""
    input_source: str = "description"  # file/feishu/description
    input_filename: Optional[str] = None
    generation_model: Optional[str] = None
    review_model: Optional[str] = None


class AITestTaskResponse(BaseModel):
    """AI测试任务响应"""
    id: int
    task_id: str
    project_id: Optional[int]
    version_id: Optional[int]
    task_name: Optional[str]
    status: str
    progress: int
    
    requirement_phase_status: str
    requirement_phase_progress: int
    total_requirements: int
    saved_requirements: int
    
    testcase_phase_status: str
    testcase_phase_progress: int
    total_testcases: int
    saved_testcases: int
    
    current_phase: Optional[str]
    current_phase_code: Optional[str]
    phases: Optional[List[dict]]
    
    error_message: Optional[str]
    logs: Optional[List[dict]]
    
    created_at: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]
    
    project_name: Optional[str] = None


class AITestTaskListResponse(BaseModel):
    """任务列表响应"""
    total: int
    items: List[AITestTaskResponse]


# ============ 辅助函数 ============

def calculate_progress(requirement_status: str, requirement_progress: int,
                      testcase_status: str, testcase_progress: int) -> int:
    """计算整体进度"""
    if requirement_status == "completed" and testcase_status == "completed":
        return 100
    
    if requirement_status == "pending":
        return 0
    
    if requirement_status == "running":
        return int(requirement_progress * 0.4)
    
    if requirement_status == "completed":
        if testcase_status == "pending":
            return 40
        if testcase_status == "running":
            return 40 + int(testcase_progress * 0.6)
        if testcase_status == "completed":
            return 100
    
    if requirement_status == "failed" or testcase_status == "failed":
        if requirement_status == "completed":
            return 40
        return 0
    
    return 0


async def serialize_task(task: AITestTask, project_name: str = None) -> dict:
    """序列化任务对象"""
    # 计算整体进度
    progress = calculate_progress(
        task.requirement_phase_status,
        task.requirement_phase_progress,
        task.testcase_phase_status,
        task.testcase_phase_progress
    )
    
    return {
        "id": task.id,
        "task_id": task.task_id,
        "project_id": task.project_id,
        "version_id": task.version_id,
        "task_name": task.task_name,
        "status": task.status,
        "progress": progress,
        
        "requirement_phase_status": task.requirement_phase_status,
        "requirement_phase_progress": task.requirement_phase_progress,
        "total_requirements": task.total_requirements,
        "saved_requirements": task.saved_requirements,
        
        "testcase_phase_status": task.testcase_phase_status,
        "testcase_phase_progress": task.testcase_phase_progress,
        "total_testcases": task.total_testcases,
        "saved_testcases": task.saved_testcases,
        
        "current_phase": task.current_phase,
        "current_phase_code": task.current_phase_code,
        "phases": task.phases or [],
        
        "error_message": task.error_message,
        "logs": task.logs or [],
        
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        
        "project_name": project_name,
    }


# ============ API端点 ============

@router.get("/stats")
async def get_task_stats():
    """获取任务统计"""
    total = await AITestTask.all().count()
    running = await AITestTask.filter(status="running").count()
    pending = await AITestTask.filter(status="pending").count()
    completed = await AITestTask.filter(status="completed").count()
    failed = await AITestTask.filter(status="failed").count()
    
    return {
        "total": total,
        "running": running,
        "pending": pending,
        "completed": completed,
        "failed": failed,
    }


@router.post("/create", response_model=dict)
async def create_ai_test_task(
    project_id: Optional[int] = Form(None, description="项目ID"),
    version_id: Optional[int] = Form(None, description="版本ID"),
    task_name: Optional[str] = Form(None, description="任务名称"),
    description: str = Form("", description="需求描述"),
    file: Optional[UploadFile] = File(None, description="需求文档文件"),
    source: Optional[str] = Form(None, description="来源：feishu"),
    feishu_url: Optional[str] = Form(None, description="飞书文档URL"),
):
    """
    创建并启动AI测试任务（统一入口）
    
    流程：
    1. 需求分析：文档解析 → 功能点提取 → 功能点保存
    2. 用例生成：用例设计 → 用例评审 → 用例保存
    """
    logger.info(f"创建AI测试任务: project_id={project_id}, task_name={task_name}")
    
    # 生成任务ID
    task_id = str(uuid.uuid4())
    
    # 读取文件内容
    document_content = ""
    input_filename = None
    input_source = "description"
    
    if file:
        input_source = "file"
        input_filename = file.filename
        try:
            content = await file.read()
            from app.rag.readers import UniversalDocumentReader
            document_content = await UniversalDocumentReader.get_text(
                content,
                file.filename or "document.txt"
            )
        except Exception as e:
            logger.error(f"文件读取失败: {e}")
            raise HTTPException(status_code=400, detail=f"文件读取失败: {str(e)}")
    
    # 飞书来源
    if source == 'feishu' and feishu_url:
        input_source = "feishu"
        try:
            from app.rag.readers import FeishuReader
            from app.config import settings
            
            app_id = getattr(settings, 'feishu_app_id', None)
            app_secret = getattr(settings, 'feishu_app_secret', None)
            
            if app_id and app_secret:
                reader = FeishuReader(app_id=app_id, app_secret=app_secret)
                docs = await reader.load_data_from_url(feishu_url)
                if docs:
                    document_content = docs[0].text
                    logger.info(f"从飞书文档加载内容成功，长度: {len(document_content)}")
        except Exception as e:
            logger.error(f"从飞书读取内容失败: {e}")
    
    # 如果task_name为空，生成默认值
    if not task_name:
        if project_id:
            task_name = f"项目{project_id}_测试任务"
        else:
            task_name = f"测试任务_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # 创建任务记录
    task = await AITestTask.create(
        task_id=task_id,
        project_id=project_id,
        version_id=version_id,
        task_name=task_name,
        status="pending",
        progress=0,
        input_source=input_source,
        input_filename=input_filename,
        document_content=document_content if len(document_content) < 50000 else document_content[:50000],  # 限制长度
    )
    
    # 后台启动任务
    async def run_unified_task():
        from app.agents.unified_workflow import run_unified_ai_test_workflow
        from app.api.websocket import push_to_websocket
        
        try:
            await run_unified_ai_test_workflow(
                task_id=task_id,
                project_id=project_id,
                version_id=version_id,
                task_name=task_name,
                document_content=document_content,
                description=description,
            )
        except Exception as e:
            logger.error(f"AI测试任务失败: {e}", exc_info=True)
            task_obj = await AITestTask.get(task_id=task_id)
            await task_obj.mark_failed(str(e))
            await push_to_websocket(task_id, "System", f"❌ 任务失败: {str(e)}", "error")
    
    asyncio.create_task(run_unified_task())
    
    return {
        "task_id": task_id,
        "message": "AI测试任务已启动",
    }


@router.get("/list")
async def list_ai_test_tasks(
    project_id: Optional[int] = Query(None, description="项目ID"),
    status: Optional[str] = Query(None, description="任务状态"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """获取AI测试任务列表（从统一任务表获取）"""
    # 从 AITestTask 获取数据
    query = AITestTask.all()
    
    if project_id:
        query = query.filter(project_id=project_id)
    if status:
        query = query.filter(status=status)
    if keyword:
        query = query.filter(task_name__icontains=keyword)
    
    # 先获取总数
    total = await query.count()
    
    # 分页查询
    tasks = await query.order_by("-created_at").offset((page - 1) * page_size).limit(page_size)
    
    # 获取项目名称映射
    project_ids = [t.project_id for t in tasks if t.project_id]
    project_map = {}
    if project_ids:
        projects = await Project.filter(id__in=set(project_ids))
        project_map = {p.id: p.name for p in projects}
    
    # 序列化任务列表
    items = []
    for task in tasks:
        task_dict = await serialize_task(task, project_map.get(task.project_id))
        items.append(task_dict)
    
    return AITestTaskListResponse(total=total, items=items)


def calculate_progress_from_phases(phases, status: str) -> int:
    """从阶段数据计算进度"""
    if not phases:
        if status == "completed":
            return 100
        if status in ["running", "pending"]:
            return 0
        return 0
    
    total = 0
    count = 0
    for phase in phases:
        prog = phase.get("progress", 0)
        total += prog
        count += 1
    
    if count > 0:
        return int(total / count)
    return 0


@router.get("/{task_id}", response_model=AITestTaskResponse)
async def get_ai_test_task(task_id: str):
    """获取任务详情"""
    task = await AITestTask.get_or_none(task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 获取项目名称
    project_name = None
    if task.project_id:
        project = await Project.get_or_none(id=task.project_id)
        if project:
            project_name = project.name
    
    return await serialize_task(task, project_name)


@router.get("/{task_id}/requirements")
async def get_task_requirements(task_id: str):
    """获取任务关联的功能点"""
    task = await AITestTask.get_or_none(task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    requirement_ids = task.saved_requirement_ids or []
    if not requirement_ids:
        # 从数据库按task_id查询
        requirements = await Requirement.filter(task_id=task_id)
        requirement_ids = [r.id for r in requirements]
    
    if requirement_ids:
        requirements = await Requirement.filter(id__in=requirement_ids)
        return {
            "total": len(requirements),
            "items": [
                {
                    "id": r.id,
                    "name": r.name,
                    "description": r.description,
                    "category": r.category,
                    "module": r.module,
                    "priority": r.priority,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in requirements
            ]
        }
    
    return {"total": 0, "items": []}


@router.get("/{task_id}/testcases")
async def get_task_testcases(task_id: str):
    """获取任务关联的测试用例"""
    task = await AITestTask.get_or_none(task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    testcase_ids = task.saved_testcase_ids or []
    if not testcase_ids:
        # 从数据库按task_id查询
        testcases = await TestCase.filter(task_id=task_id)
        testcase_ids = [tc.id for tc in testcases]
    
    if testcase_ids:
        testcases = await TestCase.filter(id__in=testcase_ids)
        return {
            "total": len(testcases),
            "items": [
                {
                    "id": tc.id,
                    "title": tc.title,
                    "priority": tc.priority,
                    "status": tc.status,
                    "test_type": tc.test_type,
                    "created_at": tc.created_at.isoformat() if tc.created_at else None,
                }
                for tc in testcases
            ]
        }
    
    return {"total": 0, "items": []}


@router.get("/{task_id}/logs")
async def get_task_logs(
    task_id: str,
    after_index: int = Query(0, description="获取此索引之后的日志")
):
    """获取任务日志（支持增量加载）"""
    task = await AITestTask.get_or_none(task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    logs = task.logs or []
    new_logs = logs[after_index:] if after_index < len(logs) else []
    
    return {
        "task_id": task_id,
        "status": task.status,
        "progress": task.progress,
        "current_phase": task.current_phase,
        "requirement_phase_status": task.requirement_phase_status,
        "testcase_phase_status": task.testcase_phase_status,
        "total_logs": len(logs),
        "new_logs": new_logs,
    }


@router.delete("/{task_id}")
async def delete_ai_test_task(task_id: str, force: bool = Query(False)):
    """
    删除任务
    支持删除任何状态的任务（pending/running/failed/cancelled/completed）
    force=True 时，即使任务正在运行也会删除
    """
    task = await AITestTask.get_or_none(task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.status == "running" and not force:
        raise HTTPException(status_code=400, detail="无法删除正在运行的任务，如需删除请使用强制删除")
    
    await task.delete()
    return {"message": "任务已删除"}


@router.post("/{task_id}/cancel")
async def cancel_ai_test_task(task_id: str):
    """
    取消任务
    支持取消：pending（排队中）、running（运行中）、failed（失败）的任务
    """
    task = await AITestTask.get_or_none(task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.status not in ["running", "pending", "failed"]:
        raise HTTPException(status_code=400, detail="只能取消进行中、排队中或失败的任务")
    
    await task.mark_cancelled()
    
    # 通知WebSocket
    from app.api.websocket import push_to_websocket
    await push_to_websocket(task_id, "System", "任务已取消", "info")
    
    return {"message": "任务已取消", "task_id": task_id}
