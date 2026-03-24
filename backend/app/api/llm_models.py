"""
LLM模型配置管理API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from loguru import logger

from app.services.llm_model_service import LLMModelService

router = APIRouter(prefix="/api/v1/llm-models", tags=["LLM模型配置"])


# ============ Pydantic Schemas ============

class LLMModelCreate(BaseModel):
    name: str
    display_name: str
    provider: str
    base_url: str
    api_key: Optional[str] = None
    default_model: str
    description: Optional[str] = None
    enabled: bool = True


class LLMModelUpdate(BaseModel):
    display_name: Optional[str] = None
    provider: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    default_model: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None


class LLMModelTest(BaseModel):
    base_url: str
    api_key: Optional[str] = None  # Ollama 本地模型不需要 API Key
    model: str
    provider: Optional[str] = "custom"  # 提供商类型


class DefaultModelSet(BaseModel):
    model_name: str


# ============ API Endpoints ============

@router.get("", response_model=List[dict])
async def get_llm_models():
    """获取所有LLM模型配置"""
    models = await LLMModelService.get_all_models()
    return [
        {
            "id": m.id,
            "name": m.name,
            "display_name": m.display_name,
            "provider": m.provider,
            "base_url": m.base_url,
            "api_key": "****" if m.api_key else None,  # 隐藏敏感信息
            "default_model": m.default_model,
            "description": m.description,
            "enabled": m.enabled,
            "is_default": m.is_default,
            "created_at": m.created_at.isoformat() if m.created_at else None,
            "updated_at": m.updated_at.isoformat() if m.updated_at else None,
        }
        for m in models
    ]


@router.get("/enabled", response_model=List[dict])
async def get_enabled_models():
    """获取所有启用的LLM模型配置"""
    models = await LLMModelService.get_enabled_models()
    return [
        {
            "id": m.id,
            "name": m.name,
            "display_name": m.display_name,
            "provider": m.provider,
            "default_model": m.default_model,
            "description": m.description,
        }
        for m in models
    ]


@router.get("/{model_id}", response_model=dict)
async def get_llm_model(model_id: int):
    """获取单个LLM模型配置"""
    model = await LLMModelService.get_model_by_id(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    
    return {
        "id": model.id,
        "name": model.name,
        "display_name": model.display_name,
        "provider": model.provider,
        "base_url": model.base_url,
        "api_key": "****" if model.api_key else None,
        "default_model": model.default_model,
        "description": model.description,
        "enabled": model.enabled,
        "is_default": model.is_default,
        "created_at": model.created_at.isoformat() if model.created_at else None,
        "updated_at": model.updated_at.isoformat() if model.updated_at else None,
    }


@router.get("/{model_id}/for-test", response_model=dict)
async def get_llm_model_for_test(model_id: int):
    """获取单个LLM模型配置（包含真实api_key，用于测试连接）"""
    model = await LLMModelService.get_model_by_id(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    
    return {
        "id": model.id,
        "name": model.name,
        "display_name": model.display_name,
        "provider": model.provider,
        "base_url": model.base_url,
        "api_key": model.api_key,  # 返回真实 api_key
        "default_model": model.default_model,
    }


@router.post("", response_model=dict)
async def create_llm_model(model_data: LLMModelCreate):
    """创建LLM模型配置"""
    try:
        model = await LLMModelService.create_model(
            name=model_data.name,
            display_name=model_data.display_name,
            provider=model_data.provider,
            base_url=model_data.base_url,
            api_key=model_data.api_key,
            default_model=model_data.default_model,
            description=model_data.description,
            enabled=model_data.enabled,
        )
        return {
            "id": model.id,
            "name": model.name,
            "display_name": model.display_name,
            "message": "创建成功",
        }
    except Exception as e:
        logger.error(f"创建LLM模型配置失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{model_id}", response_model=dict)
async def update_llm_model(model_id: int, model_data: LLMModelUpdate):
    """更新LLM模型配置"""
    try:
        model = await LLMModelService.update_model(
            id=model_id,
            display_name=model_data.display_name,
            provider=model_data.provider,
            base_url=model_data.base_url,
            api_key=model_data.api_key,
            default_model=model_data.default_model,
            description=model_data.description,
            enabled=model_data.enabled,
        )
        if not model:
            raise HTTPException(status_code=404, detail="模型配置不存在")
        
        return {
            "id": model.id,
            "name": model.name,
            "message": "更新成功",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新LLM模型配置失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{model_id}")
async def delete_llm_model(model_id: int):
    """删除LLM模型配置"""
    success = await LLMModelService.delete_model(model_id)
    if not success:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    return {"message": "删除成功"}


@router.post("/{model_id}/test", response_model=dict)
async def test_llm_model_connection(model_id: int):
    """测试指定LLM模型连接（后端内部获取真实api_key）"""
    model = await LLMModelService.get_model_by_id(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    
    result = await LLMModelService.test_connection(
        base_url=model.base_url,
        api_key=model.api_key,
        model=model.default_model,
        provider=model.provider,
    )
    return result


@router.post("/test", response_model=dict)
async def test_llm_connection(test_data: LLMModelTest):
    """测试LLM模型连接（手动输入参数）"""
    result = await LLMModelService.test_connection(
        base_url=test_data.base_url,
        api_key=test_data.api_key,
        model=test_data.model,
        provider=test_data.provider or "custom",
    )
    return result


@router.get("/defaults/all", response_model=List[dict])
async def get_all_default_configs():
    """获取所有默认模型配置"""
    configs = await LLMModelService.get_all_default_configs()
    return [
        {
            "purpose": c.purpose,
            "model_name": c.model_name,
            "model_type": c.model_type,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        }
        for c in configs
    ]


@router.put("/defaults/{purpose}", response_model=dict)
async def set_default_model(purpose: str, data: DefaultModelSet):
    """设置指定用途的默认模型"""
    # 验证 purpose 是否有效
    valid_purposes = ["requirement_analyze", "testcase_generate", "testcase_review", "embedding"]
    if purpose not in valid_purposes:
        raise HTTPException(
            status_code=400,
            detail=f"无效的用途，有效值: {', '.join(valid_purposes)}"
        )

    # 如果是 embedding 用途，调用嵌入模型服务
    if purpose == "embedding":
        from app.services.embedding_model_service import EmbeddingModelService
        success = await EmbeddingModelService.set_default_config(data.model_name)
        if not success:
            raise HTTPException(status_code=400, detail="设置失败，模型不存在或已禁用")
        return {"message": "设置成功", "purpose": purpose, "model_name": data.model_name}

    # LLM 模型用途
    success = await LLMModelService.set_default_model(purpose, data.model_name)
    if not success:
        raise HTTPException(status_code=400, detail="设置失败，模型不存在或已禁用")

    return {"message": "设置成功", "purpose": purpose, "model_name": data.model_name}


@router.get("/purpose/{purpose}", response_model=dict)
async def get_model_for_purpose(purpose: str):
    """获取指定用途的模型"""
    # 如果是 embedding 用途，调用嵌入模型服务
    if purpose == "embedding":
        from app.services.embedding_model_service import EmbeddingModelService
        config = await EmbeddingModelService.get_default_config()
        if not config:
            return {
                "configured": False,
                "message": "未配置嵌入模型",
            }
        return {
            "configured": True,
            "model": {
                "name": config.name,
                "display_name": config.display_name,
                "provider": config.provider,
                "model_name": config.model_name,
                "dimension": config.dimension,
            },
        }

    # LLM 模型用途
    model = await LLMModelService.get_model_for_purpose(purpose)
    if not model:
        return {
            "configured": False,
            "message": "未配置该用途的模型",
        }

    return {
        "configured": True,
        "model": {
            "name": model.name,
            "display_name": model.display_name,
            "provider": model.provider,
            "default_model": model.default_model,
        },
    }
