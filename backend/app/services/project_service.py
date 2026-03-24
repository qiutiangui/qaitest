"""
项目管理服务
"""
from typing import Optional, List
from app.models import Project
from loguru import logger


class ProjectService:
    """项目管理服务"""
    
    @staticmethod
    async def get_project_stats(project_id: int) -> dict:
        """获取项目统计信息"""
        from app.models import Requirement, TestCase, TestPlan, TestReport
        
        project = await Project.get_or_none(id=project_id)
        if not project:
            return {}
        
        requirement_count = await Requirement.filter(project_id=project_id).count()
        testcase_count = await TestCase.filter(project_id=project_id).count()
        testplan_count = await TestPlan.filter(project_id=project_id).count()
        report_count = await TestReport.filter(project_id=project_id).count()
        
        return {
            "project_id": project_id,
            "project_name": project.name,
            "requirement_count": requirement_count,
            "testcase_count": testcase_count,
            "testplan_count": testplan_count,
            "report_count": report_count,
        }
