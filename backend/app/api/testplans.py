"""
测试计划管理API
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from app.models import TestPlan, TestPlanCase, TestCase
from app.schemas.testplan import (
    TestPlanCreate,
    TestPlanUpdate,
    TestPlanResponse,
    TestPlanListResponse,
    TestPlanDetailResponse,
    ExecutionStatusUpdate,
)

router = APIRouter()


@router.get("", response_model=TestPlanListResponse)
async def list_testplans(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    project_id: Optional[int] = Query(None, description="项目ID"),
    version_id: Optional[int] = Query(None, description="版本ID"),
    status: Optional[str] = Query(None, description="状态筛选"),
):
    """获取测试计划列表"""
    query = TestPlan.all()
    
    if project_id:
        query = query.filter(project_id=project_id)
    if version_id:
        query = query.filter(version_id=version_id)
    if status:
        query = query.filter(status=status)
    
    total = await query.count()
    items = await query.offset((page - 1) * page_size).limit(page_size)
    
    return TestPlanListResponse(
        total=total,
        items=[TestPlanResponse.model_validate(item) for item in items],
    )


@router.post("", response_model=TestPlanResponse)
async def create_testplan(data: TestPlanCreate):
    """创建测试计划"""
    testplan = await TestPlan.create(**data.model_dump())
    return TestPlanResponse.model_validate(testplan)


@router.get("/{testplan_id}", response_model=TestPlanDetailResponse)
async def get_testplan(testplan_id: int):
    """获取测试计划详情"""
    testplan = await TestPlan.get_or_none(id=testplan_id)
    if not testplan:
        raise HTTPException(status_code=404, detail="测试计划不存在")
    
    # 获取关联的用例
    plan_cases = await TestPlanCase.filter(test_plan_id=testplan_id).prefetch_related("test_case")
    
    # 统计执行情况
    total = len(plan_cases)
    passed = sum(1 for pc in plan_cases if pc.execution_status == "通过")
    failed = sum(1 for pc in plan_cases if pc.execution_status == "失败")
    blocked = sum(1 for pc in plan_cases if pc.execution_status == "阻塞")
    not_executed = sum(1 for pc in plan_cases if pc.execution_status == "未执行")
    pass_rate = round(passed / total * 100, 2) if total > 0 else 0.0
    
    return TestPlanDetailResponse(
        **TestPlanResponse.model_validate(testplan).model_dump(),
        test_plan_cases=[pc for pc in plan_cases],
        total_cases=total,
        passed_cases=passed,
        failed_cases=failed,
        blocked_cases=blocked,
        not_executed_cases=not_executed,
        pass_rate=pass_rate,
    )


@router.put("/{testplan_id}", response_model=TestPlanResponse)
async def update_testplan(testplan_id: int, data: TestPlanUpdate):
    """更新测试计划"""
    testplan = await TestPlan.get_or_none(id=testplan_id)
    if not testplan:
        raise HTTPException(status_code=404, detail="测试计划不存在")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(testplan, key, value)
    
    await testplan.save()
    return TestPlanResponse.model_validate(testplan)


@router.delete("/{testplan_id}")
async def delete_testplan(testplan_id: int):
    """删除测试计划"""
    testplan = await TestPlan.get_or_none(id=testplan_id)
    if not testplan:
        raise HTTPException(status_code=404, detail="测试计划不存在")
    
    await testplan.delete()
    return {"message": "删除成功"}


@router.post("/{testplan_id}/cases")
async def add_cases_to_plan(testplan_id: int, testcase_ids: List[int]):
    """批量添加用例到计划"""
    testplan = await TestPlan.get_or_none(id=testplan_id)
    if not testplan:
        raise HTTPException(status_code=404, detail="测试计划不存在")
    
    # 批量创建关联
    for testcase_id in testcase_ids:
        await TestPlanCase.get_or_create(
            test_plan_id=testplan_id,
            test_case_id=testcase_id,
            defaults={"execution_status": "未执行"}
        )
    
    return {"message": f"已添加 {len(testcase_ids)} 个用例"}


@router.put("/{testplan_id}/cases/{testcase_id}")
async def update_execution_status(
    testplan_id: int,
    testcase_id: int,
    data: ExecutionStatusUpdate,
):
    """更新用例执行状态"""
    plan_case = await TestPlanCase.get_or_none(
        test_plan_id=testplan_id,
        test_case_id=testcase_id,
    )
    if not plan_case:
        raise HTTPException(status_code=404, detail="用例未添加到该计划")
    
    from datetime import datetime
    plan_case.execution_status = data.execution_status
    plan_case.executor = data.executor
    plan_case.notes = data.notes
    plan_case.executed_at = datetime.now()
    
    await plan_case.save()
    return {"message": "执行状态已更新"}
