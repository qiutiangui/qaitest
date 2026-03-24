"""
项目模型
"""
from tortoise import fields
from tortoise.models import Model


class Project(Model):
    """项目表"""
    
    id = fields.IntField(pk=True, description="项目ID")
    name = fields.CharField(max_length=200, description="项目名称")
    description = fields.TextField(null=True, description="项目描述")
    status = fields.CharField(max_length=20, default="活跃", description="状态")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    
    class Meta:
        table = "projects"
        table_description = "项目表"
    
    def __str__(self):
        return f"Project({self.id}, {self.name})"
    
    class PydanticMeta:
        computed = ["id"]
        exclude = ["created_at", "updated_at"]
