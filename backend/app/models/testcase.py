"""
测试用例模型
"""
from tortoise import fields
from tortoise.models import Model


class TestCase(Model):
    """测试用例表"""

    id = fields.IntField(pk=True, description="用例ID")
    project = fields.ForeignKeyField("models.Project", related_name="test_cases", null=True, description="所属项目")
    requirement = fields.ForeignKeyField("models.Requirement", related_name="test_cases", null=True, description="关联功能点")
    version = fields.ForeignKeyField("models.ProjectVersion", related_name="test_cases", null=True, description="关联版本（可选）")
    title = fields.CharField(max_length=500, description="用例标题")
    description = fields.TextField(null=True, description="用例描述")
    priority = fields.CharField(max_length=20, null=True, description="优先级")
    status = fields.CharField(max_length=20, default="未开始", description="状态")
    test_type = fields.CharField(max_length=50, null=True, description="测试类型")
    preconditions = fields.TextField(null=True, description="前置条件")
    test_data = fields.TextField(null=True, description="测试数据")
    creator = fields.CharField(max_length=50, default="AI", description="创建者")
    task_id = fields.CharField(max_length=100, null=True, description="任务ID")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    
    class Meta:
        table = "test_cases"
        table_description = "测试用例表"
    
    def __str__(self):
        return f"TestCase({self.id}, {self.title})"


class TestStep(Model):
    """测试步骤表"""
    
    id = fields.IntField(pk=True, description="步骤ID")
    test_case = fields.ForeignKeyField("models.TestCase", related_name="steps", description="所属用例")
    step_number = fields.IntField(description="步骤序号")
    description = fields.TextField(description="步骤描述")
    expected_result = fields.TextField(null=True, description="预期结果")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    
    class Meta:
        table = "test_steps"
        table_description = "测试步骤表"
        ordering = ["step_number"]
    
    def __str__(self):
        return f"TestStep({self.id}, step {self.step_number})"
