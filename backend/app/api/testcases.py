"""
测试用例管理API
"""
from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional
import uuid
import asyncio
from loguru import logger
from app.models import TestCase, TestStep, AITestTask, Requirement
from app.schemas.testcase import (
    TestCaseCreate,
    TestCaseUpdate,
    TestCaseResponse,
    TestCaseListResponse,
    TestStepCreate,
    TestStepResponse,
    TestCaseGenerateRequest,
)

router = APIRouter()


@router.get("", response_model=TestCaseListResponse)
async def list_testcases(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    project_id: Optional[int] = Query(None, description="项目ID"),
    requirement_id: Optional[int] = Query(None, description="功能点ID"),
    priority: Optional[str] = Query(None, description="优先级筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
):
    """获取测试用例列表"""
    query = TestCase.all().prefetch_related("steps").select_related("requirement")
    
    if project_id:
        query = query.filter(project_id=project_id)
    if requirement_id:
        query = query.filter(requirement_id=requirement_id)
    if priority:
        query = query.filter(priority=priority)
    if status:
        query = query.filter(status=status)
    if keyword:
        query = query.filter(title__contains=keyword)
    
    total = await query.count()
    items = await query.offset((page - 1) * page_size).limit(page_size)
    
    # 为每个测试用例添加requirement_name
    result_items = []
    for item in items:
        # 构建响应数据
        item_data = {
            "id": item.id,
            "project_id": item.project_id,
            "requirement_id": item.requirement_id,
            "requirement_name": item.requirement.requirement_name if hasattr(item, 'requirement') and item.requirement else None,
            "version_id": item.version_id,
            "title": item.title,
            "description": item.description,
            "priority": item.priority,
            "status": item.status,
            "test_type": item.test_type,
            "preconditions": item.preconditions,
            "test_data": item.test_data,
            "creator": item.creator,
            "created_at": item.created_at,
            "steps": list(item.steps) if item.steps else []
        }
        result_items.append(TestCaseResponse.model_validate(item_data))
    
    return TestCaseListResponse(
        total=total,
        items=result_items,
    )


@router.post("", response_model=TestCaseResponse)
async def create_testcase(data: TestCaseCreate):
    """创建测试用例"""
    steps_data = data.steps or []
    testcase_data = data.model_dump(exclude={"steps"})
    
    testcase = await TestCase.create(**testcase_data)
    
    # 创建测试步骤
    for step_data in steps_data:
        await TestStep.create(test_case_id=testcase.id, **step_data.model_dump())
    
    # 重新获取包含步骤的用例
    testcase = await TestCase.get(id=testcase.id).prefetch_related("steps")
    return TestCaseResponse.model_validate(testcase)


@router.get("/{testcase_id}", response_model=TestCaseResponse)
async def get_testcase(testcase_id: int):
    """获取测试用例详情"""
    testcase = await TestCase.get_or_none(id=testcase_id).prefetch_related("steps").select_related("requirement")
    if not testcase:
        raise HTTPException(status_code=404, detail="测试用例不存在")
    
    # 构建响应数据
    testcase_data = {
        "id": testcase.id,
        "project_id": testcase.project_id,
        "requirement_id": testcase.requirement_id,
        "requirement_name": testcase.requirement.requirement_name if hasattr(testcase, 'requirement') and testcase.requirement else None,
        "version_id": testcase.version_id,
        "title": testcase.title,
        "description": testcase.description,
        "priority": testcase.priority,
        "status": testcase.status,
        "test_type": testcase.test_type,
        "preconditions": testcase.preconditions,
        "test_data": testcase.test_data,
        "creator": testcase.creator,
        "created_at": testcase.created_at,
        "steps": list(testcase.steps) if testcase.steps else []
    }
    
    return TestCaseResponse.model_validate(testcase_data)


@router.put("/{testcase_id}", response_model=TestCaseResponse)
async def update_testcase(testcase_id: int, data: TestCaseUpdate):
    """更新测试用例"""
    testcase = await TestCase.get_or_none(id=testcase_id)
    if not testcase:
        raise HTTPException(status_code=404, detail="测试用例不存在")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(testcase, key, value)
    
    await testcase.save()
    return TestCaseResponse.model_validate(testcase)


@router.post("/by-ids")
async def get_testcases_by_ids(ids: list[int] = Body(..., embed=True)):
    """根据ID列表获取测试用例"""
    if not ids:
        return []
    testcases = await TestCase.filter(id__in=ids)
    result = []
    for tc in testcases:
        # 获取关联的功能点名称
        requirement_name = None
        if tc.requirement_id:
            req = await Requirement.get_or_none(id=tc.requirement_id)
            if req:
                requirement_name = req.name

        # 获取步骤
        steps = await TestStep.filter(test_case_id=tc.id).order_by("step_number")
        step_responses = [TestStepResponse.model_validate(s) for s in steps]

        # 先将 steps 设为空列表，避免 Pydantic 验证失败
        tc.steps = []
        response_data = TestCaseResponse.model_validate(tc)
        response_data.requirement_name = requirement_name
        response_data.steps = step_responses
        result.append(response_data)

    return result


@router.delete("/{testcase_id}")
async def delete_testcase(testcase_id: int):
    """删除测试用例"""
    testcase = await TestCase.get_or_none(id=testcase_id)
    if not testcase:
        raise HTTPException(status_code=404, detail="测试用例不存在")
    
    await testcase.delete()
    return {"message": "删除成功"}


@router.post("/batch-delete")
async def batch_delete_testcases(ids: list[int]):
    """批量删除测试用例"""
    if not ids:
        raise HTTPException(status_code=400, detail="请选择要删除的测试用例")
    
    # 获取要删除的测试用例
    testcases = await TestCase.filter(id__in=ids)
    
    if not testcases:
        raise HTTPException(status_code=404, detail="未找到要删除的测试用例")
    
    # 执行批量删除
    deleted_count = await TestCase.filter(id__in=ids).delete()
    
    return {
        "message": f"成功删除 {deleted_count} 个测试用例",
        "deleted_count": deleted_count
    }


@router.post("/generate")
async def generate_testcases(data: TestCaseGenerateRequest):
    """
    生成测试用例

    Args:
        data: 包含项目ID、功能点ID列表、版本ID、模型配置

    Returns:
        task_id: 任务ID，用于WebSocket连接
    """
    logger.info(f"收到生成请求: requirement_ids={data.requirement_ids}, llm_config={data.llm_config}")

    # 使用传入的task_id或生成新的
    task_id = data.task_id or str(uuid.uuid4())

    # 获取功能点名称
    from app.models import Requirement
    requirements = await Requirement.filter(id__in=data.requirement_ids)
    function_names = [r.name for r in requirements]

    # 检查是否已存在相同的task_id任务
    existing_task = await AITestTask.get_or_none(task_id=task_id)
    if existing_task:
        # 检查用例生成阶段状态
        if existing_task.testcase_phase_status == "running":
            return {
                "task_id": task_id,
                "message": "用例生成任务已在运行中",
                "status": "running"
            }
        elif existing_task.testcase_phase_status == "completed":
            return {
                "task_id": task_id,
                "message": "用例生成任务已完成",
                "status": "completed",
                "saved_count": existing_task.saved_testcases or 0
            }
        else:
            # 如果之前失败，可以重新运行
            await existing_task.update_testcase_progress(status="running", progress=0)
            existing_task.error_message = None
            await existing_task.save()
            task = existing_task
    else:
        # 创建新的任务记录
        task = await AITestTask.create(
            task_id=task_id,
            project_id=data.project_id,
            version_id=data.version_id,
            task_name=function_names[0] if function_names else f"用例生成任务_{task_id[:8]}",
            status="running",
            progress=40,  # 需求分析已完成，进度从40%开始
            requirement_phase_status="completed",
            requirement_phase_progress=100,
            testcase_phase_status="running",
            testcase_phase_progress=0,
            total_testcases=0,
            saved_testcases=0,
        )

    # 后台启动生成任务
    async def run_generation():
        from app.agents.testcase_agents import run_testcase_generation  # 使用新的并行RAG版本
        try:
            await run_testcase_generation(
                task_id=task_id,
                project_id=data.project_id,
                requirement_ids=data.requirement_ids,
                version_id=data.version_id,
                llm_config=data.llm_config,
            )
        except Exception as e:
            logger.error(f"测试用例生成失败: {e}")
            # 更新任务状态为失败
            task = await AITestTask.get_or_none(task_id=task_id)
            if task:
                await task.mark_failed(error_message=str(e))

    # 启动后台任务
    asyncio.create_task(run_generation())

    return {
        "task_id": task_id,
        "message": "测试用例生成任务已启动",
    }


@router.get("/stats/project/{project_id}")
async def get_testcase_stats(project_id: int):
    """获取项目的测试用例统计信息"""
    total = await TestCase.filter(project_id=project_id).count()
    
    # 按优先级统计
    priorities = {}
    testcases = await TestCase.filter(project_id=project_id)
    for tc in testcases:
        priority = tc.priority or "中"
        priorities[priority] = priorities.get(priority, 0) + 1
    
    # 按类型统计
    test_types = {}
    for tc in testcases:
        test_type = tc.test_type or "功能测试"
        test_types[test_type] = test_types.get(test_type, 0) + 1
    
    return {
        "project_id": project_id,
        "total": total,
        "by_priority": priorities,
        "by_type": test_types,
    }


@router.get("/export/{task_id}")
async def export_testcases(
    task_id: str,
    format: str = Query("excel", description="导出格式: excel/markdown")
):
    """根据任务ID导出测试用例"""
    testcases = await TestCase.filter(task_id=task_id).prefetch_related("steps")
    
    if format == "markdown":
        # 生成Markdown格式
        lines = ["# 测试用例列表\n"]
        for tc in testcases:
            lines.append(f"## {tc.title}\n")
            lines.append(f"**描述**: {tc.description or '无'}\n")
            lines.append(f"**优先级**: {tc.priority}\n")
            lines.append(f"**类型**: {tc.test_type or '功能测试'}\n")
            lines.append(f"**前置条件**: {tc.preconditions or '无'}\n")
            lines.append("\n### 测试步骤\n")
            for step in tc.steps:
                lines.append(f"{step.step_number}. {step.description}\n")
                lines.append(f"   - 预期结果: {step.expected_result or '无'}\n")
            lines.append("\n---\n")
        
        return {"content": "\n".join(lines), "format": "markdown"}
    
    else:
        # 返回Excel数据结构，前端处理导出
        data = []
        for tc in testcases:
            row = {
                "ID": tc.id,
                "标题": tc.title,
                "描述": tc.description,
                "优先级": tc.priority,
                "类型": tc.test_type,
                "前置条件": tc.preconditions,
                "状态": tc.status,
                "创建时间": tc.created_at.isoformat() if tc.created_at else "",
            }
            # 添加步骤信息
            for i, step in enumerate(tc.steps, 1):
                row[f"步骤{i}"] = step.description
                row[f"预期结果{i}"] = step.expected_result
            data.append(row)
        
        return {"data": data, "format": "excel"}
