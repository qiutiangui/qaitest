"""
嵌入模型配置表 - 用于RAG知识检索的嵌入模型
"""
from tortoise import fields
from tortoise.models import Model


class EmbeddingModelConfig(Model):
    """嵌入模型配置表 - 用于RAG知识检索的嵌入向量模型"""

    id = fields.IntField(pk=True, description="主键ID")
    name = fields.CharField(max_length=100, unique=True, description="配置标识（如 qwen-embedding-v3）")
    display_name = fields.CharField(max_length=100, description="显示名称（如 Qwen 嵌入模型 v3）")
    provider = fields.CharField(max_length=50, description="提供商：dashscope, openai, custom")
    api_base = fields.CharField(max_length=500, description="API 地址")
    api_key = fields.CharField(max_length=500, null=True, description="API Key（可选，敏感信息）")
    model_name = fields.CharField(max_length=100, description="嵌入模型名（如 text-embedding-v3）")
    dimension = fields.IntField(default=1024, description="向量维度")
    enabled = fields.BooleanField(default=True, description="是否启用")
    is_default = fields.BooleanField(default=False, description="是否默认嵌入模型")
    description = fields.CharField(max_length=500, null=True, description="模型描述")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "embedding_model_configs"
        table_description = "嵌入模型配置表"

    def __str__(self):
        return f"EmbeddingModelConfig({self.name}, {self.display_name})"
