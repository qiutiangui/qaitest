"""
模型配置初始化脚本

用于在系统首次启动时创建默认的模型配置
可以通过调用 API 端点 /api/v1/model-status/initialize 来触发初始化
"""
from typing import List, Dict, Any
from loguru import logger

# 默认LLM模型配置（已禁用自动初始化，由用户手动添加）
DEFAULT_LLM_MODELS: List[Dict[str, Any]] = []

# 默认嵌入模型配置（已禁用自动初始化，由用户手动添加）
DEFAULT_EMBEDDING_CONFIGS: List[Dict[str, Any]] = []

# 默认用途模型配置（已禁用自动初始化，由用户手动添加）
DEFAULT_PURPOSE_MAPPINGS: List[Dict[str, str]] = []


async def initialize_llm_models() -> tuple[int, List[str]]:
    """
    初始化默认LLM模型配置

    Returns:
        (创建数量, 模型名称列表)
    """
    from app.models.llm_model import LLMModelConfig

    created_count = 0
    created_names = []

    for model_data in DEFAULT_LLM_MODELS:
        existing = await LLMModelConfig.get_or_none(name=model_data["name"])
        if not existing:
            await LLMModelConfig.create(**model_data)
            created_count += 1
            created_names.append(model_data["name"])
            logger.info(f"创建默认LLM模型: {model_data['name']}")
        else:
            logger.debug(f"LLM模型已存在: {model_data['name']}")

    return created_count, created_names


async def initialize_embedding_configs() -> tuple[int, List[str]]:
    """
    初始化默认嵌入模型配置

    Returns:
        (创建数量, 配置名称列表)
    """
    from app.models.embedding_model import EmbeddingModelConfig

    created_count = 0
    created_names = []

    for config_data in DEFAULT_EMBEDDING_CONFIGS:
        existing = await EmbeddingModelConfig.get_or_none(name=config_data["name"])
        if not existing:
            await EmbeddingModelConfig.create(**config_data)
            created_count += 1
            created_names.append(config_data["name"])
            logger.info(f"创建默认嵌入模型配置: {config_data['name']}")
        else:
            logger.debug(f"嵌入模型配置已存在: {config_data['name']}")

    return created_count, created_names


async def initialize_purpose_mappings() -> tuple[int, List[str]]:
    """
    初始化默认用途模型映射

    Returns:
        (创建数量, 用途列表)
    """
    from app.models.default_model import DefaultModelConfig

    created_count = 0
    created_purposes = []

    for mapping in DEFAULT_PURPOSE_MAPPINGS:
        existing = await DefaultModelConfig.get_or_none(purpose=mapping["purpose"])
        if not existing:
            await DefaultModelConfig.create(**mapping)
            created_count += 1
            created_purposes.append(mapping["purpose"])
            logger.info(f"创建默认用途映射: {mapping['purpose']} -> {mapping['model_name']}")
        else:
            logger.debug(f"用途映射已存在: {mapping['purpose']}")

    return created_count, created_purposes


async def initialize_all_model_configs() -> Dict[str, Any]:
    """
    初始化所有模型配置

    Returns:
        初始化结果统计
    """
    result = {
        "llm_models": {"created": 0, "total": len(DEFAULT_LLM_MODELS)},
        "embedding_configs": {"created": 0, "total": len(DEFAULT_EMBEDDING_CONFIGS)},
        "purpose_mappings": {"created": 0, "total": len(DEFAULT_PURPOSE_MAPPINGS)},
    }

    try:
        # 初始化LLM模型
        llm_count, llm_names = await initialize_llm_models()
        result["llm_models"]["created"] = llm_count

        # 初始化嵌入模型
        emb_count, emb_names = await initialize_embedding_configs()
        result["embedding_configs"]["created"] = emb_count

        # 初始化用途映射
        map_count, map_purposes = await initialize_purpose_mappings()
        result["purpose_mappings"]["created"] = map_count

        result["success"] = True
        result["message"] = "模型配置初始化完成"

        logger.info(f"模型配置初始化完成: LLM模型 {llm_count}/{len(DEFAULT_LLM_MODELS)}, "
                   f"嵌入模型 {emb_count}/{len(DEFAULT_EMBEDDING_CONFIGS)}, "
                   f"用途映射 {map_count}/{len(DEFAULT_PURPOSE_MAPPINGS)}")

    except Exception as e:
        result["success"] = False
        result["message"] = f"初始化失败: {str(e)}"
        logger.error(f"模型配置初始化失败: {e}")

    return result


async def check_and_initialize_if_needed() -> Dict[str, Any]:
    """
    检查并初始化模型配置（如果需要）

    仅在没有任何模型配置时进行初始化
    """
    from app.models.llm_model import LLMModelConfig
    from app.models.embedding_model import EmbeddingModelConfig

    # 检查是否已有配置
    llm_count = await LLMModelConfig.all().count()
    emb_count = await EmbeddingModelConfig.all().count()

    if llm_count > 0 or emb_count > 0:
        return {
            "success": True,
            "message": "模型配置已存在，无需初始化",
            "already_initialized": True,
        }

    # 执行初始化
    return await initialize_all_model_configs()


# 导出配置模板供前端使用
def get_llm_model_templates() -> List[Dict[str, Any]]:
    """获取LLM模型配置模板"""
    return [
        {
            "provider": "deepseek",
            "display_name": "DeepSeek",
            "base_url": "https://api.deepseek.com/v1",
            "models": ["deepseek-chat", "deepseek-reasoner"],
        },
        {
            "provider": "moonshot",
            "display_name": "Moonshot AI",
            "base_url": "https://api.moonshot.cn/v1",
            "models": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
        },
        {
            "provider": "qwen",
            "display_name": "通义千问",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "models": ["qwen-turbo", "qwen-plus", "qwen-max", "qwen-max-longcontext"],
        },
        {
            "provider": "openai",
            "display_name": "OpenAI",
            "base_url": "https://api.openai.com/v1",
            "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
        },
        {
            "provider": "anthropic",
            "display_name": "Anthropic",
            "base_url": "https://api.anthropic.com/v1",
            "models": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229"],
        },
    ]


def get_embedding_model_templates() -> List[Dict[str, Any]]:
    """获取嵌入模型配置模板"""
    return [
        {
            "provider": "dashscope",
            "display_name": "阿里云 DashScope",
            "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "models": [
                {"name": "text-embedding-v3", "dimension": 1024},
                {"name": "text-embedding-v2", "dimension": 1536},
            ],
        },
        {
            "provider": "openai",
            "display_name": "OpenAI",
            "api_base": "https://api.openai.com/v1",
            "models": [
                {"name": "text-embedding-3-small", "dimension": 1536},
                {"name": "text-embedding-3-large", "dimension": 3072},
                {"name": "text-embedding-ada-002", "dimension": 1536},
            ],
        },
    ]
