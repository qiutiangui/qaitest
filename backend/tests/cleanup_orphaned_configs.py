"""
清理 default_model_configs 中指向已删除模型的脏数据
"""
import asyncio
from tortoise import Tortoise
from app.models.default_model import DefaultModelConfig
from app.models.llm_model import LLMModelConfig
from app.models.embedding_model import EmbeddingModelConfig
from loguru import logger


async def cleanup_orphaned_default_configs():
    """清理指向已删除模型的默认配置"""
    await Tortoise.init(db_url='mysql://root:test123456@8.148.248.39:3306/qaitest2', 
                        modules={'models': ['app.models']})
    await Tortoise.generate_schemas()
    
    try:
        # 获取所有默认配置
        all_defaults = await DefaultModelConfig.all()
        
        # 获取所有有效模型名称
        llm_models = await LLMModelConfig.all()
        embedding_models = await EmbeddingModelConfig.all()
        
        llm_names = {m.name for m in llm_models}
        embedding_names = {m.name for m in embedding_models}
        
        logger.info(f"LLM 模型数量: {len(llm_names)}, 名称: {llm_names}")
        logger.info(f"嵌入模型数量: {len(embedding_names)}, 名称: {embedding_names}")
        logger.info(f"默认配置记录数: {len(all_defaults)}")
        
        orphaned = []
        for config in all_defaults:
            is_orphan = False
            if config.model_type == "llm":
                if config.model_name not in llm_names:
                    is_orphan = True
            elif config.model_type == "embedding":
                if config.model_name not in embedding_names:
                    is_orphan = True
            
            if is_orphan:
                orphaned.append(config)
                logger.warning(f"发现孤立默认配置: id={config.id}, purpose={config.purpose}, "
                             f"model_name={config.model_name}, model_type={config.model_type}")
        
        # 删除孤立的配置
        if orphaned:
            for config in orphaned:
                await config.delete()
                logger.info(f"已删除孤立配置: purpose={config.purpose}, model_name={config.model_name}")
            logger.info(f"共清理 {len(orphaned)} 条孤立配置")
        else:
            logger.info("没有发现孤立的默认配置")
        
        return len(orphaned)
    
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    count = asyncio.run(cleanup_orphaned_default_configs())
    print(f"\n清理完成，共删除 {count} 条孤立配置")
