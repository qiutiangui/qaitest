"""
测试报告管理API
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.models import TestReport, TestPlan, TestPlanCase
from app.schemas.testreport import (
    TestReportCreate,
    TestReportUpdate,
    TestReportResponse,
    TestReportListResponse,
    TestReportDetailResponse,
)

router = APIRouter()


@router.get("", response_model=TestReportListResponse)
async def list_testreports(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    project_id: Optional[int] = Query(None, description="项目ID"),
    version_id: Optional[int] = Query(None, description="版本ID"),
    status: Optional[str] = Query(None, description="状态筛选"),
):
    """获取测试报告列表"""
    query = TestReport.all()
    
    if project_id:
        query = query.filter(project_id=project_id)
    if version_id:
        query = query.filter(version_id=version_id)
    if status:
        query = query.filter(status=status)
    
    total = await query.count()
    items = await query.offset((page - 1) * page_size).limit(page_size)
    
    return TestReportListResponse(
        total=total,
        items=[TestReportResponse.model_validate(item) for item in items],
    )


@router.post("", response_model=TestReportResponse)
async def create_testreport(data: TestReportCreate):
    """创建测试报告"""
    # 获取测试计划信息
    testplan = await TestPlan.get_or_none(id=data.test_plan_id)
    if not testplan:
        raise HTTPException(status_code=404, detail="测试计划不存在")
    
    # 统计执行情况
    plan_cases = await TestPlanCase.filter(test_plan_id=data.test_plan_id)
    total = len(plan_cases)
    passed = sum(1 for pc in plan_cases if pc.execution_status == "通过")
    failed = sum(1 for pc in plan_cases if pc.execution_status == "失败")
    blocked = sum(1 for pc in plan_cases if pc.execution_status == "阻塞")
    not_executed = sum(1 for pc in plan_cases if pc.execution_status == "未执行")
    pass_rate = round(passed / total * 100, 2) if total > 0 else 0.0
    
    # 创建报告
    report = await TestReport.create(
        test_plan_id=data.test_plan_id,
        project_id=testplan.project_id,
        version_id=testplan.version_id,
        title=data.title,
        report_type=data.report_type,
        summary=data.summary,
        total_cases=total,
        passed_cases=passed,
        failed_cases=failed,
        blocked_cases=blocked,
        not_executed_cases=not_executed,
        pass_rate=pass_rate,
    )
    
    return TestReportResponse.model_validate(report)


@router.get("/{report_id}", response_model=TestReportDetailResponse)
async def get_testreport(report_id: int):
    """获取测试报告详情"""
    report = await TestReport.get_or_none(id=report_id)
    if not report:
        raise HTTPException(status_code=404, detail="测试报告不存在")
    
    # 获取执行详情
    plan_cases = await TestPlanCase.filter(test_plan_id=report.test_plan_id).prefetch_related("test_case")
    execution_details = [
        {
            "testcase_id": pc.test_case_id,
            "title": pc.test_case.title if pc.test_case else None,
            "execution_status": pc.execution_status,
            "executor": pc.executor,
            "executed_at": pc.executed_at.isoformat() if pc.executed_at else None,
            "notes": pc.notes,
        }
        for pc in plan_cases
    ]
    
    return TestReportDetailResponse(
        **TestReportResponse.model_validate(report).model_dump(),
        execution_details=execution_details,
    )


@router.put("/{report_id}", response_model=TestReportResponse)
async def update_testreport(report_id: int, data: TestReportUpdate):
    """更新测试报告"""
    report = await TestReport.get_or_none(id=report_id)
    if not report:
        raise HTTPException(status_code=404, detail="测试报告不存在")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(report, key, value)
    
    await report.save()
    return TestReportResponse.model_validate(report)


@router.delete("/{report_id}")
async def delete_testreport(report_id: int):
    """删除测试报告"""
    report = await TestReport.get_or_none(id=report_id)
    if not report:
        raise HTTPException(status_code=404, detail="测试报告不存在")
    
    await report.delete()
    return {"message": "删除成功"}


@router.get("/{report_id}/export")
async def export_report(report_id: int, format: str = Query("pdf", description="导出格式：pdf/html/word")):
    """导出测试报告"""
    report = await TestReport.get_or_none(id=report_id)
    if not report:
        raise HTTPException(status_code=404, detail="测试报告不存在")
    
    # TODO: 实现报告导出逻辑
    return {"message": f"导出功能开发中，格式：{format}"}
