"""
嵌入模型配置服务
"""
from typing import List, Optional, Dict, Any
from loguru import logger

from app.models.embedding_model import EmbeddingModelConfig
from app.models.default_model import DefaultModelConfig


class EmbeddingModelService:
    """嵌入模型配置服务"""

    @staticmethod
    async def get_all_configs() -> List[EmbeddingModelConfig]:
        """获取所有嵌入模型配置"""
        return await EmbeddingModelConfig.all()

    @staticmethod
    async def get_enabled_configs() -> List[EmbeddingModelConfig]:
        """获取所有启用的嵌入模型配置"""
        return await EmbeddingModelConfig.filter(enabled=True)

    @staticmethod
    async def get_config_by_name(name: str) -> Optional[EmbeddingModelConfig]:
        """根据名称获取嵌入模型配置"""
        return await EmbeddingModelConfig.get_or_none(name=name)

    @staticmethod
    async def get_config_by_id(id: int) -> Optional[EmbeddingModelConfig]:
        """根据ID获取嵌入模型配置"""
        return await EmbeddingModelConfig.get_or_none(id=id)

    @staticmethod
    async def get_default_config() -> Optional[EmbeddingModelConfig]:
        """获取默认嵌入模型配置"""
        # 优先从 DefaultModelConfig 获取
        default_config = await DefaultModelConfig.get_or_none(purpose="embedding")
        if default_config:
            config = await EmbeddingModelConfig.get_or_none(
                name=default_config.model_name,
                enabled=True
            )
            if config:
                return config

        # 回退到 is_default 标记
        config = await EmbeddingModelConfig.get_or_none(is_default=True, enabled=True)
        if config:
            return config

        # 返回第一个启用的配置
        return await EmbeddingModelConfig.filter(enabled=True).first()

    @staticmethod
    async def create_config(
        name: str,
        display_name: str,
        provider: str,
        api_base: str,
        api_key: str,
        model_name: str,
        dimension: int = 1024,
        description: str = None,
        enabled: bool = True,
        is_default: bool = False,
    ) -> EmbeddingModelConfig:
        """创建嵌入模型配置"""
        # 如果设置为默认，需要取消其他默认配置
        if is_default:
            await EmbeddingModelConfig.all().update(is_default=False)
            # 同步更新 DefaultModelConfig
            await DefaultModelConfig.filter(purpose="embedding").delete()
            await DefaultModelConfig.create(
                purpose="embedding",
                model_name=name,
                model_type="embedding"
            )

        config = await EmbeddingModelConfig.create(
            name=name,
            display_name=display_name,
            provider=provider,
            api_base=api_base,
            api_key=api_key,
            model_name=model_name,
            dimension=dimension,
            description=description,
            enabled=enabled,
            is_default=is_default,
        )
        logger.info(f"创建嵌入模型配置: {name}")
        return config

    @staticmethod
    async def update_config(
        id: int,
        display_name: str = None,
        provider: str = None,
        api_base: str = None,
        api_key: str = None,
        model_name: str = None,
        dimension: int = None,
        description: str = None,
        enabled: bool = None,
        is_default: bool = None,
    ) -> Optional[EmbeddingModelConfig]:
        """更新嵌入模型配置"""
        config = await EmbeddingModelConfig.get_or_none(id=id)
        if not config:
            return None

        update_data = {}
        if display_name is not None:
            update_data["display_name"] = display_name
        if provider is not None:
            update_data["provider"] = provider
        if api_base is not None:
            update_data["api_base"] = api_base
        if api_key is not None:
            update_data["api_key"] = api_key
        if model_name is not None:
            update_data["model_name"] = model_name
        if dimension is not None:
            update_data["dimension"] = dimension
        if description is not None:
            update_data["description"] = description
        if enabled is not None:
            update_data["enabled"] = enabled
        if is_default is not None:
            update_data["is_default"] = is_default
            # 如果设置为默认，需要取消其他默认配置并更新 DefaultModelConfig
            if is_default:
                await EmbeddingModelConfig.all().update(is_default=False)
                await DefaultModelConfig.filter(purpose="embedding").delete()
                await DefaultModelConfig.create(
                    purpose="embedding",
                    model_name=config.name,
                    model_type="embedding"
                )

        if update_data:
            await config.update_from_dict(update_data)
            await config.save()
            logger.info(f"更新嵌入模型配置: {config.name}")

        return config

    @staticmethod
    async def delete_config(id: int) -> bool:
        """删除嵌入模型配置"""
        config = await EmbeddingModelConfig.get_or_none(id=id)
        if not config:
            return False

        # 删除关联的默认模型配置
        await DefaultModelConfig.filter(
            model_name=config.name,
            model_type="embedding"
        ).delete()

        await config.delete()
        logger.info(f"删除嵌入模型配置: {config.name}")
        return True

    @staticmethod
    async def set_default_config(name: str) -> bool:
        """设置默认嵌入模型"""
        config = await EmbeddingModelConfig.get_or_none(name=name, enabled=True)
        if not config:
            return False

        # 取消其他默认配置
        await EmbeddingModelConfig.all().update(is_default=False)

        # 设置新的默认配置
        config.is_default = True
        await config.save()

        # 更新 DefaultModelConfig
        default_config = await DefaultModelConfig.get_or_none(purpose="embedding")
        if default_config:
            default_config.model_name = name
            default_config.model_type = "embedding"
            await default_config.save()
        else:
            await DefaultModelConfig.create(
                purpose="embedding",
                model_name=name,
                model_type="embedding"
            )

        logger.info(f"设置默认嵌入模型: {name}")
        return True

    @staticmethod
    async def test_connection(
        api_base: str,
        api_key: str,
        model_name: str,
        provider: str = "dashscope",
        dimension: int = 1024,
    ) -> Dict[str, Any]:
        """测试嵌入模型连接"""
        try:
            from app.rag.llama_embeddings import QwenEmbeddingModel, OllamaEmbeddingModel

            # 根据 provider 选择不同的嵌入模型
            if provider == "ollama":
                embedding_model = OllamaEmbeddingModel(
                    model_name=model_name,
                    api_base=api_base,
                    dimension=dimension,
                )
            else:
                embedding_model = QwenEmbeddingModel(
                    api_key=api_key,
                    model_name=model_name,
                    api_base=api_base,
                    dimension=dimension,
                )

            # 测试嵌入
            test_text = "测试连接"
            embedding = await embedding_model._get_embedding(test_text)

            return {
                "success": True,
                "message": "连接成功",
                "embedding_dim": len(embedding) if embedding else 0,
            }
        except Exception as e:
            logger.error(f"嵌入模型连接测试失败: {e}")
            return {
                "success": False,
                "message": f"连接失败: {str(e)}",
            }

    @staticmethod
    async def get_or_create_default_configs() -> List[EmbeddingModelConfig]:
        """获取或创建默认嵌入模型配置（用于初始化）- 已禁用自动创建"""
        # 已禁用默认嵌入模型自动创建，用户需要手动添加模型
        return []

    @staticmethod
    async def get_embedding_config() -> Optional[EmbeddingModelConfig]:
        """获取嵌入模型配置（兼容旧接口）"""
        return await EmbeddingModelService.get_default_config()
