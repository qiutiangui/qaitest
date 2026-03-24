"""
默认模型配置表 - 存储各用途的默认模型选择
"""
from tortoise import fields
from tortoise.models import Model


class DefaultModelConfig(Model):
    """默认模型配置表 - 存储各用途的默认模型选择"""

    id = fields.IntField(pk=True, description="主键ID")
    purpose = fields.CharField(max_length=50, unique=True, description="用途：requirement_analyze, testcase_generate, testcase_review, embedding")
    model_name = fields.CharField(max_length=100, description="关联的模型名称")
    model_type = fields.CharField(max_length=20, description="模型类型：llm 或 embedding")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "default_model_configs"
        table_description = "默认模型配置表"

    def __str__(self):
        return f"DefaultModelConfig({self.purpose}, {self.model_name})"
