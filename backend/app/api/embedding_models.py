"""
嵌入模型配置管理API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from loguru import logger

from app.services.embedding_model_service import EmbeddingModelService

router = APIRouter(prefix="/api/v1/embedding-models", tags=["嵌入模型配置"])


# ============ Pydantic Schemas ============

class EmbeddingModelCreate(BaseModel):
    name: str
    display_name: str
    provider: str
    api_base: str
    api_key: Optional[str] = None
    model_name: str
    dimension: int = 1024
    description: Optional[str] = None
    enabled: bool = True
    is_default: bool = False


class EmbeddingModelUpdate(BaseModel):
    display_name: Optional[str] = None
    provider: Optional[str] = None
    api_base: Optional[str] = None
    api_key: Optional[str] = None
    model_name: Optional[str] = None
    dimension: Optional[int] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    is_default: Optional[bool] = None


class EmbeddingModelTest(BaseModel):
    api_base: str
    api_key: Optional[str] = None  # Ollama 本地模型不需要 API Key
    model_name: str
    provider: Optional[str] = "dashscope"
    dimension: Optional[int] = 1024


# ============ API Endpoints ============

@router.get("", response_model=List[dict])
async def get_embedding_models():
    """获取所有嵌入模型配置"""
    configs = await EmbeddingModelService.get_all_configs()
    return [
        {
            "id": c.id,
            "name": c.name,
            "display_name": c.display_name,
            "provider": c.provider,
            "api_base": c.api_base,
            "api_key": "****" if c.api_key else None,
            "model_name": c.model_name,
            "dimension": c.dimension,
            "description": c.description,
            "enabled": c.enabled,
            "is_default": c.is_default,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        }
        for c in configs
    ]


@router.get("/enabled", response_model=List[dict])
async def get_enabled_embedding_models():
    """获取所有启用的嵌入模型配置"""
    configs = await EmbeddingModelService.get_enabled_configs()
    return [
        {
            "id": c.id,
            "name": c.name,
            "display_name": c.display_name,
            "provider": c.provider,
            "model_name": c.model_name,
            "dimension": c.dimension,
            "description": c.description,
        }
        for c in configs
    ]


@router.get("/default", response_model=dict)
async def get_default_embedding_model():
    """获取默认嵌入模型配置"""
    config = await EmbeddingModelService.get_default_config()
    if not config:
        return {
            "configured": False,
            "message": "未配置嵌入模型",
        }
    
    return {
        "configured": True,
        "model": {
            "id": config.id,
            "name": config.name,
            "display_name": config.display_name,
            "provider": config.provider,
            "model_name": config.model_name,
            "dimension": config.dimension,
        },
    }


@router.get("/{config_id}", response_model=dict)
async def get_embedding_model(config_id: int):
    """获取单个嵌入模型配置"""
    config = await EmbeddingModelService.get_config_by_id(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="嵌入模型配置不存在")
    
    return {
        "id": config.id,
        "name": config.name,
        "display_name": config.display_name,
        "provider": config.provider,
        "api_base": config.api_base,
        "api_key": "****" if config.api_key else None,
        "model_name": config.model_name,
        "dimension": config.dimension,
        "description": config.description,
        "enabled": config.enabled,
        "is_default": config.is_default,
        "created_at": config.created_at.isoformat() if config.created_at else None,
        "updated_at": config.updated_at.isoformat() if config.updated_at else None,
    }


@router.post("", response_model=dict)
async def create_embedding_model(model_data: EmbeddingModelCreate):
    """创建嵌入模型配置"""
    try:
        config = await EmbeddingModelService.create_config(
            name=model_data.name,
            display_name=model_data.display_name,
            provider=model_data.provider,
            api_base=model_data.api_base,
            api_key=model_data.api_key,
            model_name=model_data.model_name,
            dimension=model_data.dimension,
            description=model_data.description,
            enabled=model_data.enabled,
            is_default=model_data.is_default,
        )
        return {
            "id": config.id,
            "name": config.name,
            "display_name": config.display_name,
            "message": "创建成功",
        }
    except Exception as e:
        logger.error(f"创建嵌入模型配置失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{config_id}", response_model=dict)
async def update_embedding_model(config_id: int, model_data: EmbeddingModelUpdate):
    """更新嵌入模型配置"""
    try:
        config = await EmbeddingModelService.update_config(
            id=config_id,
            display_name=model_data.display_name,
            provider=model_data.provider,
            api_base=model_data.api_base,
            api_key=model_data.api_key,
            model_name=model_data.model_name,
            dimension=model_data.dimension,
            description=model_data.description,
            enabled=model_data.enabled,
            is_default=model_data.is_default,
        )
        if not config:
            raise HTTPException(status_code=404, detail="嵌入模型配置不存在")
        
        return {
            "id": config.id,
            "name": config.name,
            "message": "更新成功",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新嵌入模型配置失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{config_id}")
async def delete_embedding_model(config_id: int):
    """删除嵌入模型配置"""
    success = await EmbeddingModelService.delete_config(config_id)
    if not success:
        raise HTTPException(status_code=404, detail="嵌入模型配置不存在")
    return {"message": "删除成功"}


@router.post("/test", response_model=dict)
async def test_embedding_connection(test_data: EmbeddingModelTest):
    """测试嵌入模型连接"""
    # 获取 provider（如果提供了 api_base，可以推断）
    provider = test_data.provider if test_data.provider else "dashscope"
    dimension = test_data.dimension if test_data.dimension else 1024
    
    result = await EmbeddingModelService.test_connection(
        api_base=test_data.api_base,
        api_key=test_data.api_key or "",
        model_name=test_data.model_name,
        provider=provider,
        dimension=dimension,
    )
    return result


@router.put("/default/{name}", response_model=dict)
async def set_default_embedding_model(name: str):
    """设置默认嵌入模型"""
    success = await EmbeddingModelService.set_default_config(name)
    if not success:
        raise HTTPException(status_code=400, detail="设置失败，嵌入模型不存在或已禁用")
    
    return {"message": "设置成功", "name": name}
