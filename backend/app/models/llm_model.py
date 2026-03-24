"""
LLM模型配置表 - 存储可用的LLM模型配置
"""
from tortoise import fields
from tortoise.models import Model


class LLMModelConfig(Model):
    """LLM模型配置表 - 存储支持的所有LLM模型配置"""

    id = fields.IntField(pk=True, description="主键ID")
    name = fields.CharField(max_length=50, unique=True, description="模型标识（如 deepseek-chat）")
    display_name = fields.CharField(max_length=100, description="显示名称（如 DeepSeek Chat）")
    provider = fields.CharField(max_length=50, description="提供商：deepseek, moonshot, qwen, custom")
    base_url = fields.CharField(max_length=500, description="API 地址")
    api_key = fields.CharField(max_length=500, null=True, description="API Key（可选，敏感信息）")
    default_model = fields.CharField(max_length=100, description="默认模型名")
    description = fields.CharField(max_length=500, null=True, description="模型描述")
    enabled = fields.BooleanField(default=True, description="是否启用")
    is_default = fields.BooleanField(default=False, description="是否系统默认模型")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "llm_model_configs"
        table_description = "LLM模型配置表"

    def __str__(self):
        return f"LLMModelConfig({self.name}, {self.display_name})"
