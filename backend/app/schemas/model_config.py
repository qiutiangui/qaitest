"""
模型配置相关Schema
支持用户动态选择生成模型和评审模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime


class ModelProvider(str, Enum):
    """模型提供商"""
    DEEPSEEK = "deepseek"
    MOONSHOT = "moonshot"
    QWEN = "qwen"
    OPENAI = "openai"
    OLLAMA = "ollama"  # Ollama 本地模型
    CUSTOM = "custom"  # 用户自定义模型


class ModelConfig(BaseModel):
    """模型配置"""
    provider: ModelProvider = Field(..., description="模型提供商")
    model: Optional[str] = Field(None, description="具体模型名称，不填则使用默认")
    api_key: Optional[str] = Field(None, description="API Key，不填则使用系统配置")
    base_url: Optional[str] = Field(None, description="API Base URL，不填则使用默认")
    custom_id: Optional[int] = Field(None, description="自定义模型ID，仅当provider为custom时使用")
    
    class Config:
        json_schema_extra = {
            "example": {
                "provider": "deepseek",
                "model": "deepseek-chat",
                "api_key": None,
                "base_url": None
            }
        }


class ModelConfigRequest(BaseModel):
    """模型配置请求"""
    # 需求分析模型配置（用于需求分析阶段）
    requirement_analyze_model: Optional[ModelConfig] = Field(
        None,
        description="需求分析模型配置"
    )

    # 用例生成模型配置（用于用例生成）
    testcase_generate_model: Optional[ModelConfig] = Field(
        None,
        description="用例生成模型配置"
    )

    # 用例评审模型配置（用于用例评审、定稿）
    testcase_review_model: Optional[ModelConfig] = Field(
        None,
        description="用例评审模型配置"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "requirement_analyze_model": {
                    "provider": "deepseek",
                    "model": "deepseek-chat"
                },
                "testcase_generate_model": {
                    "provider": "deepseek",
                    "model": "deepseek-chat"
                },
                "testcase_review_model": {
                    "provider": "moonshot",
                    "model": "moonshot-v1-32k"
                }
            }
        }


class AvailableModel(BaseModel):
    """可用模型信息"""
    provider: ModelProvider
    model_name: str
    display_name: str
    description: str
    supported_features: List[str] = Field(default_factory=list)
    is_available: bool = Field(default=True, description="是否已配置API Key")
    custom_id: Optional[int] = Field(None, description="自定义模型ID")


class ModelListResponse(BaseModel):
    """可用模型列表响应"""
    requirement_analyze_models: List[AvailableModel] = Field(default_factory=list)
    testcase_generate_models: List[AvailableModel] = Field(default_factory=list)
    testcase_review_models: List[AvailableModel] = Field(default_factory=list)
    default_requirement_analyze: ModelProvider = ModelProvider.DEEPSEEK
    default_testcase_generate: ModelProvider = ModelProvider.DEEPSEEK
    default_testcase_review: ModelProvider = ModelProvider.MOONSHOT


# ========== 自定义模型相关Schema ==========

class CustomModelCreate(BaseModel):
    """创建自定义模型请求"""
    name: str = Field(..., description="模型标识（如 kimi）", min_length=1, max_length=50)
    display_name: str = Field(..., description="显示名称（如 Kimi AI）", min_length=1, max_length=100)
    base_url: str = Field(..., description="API 地址（如 https://api.moonshot.cn/v1）", min_length=1, max_length=500)
    api_key: str = Field(..., description="API Key", min_length=1, max_length=500)
    default_model: str = Field(..., description="默认模型名", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="模型描述", max_length=500)


class CustomModelUpdate(BaseModel):
    """更新自定义模型请求"""
    display_name: Optional[str] = Field(None, description="显示名称", max_length=100)
    base_url: Optional[str] = Field(None, description="API 地址", max_length=500)
    api_key: Optional[str] = Field(None, description="API Key", max_length=500)
    default_model: Optional[str] = Field(None, description="默认模型名", max_length=100)
    description: Optional[str] = Field(None, description="模型描述", max_length=500)
    enabled: Optional[bool] = Field(None, description="是否启用")


class CustomModelResponse(BaseModel):
    """自定义模型响应"""
    id: int
    name: str
    display_name: str
    base_url: str
    default_model: str
    description: Optional[str] = None
    enabled: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
