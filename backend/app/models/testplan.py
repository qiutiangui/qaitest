"""
测试计划模型
"""
from tortoise import fields
from tortoise.models import Model


class TestPlan(Model):
    """测试计划表"""
    
    id = fields.IntField(pk=True, description="计划ID")
    project = fields.ForeignKeyField("models.Project", related_name="test_plans", description="所属项目")
    version = fields.ForeignKeyField("models.ProjectVersion", related_name="test_plans", null=True, description="关联版本")
    name = fields.CharField(max_length=200, description="计划名称")
    description = fields.TextField(null=True, description="计划描述")
    status = fields.CharField(max_length=20, default="未开始", description="状态：未开始/进行中/已完成/已归档")
    start_time = fields.DatetimeField(null=True, description="开始时间")
    end_time = fields.DatetimeField(null=True, description="结束时间")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    
    class Meta:
        table = "test_plans"
        table_description = "测试计划表"
    
    def __str__(self):
        return f"TestPlan({self.id}, {self.name})"


class TestPlanCase(Model):
    """测试计划用例关联表"""
    
    id = fields.IntField(pk=True, description="关联ID")
    test_plan = fields.ForeignKeyField("models.TestPlan", related_name="test_plan_cases", description="所属计划")
    test_case = fields.ForeignKeyField("models.TestCase", related_name="test_plan_cases", description="所属用例")
    execution_status = fields.CharField(max_length=20, default="未执行", description="执行状态：未执行/通过/失败/阻塞")
    executed_at = fields.DatetimeField(null=True, description="执行时间")
    executor = fields.CharField(max_length=50, null=True, description="执行人")
    notes = fields.TextField(null=True, description="备注")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    
    class Meta:
        table = "test_plan_cases"
        table_description = "测试计划用例关联表"
        unique_together = ("test_plan", "test_case")
    
    def __str__(self):
        return f"TestPlanCase({self.id}, status={self.execution_status})"
