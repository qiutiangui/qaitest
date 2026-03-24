"""
测试报告模型
"""
from tortoise import fields
from tortoise.models import Model


class TestReport(Model):
    """测试报告表"""
    
    id = fields.IntField(pk=True, description="报告ID")
    test_plan = fields.ForeignKeyField("models.TestPlan", related_name="reports", description="所属计划")
    project = fields.ForeignKeyField("models.Project", related_name="reports", description="所属项目")
    version = fields.ForeignKeyField("models.ProjectVersion", related_name="reports", null=True, description="关联版本")
    title = fields.CharField(max_length=200, description="报告标题")
    report_type = fields.CharField(max_length=20, default="执行报告", description="报告类型")
    summary = fields.TextField(null=True, description="摘要")
    total_cases = fields.IntField(default=0, description="总用例数")
    passed_cases = fields.IntField(default=0, description="通过用例数")
    failed_cases = fields.IntField(default=0, description="失败用例数")
    blocked_cases = fields.IntField(default=0, description="阻塞用例数")
    not_executed_cases = fields.IntField(default=0, description="未执行用例数")
    pass_rate = fields.DecimalField(max_digits=5, decimal_places=2, default=0.00, description="通过率")
    start_time = fields.DatetimeField(null=True, description="开始时间")
    end_time = fields.DatetimeField(null=True, description="结束时间")
    status = fields.CharField(max_length=20, default="草稿", description="状态：草稿/已发布")
    created_by = fields.CharField(max_length=50, null=True, description="创建人")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    
    class Meta:
        table = "test_reports"
        table_description = "测试报告表"
    
    def __str__(self):
        return f"TestReport({self.id}, {self.title})"
