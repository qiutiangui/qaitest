"""
自定义模型配置
"""
from tortoise import fields
from tortoise.models import Model


class CustomModel(Model):
    """用户自定义模型配置表"""
    
    id = fields.IntField(pk=True, description="主键ID")
    name = fields.CharField(max_length=50, unique=True, description="模型标识（如 kimi）")
    display_name = fields.CharField(max_length=100, description="显示名称（如 Kimi AI）")
    base_url = fields.CharField(max_length=500, description="API 地址")
    api_key = fields.CharField(max_length=500, description="API Key")
    default_model = fields.CharField(max_length=100, description="默认模型名")
    description = fields.CharField(max_length=500, null=True, description="模型描述")
    enabled = fields.BooleanField(default=True, description="是否启用")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    
    class Meta:
        table = "custom_models"
        table_description = "用户自定义AI模型配置表"
    
    def __str__(self):
        return f"CustomModel({self.name}, {self.display_name})"
