"""
LLM模型配置服务
"""
from typing import List, Optional, Dict, Any
from loguru import logger

from app.models.llm_model import LLMModelConfig
from app.models.default_model import DefaultModelConfig
from autogen_ext.models.openai import OpenAIChatCompletionClient


class LLMModelService:
    """LLM模型配置服务"""

    @staticmethod
    async def get_all_models() -> List[LLMModelConfig]:
        """获取所有LLM模型配置"""
        return await LLMModelConfig.all()

    @staticmethod
    async def get_enabled_models() -> List[LLMModelConfig]:
        """获取所有启用的LLM模型配置"""
        return await LLMModelConfig.filter(enabled=True)

    @staticmethod
    async def get_model_by_name(name: str) -> Optional[LLMModelConfig]:
        """根据名称获取模型配置"""
        return await LLMModelConfig.get_or_none(name=name)

    @staticmethod
    async def get_model_by_id(id: int) -> Optional[LLMModelConfig]:
        """根据ID获取模型配置"""
        return await LLMModelConfig.get_or_none(id=id)

    @staticmethod
    async def create_model(
        name: str,
        display_name: str,
        provider: str,
        base_url: str,
        api_key: Optional[str],
        default_model: str,
        description: str = None,
        enabled: bool = True,
    ) -> LLMModelConfig:
        """创建LLM模型配置"""
        model = await LLMModelConfig.create(
            name=name,
            display_name=display_name,
            provider=provider,
            base_url=base_url,
            api_key=api_key,  # Ollama 本地模型可以为 None
            default_model=default_model,
            description=description,
            enabled=enabled,
        )
        logger.info(f"创建LLM模型配置: {name}")
        return model

    @staticmethod
    async def update_model(
        id: int,
        display_name: str = None,
        provider: str = None,
        base_url: str = None,
        api_key: str = None,
        default_model: str = None,
        description: str = None,
        enabled: bool = None,
    ) -> Optional[LLMModelConfig]:
        """更新LLM模型配置"""
        model = await LLMModelConfig.get_or_none(id=id)
        if not model:
            return None

        update_data = {}
        if display_name is not None:
            update_data["display_name"] = display_name
        if provider is not None:
            update_data["provider"] = provider
        if base_url is not None:
            update_data["base_url"] = base_url
        if api_key is not None:
            update_data["api_key"] = api_key
            logger.info(f"更新API Key: 长度={len(api_key)}")
        if default_model is not None:
            update_data["default_model"] = default_model
        if description is not None:
            update_data["description"] = description
        if enabled is not None:
            update_data["enabled"] = enabled

        if update_data:
            await model.update_from_dict(update_data)
            await model.save()
            logger.info(f"更新LLM模型配置: {model.name}, 更新字段={list(update_data.keys())}")

        return model

    @staticmethod
    async def delete_model(id: int) -> bool:
        """删除LLM模型配置"""
        model = await LLMModelConfig.get_or_none(id=id)
        if not model:
            return False

        await model.delete()
        logger.info(f"删除LLM模型配置: {model.name}")
        return True

    @staticmethod
    async def test_connection(
        base_url: str,
        api_key: Optional[str],
        model: str,
        provider: str = "custom",
    ) -> Dict[str, Any]:
        """测试模型连接"""
        try:
            # Ollama 本地模型不需要 API Key
            if api_key is None or api_key == "":
                api_key = "ollama"  # Ollama API 接受任意非空字符串作为 api_key
            
            logger.info(f"测试模型连接: base_url={base_url}, model={model}, provider={provider}, api_key长度={len(api_key) if api_key else 0}")
            
            client = OpenAIChatCompletionClient(
                model=model,
                base_url=base_url,
                api_key=api_key,
                model_info={
                    "vision": False,
                    "function_calling": True,
                    "json_output": True,
                    "structured_output": True,
                    "family": provider,
                }
            )

            # 发送一个简单的测试请求
            from autogen_core.models import UserMessage
            response = await client.create(
                messages=[UserMessage(content="Hello", source="user")]
            )

            return {
                "success": True,
                "message": "连接成功",
                "response": response.content[:100] if response.content else "",
            }
        except Exception as e:
            logger.error(f"模型连接测试失败: {e}")
            return {
                "success": False,
                "message": f"连接失败: {str(e)}",
            }

    @staticmethod
    async def get_default_model(purpose: str) -> Optional[LLMModelConfig]:
        """获取指定用途的默认模型"""
        default_config = await DefaultModelConfig.get_or_none(purpose=purpose)
        if not default_config or default_config.model_type != "llm":
            return None

        return await LLMModelConfig.get_or_none(
            name=default_config.model_name,
            enabled=True
        )

    @staticmethod
    async def set_default_model(purpose: str, model_name: str) -> bool:
        """设置指定用途的默认模型"""
        # 验证模型存在
        model = await LLMModelConfig.get_or_none(name=model_name, enabled=True)
        if not model:
            return False

        # 更新或创建默认配置
        default_config = await DefaultModelConfig.get_or_none(purpose=purpose)
        if default_config:
            default_config.model_name = model_name
            default_config.model_type = "llm"
            await default_config.save()
        else:
            await DefaultModelConfig.create(
                purpose=purpose,
                model_name=model_name,
                model_type="llm"
            )

        logger.info(f"设置默认模型: {purpose} -> {model_name}")
        return True

    @staticmethod
    async def get_all_default_configs() -> List[DefaultModelConfig]:
        """获取所有默认模型配置"""
        return await DefaultModelConfig.all()

    @staticmethod
    async def get_model_for_purpose(purpose: str) -> Optional[LLMModelConfig]:
        """
        获取指定用途的模型配置
        
        用途说明：
        - requirement_analyze: 需求分析模型
        - testcase_generate: 用例生成模型
        - testcase_review: 用例评审模型
        """
        # 先尝试从默认配置获取
        model = await LLMModelService.get_default_model(purpose)
        if model:
            logger.info(f"从默认配置获取模型: purpose={purpose}, model={model.name}")
            return model

        # 如果没有设置默认配置，返回第一个启用的模型
        enabled_models = await LLMModelConfig.filter(enabled=True).first()
        if enabled_models:
            logger.info(f"使用第一个启用的模型作为备选: purpose={purpose}, model={enabled_models.name}")
            return enabled_models
        
        logger.warning(f"未找到可用的模型配置: purpose={purpose}")
        return None

    @staticmethod
    async def get_or_create_default_models() -> List[LLMModelConfig]:
        """获取或创建默认模型配置（用于初始化）- 已禁用自动创建"""
        # 已禁用默认模型自动创建，用户需要手动添加模型
        return []

    @staticmethod
    async def create_client(model_name: str) -> Optional[OpenAIChatCompletionClient]:
        """根据模型名称创建模型客户端"""
        model = await LLMModelConfig.get_or_none(name=model_name, enabled=True)
        if not model:
            logger.warning(f"模型不存在或已禁用: {model_name}")
            return None

        try:
            # Ollama 本地模型不需要 API Key
            api_key = model.api_key
            if not api_key and model.provider == "ollama":
                api_key = "ollama"  # Ollama API 接受任意非空字符串

            client = OpenAIChatCompletionClient(
                model=model.default_model,
                base_url=model.base_url,
                api_key=api_key,
                model_info={
                    "vision": False,
                    "function_calling": True,
                    "json_output": True,
                    "structured_output": True,
                    "family": model.provider,
                }
            )
            logger.info(f"创建模型客户端成功: {model_name}")
            return client
        except Exception as e:
            logger.error(f"创建模型客户端失败: {e}")
            return None
