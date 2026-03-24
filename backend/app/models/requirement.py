"""
功能点（需求）模型
"""
from tortoise import fields
from tortoise.models import Model


class Requirement(Model):
    """功能点表"""

    id = fields.IntField(pk=True, description="功能点ID")
    project = fields.ForeignKeyField("models.Project", related_name="requirements", null=True, description="所属项目")
    version = fields.ForeignKeyField("models.ProjectVersion", related_name="requirements", null=True, description="关联版本")
    requirement_name = fields.CharField(max_length=200, null=True, description="需求名称")
    name = fields.CharField(max_length=500, description="功能点名称")
    description = fields.TextField(null=True, description="功能点描述")
    category = fields.CharField(max_length=50, null=True, description="类别")
    module = fields.CharField(max_length=100, null=True, description="所属模块")
    priority = fields.CharField(max_length=10, null=True, description="优先级")
    acceptance_criteria = fields.TextField(null=True, description="验收标准")
    keywords = fields.CharField(max_length=500, null=True, description="关键词")
    task_id = fields.CharField(max_length=100, null=True, description="任务ID")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    
    class Meta:
        table = "requirements"
        table_description = "功能点表"
    
    def __str__(self):
        return f"Requirement({self.id}, {self.name})"
