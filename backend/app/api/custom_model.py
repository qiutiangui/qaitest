"""
自定义模型管理API
支持用户添加、查看、删除自定义AI模型
"""
from fastapi import APIRouter, HTTPException
from typing import List
from loguru import logger
import httpx

from app.models.custom_model import CustomModel
from app.schemas.model_config import (
    CustomModelCreate,
    CustomModelUpdate,
    CustomModelResponse,
    ModelProvider,
    AvailableModel,
)
from app.api.model_config import get_all_available_models

router = APIRouter(prefix="", tags=["自定义模型管理"])


@router.get("/", response_model=List[CustomModelResponse])
async def list_custom_models():
    """
    获取用户自定义模型列表
    """
    try:
        models = await CustomModel.all().order_by("-created_at")
        return models
    except Exception as e:
        logger.error(f"获取自定义模型列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取模型列表失败")


@router.post("/", response_model=CustomModelResponse)
async def create_custom_model(model_data: CustomModelCreate):
    """
    添加自定义模型
    
    - name: 模型标识（唯一），如 "kimi"、"zhipu"
    - display_name: 显示名称，如 "Kimi AI"
    - base_url: API地址，如 "https://api.moonshot.cn/v1"
    - api_key: API密钥
    - default_model: 默认模型名，如 "moonshot-v1-8k"
    - description: 模型描述（可选）
    """
    try:
        # 检查名称是否已存在
        existing = await CustomModel.filter(name=model_data.name).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"模型标识 '{model_data.name}' 已存在")
        
        # 创建新模型
        new_model = await CustomModel.create(
            name=model_data.name,
            display_name=model_data.display_name,
            base_url=model_data.base_url,
            api_key=model_data.api_key,
            default_model=model_data.default_model,
            description=model_data.description or "",
            enabled=True,
        )
        logger.info(f"创建自定义模型成功: {new_model.name}")
        return new_model
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建自定义模型失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建模型失败: {str(e)}")


@router.get("/{model_id}", response_model=CustomModelResponse)
async def get_custom_model(model_id: int):
    """
    获取指定自定义模型详情
    """
    model = await CustomModel.get_or_none(id=model_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    return model


@router.put("/{model_id}", response_model=CustomModelResponse)
async def update_custom_model(model_id: int, update_data: CustomModelUpdate):
    """
    更新自定义模型配置
    """
    model = await CustomModel.get_or_none(id=model_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    try:
        # 更新字段
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(model, field, value)
        await model.save()
        logger.info(f"更新自定义模型成功: {model.name}")
        return model
    except Exception as e:
        logger.error(f"更新自定义模型失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新模型失败: {str(e)}")


@router.delete("/{model_id}")
async def delete_custom_model(model_id: int):
    """
    删除自定义模型
    """
    model = await CustomModel.get_or_none(id=model_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    try:
        model_name = model.name
        await model.delete()
        logger.info(f"删除自定义模型成功: {model_name}")
        return {"message": "删除成功", "name": model_name}
    except Exception as e:
        logger.error(f"删除自定义模型失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除模型失败: {str(e)}")


@router.post("/{model_id}/toggle")
async def toggle_custom_model(model_id: int):
    """
    启用/禁用自定义模型
    """
    model = await CustomModel.get_or_none(id=model_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    model.enabled = not model.enabled
    await model.save()
    status = "启用" if model.enabled else "禁用"
    logger.info(f"{status}自定义模型: {model.name}")
    return {"message": f"{status}成功", "enabled": model.enabled}


@router.post("/{model_id}/test")
async def test_custom_model(model_id: int):
    """
    测试自定义模型连接
    """
    model = await CustomModel.get_or_none(id=model_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{model.base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {model.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model.default_model,
                    "messages": [{"role": "user", "content": "你好"}],
                    "max_tokens": 10,
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")[:100]
                return {"success": True, "message": "连接成功", "response": content}
            else:
                return {"success": False, "message": f"请求失败: {response.status_code} - {response.text[:200]}"}
    except httpx.ConnectError:
        return {"success": False, "message": f"无法连接到 {model.base_url}，请检查地址是否正确"}
    except httpx.TimeoutException:
        return {"success": False, "message": "连接超时，请检查网络或服务是否正常"}
    except Exception as e:
        return {"success": False, "message": f"测试失败: {str(e)[:200]}"}


@router.post("/test-connection")
async def test_connection(data: CustomModelCreate):
    """
    测试自定义模型连接（创建前测试）
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{data.base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {data.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": data.default_model,
                    "messages": [{"role": "user", "content": "你好"}],
                    "max_tokens": 10,
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")[:100]
                return {"success": True, "message": "连接成功", "response": content}
            else:
                return {"success": False, "message": f"请求失败: {response.status_code} - {response.text[:200]}"}
    except httpx.ConnectError:
        return {"success": False, "message": f"无法连接到 {data.base_url}，请检查地址是否正确"}
    except httpx.TimeoutException:
        return {"success": False, "message": "连接超时，请检查网络或服务是否正常"}
    except Exception as e:
        return {"success": False, "message": f"测试失败: {str(e)[:200]}"}


@router.get("/all/available", response_model=List[AvailableModel])
async def get_all_models_with_custom():
    """
    获取所有可用模型（包括内置和自定义）
    """
    models = await get_all_available_models()
    
    # 添加自定义模型
    custom_models = await CustomModel.filter(enabled=True).all()
    for cm in custom_models:
        models.append(AvailableModel(
            provider=ModelProvider.CUSTOM,
            model_name=cm.default_model,
            display_name=cm.display_name,
            description=cm.description or f"自定义模型: {cm.name}",
            supported_features=["生成", "评审"],
            is_available=True,
            custom_id=cm.id,
        ))
    
    return models
