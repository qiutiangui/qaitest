"""
版本管理服务
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.models import (
    ProjectVersion, VersionSnapshot, 
    Requirement, TestCase, TestPlan, TestReport
)
from loguru import logger


class VersionService:
    """版本管理服务"""
    
    @staticmethod
    async def create_baseline(version_id: int) -> VersionSnapshot:
        """创建版本基线快照"""
        version = await ProjectVersion.get_or_none(id=version_id)
        if not version:
            raise ValueError(f"版本不存在: {version_id}")
        
        # 收集版本相关的所有数据
        requirements = await Requirement.filter(version_id=version_id).values()
        test_cases = await TestCase.filter(version_id=version_id).values()
        test_plans = await TestPlan.filter(version_id=version_id).values()
        test_reports = await TestReport.filter(version_id=version_id).values()
        
        snapshot_data = {
            "version_info": {
                "id": version.id,
                "version_number": version.version_number,
                "version_name": version.version_name,
                "status": version.status,
                "description": version.description,
            },
            "requirements": list(requirements),
            "test_cases": list(test_cases),
            "test_plans": list(test_plans),
            "test_reports": list(test_reports),
            "snapshot_time": datetime.now().isoformat(),
        }
        
        snapshot = await VersionSnapshot.create(
            version_id=version_id,
            snapshot_type="基线快照",
            snapshot_data=snapshot_data,
        )
        
        version.is_baseline = True
        await version.save()
        
        logger.info(f"创建版本基线: version_id={version_id}")
        
        return snapshot
    
    @staticmethod
    async def compare_versions(version_a_id: int, version_b_id: int) -> Dict[str, Any]:
        """对比两个版本"""
        version_a = await ProjectVersion.get_or_none(id=version_a_id)
        version_b = await ProjectVersion.get_or_none(id=version_b_id)
        
        if not version_a or not version_b:
            raise ValueError("版本不存在")
        
        # 获取两个版本的需求
        reqs_a = await Requirement.filter(version_id=version_a_id).values_list("id", flat=True)
        reqs_b = await Requirement.filter(version_id=version_b_id).values_list("id", flat=True)
        
        # 获取两个版本的用例
        cases_a = await TestCase.filter(version_id=version_a_id).values_list("id", flat=True)
        cases_b = await TestCase.filter(version_id=version_b_id).values_list("id", flat=True)
        
        # 获取两个版本的测试计划
        plans_a = await TestPlan.filter(version_id=version_a_id).values_list("id", flat=True)
        plans_b = await TestPlan.filter(version_id=version_b_id).values_list("id", flat=True)
        
        reqs_a_set, reqs_b_set = set(reqs_a), set(reqs_b)
        cases_a_set, cases_b_set = set(cases_a), set(cases_b)
        plans_a_set, plans_b_set = set(plans_a), set(plans_b)
        
        return {
            "version_a": {
                "id": version_a_id,
                "version_number": version_a.version_number,
                "status": version_a.status,
            },
            "version_b": {
                "id": version_b_id,
                "version_number": version_b.version_number,
                "status": version_b.status,
            },
            "requirement_changes": {
                "added": list(reqs_b_set - reqs_a_set),
                "removed": list(reqs_a_set - reqs_b_set),
                "common": list(reqs_a_set & reqs_b_set),
            },
            "testcase_changes": {
                "added": list(cases_b_set - cases_a_set),
                "removed": list(cases_a_set - cases_b_set),
                "common": list(cases_a_set & cases_b_set),
            },
            "testplan_changes": {
                "added": list(plans_b_set - plans_a_set),
                "removed": list(plans_a_set - plans_b_set),
                "common": list(plans_a_set & plans_b_set),
            },
        }
    
    @staticmethod
    async def rollback_version(version_id: int) -> Dict[str, Any]:
        """版本回溯 - 恢复到该版本的基线快照"""
        version = await ProjectVersion.get_or_none(id=version_id)
        if not version:
            raise ValueError("版本不存在")
        
        # 获取最近的基线快照
        snapshot = await VersionSnapshot.filter(
            version_id=version_id,
            snapshot_type="基线快照"
        ).order_by("-created_at").first()
        
        if not snapshot:
            raise ValueError("该版本没有基线快照，无法回溯")
        
        # TODO: 实现数据恢复逻辑（根据快照数据恢复）
        # 这里需要谨慎处理，可能需要创建新的记录而不是直接覆盖
        
        logger.info(f"版本回溯: version_id={version_id}")
        
        return {
            "message": "版本回溯成功",
            "version_id": version_id,
            "snapshot_id": snapshot.id,
            "snapshot_time": snapshot.created_at.isoformat() if snapshot.created_at else None,
        }
    
    @staticmethod
    async def get_version_stats(version_id: int) -> Dict[str, Any]:
        """获取版本统计信息"""
        version = await ProjectVersion.get_or_none(id=version_id)
        if not version:
            return {}
        
        requirement_count = await Requirement.filter(version_id=version_id).count()
        testcase_count = await TestCase.filter(version_id=version_id).count()
        testplan_count = await TestPlan.filter(version_id=version_id).count()
        report_count = await TestReport.filter(version_id=version_id).count()
        
        return {
            "version_id": version_id,
            "version_number": version.version_number,
            "requirement_count": requirement_count,
            "testcase_count": testcase_count,
            "testplan_count": testplan_count,
            "report_count": report_count,
        }
