"""
模型配置API
支持用户查看和选择可用模型
"""
from fastapi import APIRouter
from typing import List
from loguru import logger

from app.schemas.model_config import (
    ModelListResponse,
    AvailableModel,
    ModelProvider,
)
from app.config import settings
from app.models.custom_model import CustomModel

router = APIRouter()


def get_all_available_models() -> List[AvailableModel]:
    """获取所有可用模型"""
    models = []
    
    # DeepSeek 模型
    if settings.deepseek_api_key:
        models.extend([
            AvailableModel(
                provider=ModelProvider.DEEPSEEK,
                model_name="deepseek-chat",
                display_name="DeepSeek Chat",
                description="DeepSeek通用对话模型",
                supported_features=["生成", "评审", "分析"],
                is_available=True
            ),
            AvailableModel(
                provider=ModelProvider.DEEPSEEK,
                model_name="deepseek-reasoner",
                display_name="DeepSeek Reasoner",
                description="DeepSeek推理模型，擅长逻辑推理",
                supported_features=["生成", "评审", "推理"],
                is_available=True
            ),
        ])
    
    # Moonshot 模型
    if settings.moonshot_api_key:
        models.extend([
            AvailableModel(
                provider=ModelProvider.MOONSHOT,
                model_name="moonshot-v1-8k",
                display_name="Moonshot 8K",
                description="月之暗面8K上下文模型",
                supported_features=["生成", "评审", "长文本"],
                is_available=True
            ),
            AvailableModel(
                provider=ModelProvider.MOONSHOT,
                model_name="moonshot-v1-32k",
                display_name="Moonshot 32K",
                description="月之暗面32K上下文模型",
                supported_features=["生成", "评审", "长文本"],
                is_available=True
            ),
            AvailableModel(
                provider=ModelProvider.MOONSHOT,
                model_name="moonshot-v1-128k",
                display_name="Moonshot 128K",
                description="月之暗面128K超长上下文模型",
                supported_features=["生成", "评审", "超长文本"],
                is_available=True
            ),
        ])
    
    # Qwen 模型
    if settings.dashscope_api_key:
        models.extend([
            AvailableModel(
                provider=ModelProvider.QWEN,
                model_name="qwen-plus",
                display_name="通义千问 Plus",
                description="通义千问增强版，擅长长文本生成",
                supported_features=["生成", "评审", "长文本"],
                is_available=True
            ),
            AvailableModel(
                provider=ModelProvider.QWEN,
                model_name="qwen-turbo",
                display_name="通义千问 Turbo",
                description="通义千问快速版，适合快速响应",
                supported_features=["生成", "评审", "快速响应"],
                is_available=True
            ),
            AvailableModel(
                provider=ModelProvider.QWEN,
                model_name="qwen-max",
                display_name="通义千问 Max",
                description="通义千问旗舰版，效果最好",
                supported_features=["生成", "评审", "复杂推理"],
                is_available=True
            ),
            AvailableModel(
                provider=ModelProvider.QWEN,
                model_name="qwen-max-long",
                display_name="通义千问 Max-Long",
                description="通义千问长文本版，100万字上下文",
                supported_features=["生成", "评审", "超长文本"],
                is_available=True
            ),
        ])
    
    return models


@router.get("/available", response_model=ModelListResponse)
async def get_available_models():
    """
    获取可用模型列表

    返回：
    - requirement_analyze_models: 可用于需求分析的模型列表
    - testcase_generate_models: 可用于用例生成的模型列表
    - testcase_review_models: 可用于用例评审的模型列表
    - default_requirement_analyze: 默认需求分析模型的提供商
    - default_testcase_generate: 默认用例生成模型的提供商
    - default_testcase_review: 默认用例评审模型的提供商
    """
    all_models = get_all_available_models()

    # 添加自定义模型
    try:
        custom_models = await CustomModel.filter(enabled=True).all()
        for cm in custom_models:
            all_models.append(AvailableModel(
                provider=ModelProvider.CUSTOM,
                model_name=cm.default_model,
                display_name=cm.display_name,
                description=cm.description or f"自定义模型: {cm.name}",
                supported_features=["生成", "评审"],
                is_available=True,
                custom_id=cm.id,
            ))
    except Exception:
        pass  # 数据库可能还没初始化

    if not all_models:
        return ModelListResponse(
            requirement_analyze_models=[],
            testcase_generate_models=[],
            testcase_review_models=[],
            default_requirement_analyze=ModelProvider.DEEPSEEK,
            default_testcase_generate=ModelProvider.DEEPSEEK,
            default_testcase_review=ModelProvider.MOONSHOT,
        )

    # 查找默认模型提供商
    # 使用配置中的默认值
    default_generate_provider = settings.generate_model_provider
    default_review_provider = settings.review_model_provider

    # 验证默认模型是否可用
    has_default_generate = any(m.provider == default_generate_provider for m in all_models)
    has_default_review = any(m.provider == default_review_provider for m in all_models)

    # 如果默认生成模型不可用，尝试使用其他可用模型
    if not has_default_generate and all_models:
        default_generate_provider = all_models[0].provider

    # 如果默认评审模型不可用，尝试使用其他可用模型
    if not has_default_review and all_models:
        # 优先使用与生成模型不同的模型进行评审
        available_providers = [m.provider for m in all_models]
        for provider in available_providers:
            if provider != default_generate_provider and provider != ModelProvider.CUSTOM:
                default_review_provider = provider
                break
        else:
            # 如果都是自定义模型或没有其他选项，使用第一个非自定义模型
            for provider in available_providers:
                if provider != default_generate_provider:
                    default_review_provider = provider
                    break
            else:
                default_review_provider = available_providers[0] if available_providers else default_generate_provider

    # 三种场景使用相同的模型列表
    return ModelListResponse(
        requirement_analyze_models=all_models,
        testcase_generate_models=all_models,
        testcase_review_models=all_models,
        default_requirement_analyze=default_generate_provider,
        default_testcase_generate=default_generate_provider,
        default_testcase_review=default_review_provider,
    )


@router.get("/providers")
async def get_model_providers():
    """
    获取模型提供商列表
    
    返回支持的模型提供商及其配置状态
    """
    return {
        "providers": [
            {
                "name": "deepseek",
                "display_name": "DeepSeek",
                "description": "深度求索，擅长创意和分析",
                "configured": bool(settings.deepseek_api_key),
                "default_model": settings.deepseek_model,
            },
            {
                "name": "moonshot",
                "display_name": "Moonshot AI",
                "description": "月之暗面，擅长长文本和JSON输出",
                "configured": bool(settings.moonshot_api_key),
                "default_model": settings.moonshot_model,
            },
            {
                "name": "qwen",
                "display_name": "通义千问",
                "description": "阿里云大模型，稳定可靠",
                "configured": bool(settings.dashscope_api_key),
                "default_model": settings.qwen_model,
            },
        ]
    }
