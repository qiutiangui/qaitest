"""
模型配置状态API
用于前端检查模型配置状态
"""
from fastapi import APIRouter
from loguru import logger

from app.services.llm_model_service import LLMModelService
from app.services.embedding_model_service import EmbeddingModelService
from app.config import settings

router = APIRouter(prefix="/api/v1/model-status", tags=["模型状态"])


@router.get("")
async def get_model_status():
    """
    获取模型配置状态
    
    返回各用途的模型配置状态，供前端判断是否需要引导用户配置模型
    """
    # 获取需求分析模型
    req_model = await LLMModelService.get_model_for_purpose("requirement_analyze")
    
    # 获取用例生成模型
    gen_model = await LLMModelService.get_model_for_purpose("testcase_generate")
    
    # 获取用例评审模型
    rev_model = await LLMModelService.get_model_for_purpose("testcase_review")
    
    # 获取嵌入模型
    emb_config = await EmbeddingModelService.get_default_config()
    
    # 构建状态
    # 注意：model_name 使用 default_model（实际 API 调用的模型名），如 ollama 模型需要 qwen2.5:7b-instruct
    status = {
        "requirement_analyze": {
            "configured": req_model is not None,
            "model": req_model.display_name if req_model else None,
            "model_name": req_model.default_model if req_model else None,
            "provider": req_model.provider if req_model else None,
            "id": req_model.id if req_model else None,
            "is_custom": req_model.provider == "custom" if req_model else False,
        },
        "testcase_generate": {
            "configured": gen_model is not None,
            "model": gen_model.display_name if gen_model else None,
            "model_name": gen_model.default_model if gen_model else None,
            "provider": gen_model.provider if gen_model else None,
            "id": gen_model.id if gen_model else None,
            "is_custom": gen_model.provider == "custom" if gen_model else False,
        },
        "testcase_review": {
            "configured": rev_model is not None,
            "model": rev_model.display_name if rev_model else None,
            "model_name": rev_model.default_model if rev_model else None,
            "provider": rev_model.provider if rev_model else None,
            "id": rev_model.id if rev_model else None,
            "is_custom": rev_model.provider == "custom" if rev_model else False,
        },
        "embedding": {
            "configured": emb_config is not None,
            "model": emb_config.display_name if emb_config else None,
            "model_name": emb_config.name if emb_config else None,
            "provider": emb_config.provider if emb_config else None,
            "dimension": emb_config.dimension if emb_config else None,
        },
    }
    
    # 判断是否所有必需的模型都已配置
    all_required_configured = (
        status["requirement_analyze"]["configured"] and
        status["testcase_generate"]["configured"] and
        status["testcase_review"]["configured"]
    )
    
    # RAG 功能需要嵌入模型
    rag_available = status["embedding"]["configured"]
    
    return {
        **status,
        "all_required_configured": all_required_configured,
        "rag_available": rag_available,
    }


@router.get("/summary")
async def get_model_status_summary():
    """
    获取模型配置状态摘要
    
    简化的状态信息，用于快速检查
    """
    status = await get_model_status()
    
    # 统计已配置和未配置的模型
    configured_count = sum(1 for key in ["requirement_analyze", "testcase_generate", "testcase_review", "embedding"] 
                          if status[key]["configured"])
    total_count = 4
    
    missing_models = []
    if not status["requirement_analyze"]["configured"]:
        missing_models.append({"purpose": "requirement_analyze", "display_name": "需求分析模型"})
    if not status["testcase_generate"]["configured"]:
        missing_models.append({"purpose": "testcase_generate", "display_name": "用例生成模型"})
    if not status["testcase_review"]["configured"]:
        missing_models.append({"purpose": "testcase_review", "display_name": "用例评审模型"})
    if not status["embedding"]["configured"]:
        missing_models.append({"purpose": "embedding", "display_name": "嵌入模型"})
    
    return {
        "configured_count": configured_count,
        "total_count": total_count,
        "all_configured": configured_count == total_count,
        "missing_models": missing_models,
    }


@router.post("/initialize")
async def initialize_default_models():
    """
    初始化默认模型配置
    
    创建系统默认的模型配置（仅在首次初始化时使用）
    """
    try:
        # 创建默认 LLM 模型
        llm_models = await LLMModelService.get_or_create_default_models()
        
        # 创建默认嵌入模型
        emb_configs = await EmbeddingModelService.get_or_create_default_configs()
        
        # 设置默认用途模型
        if llm_models:
            # 设置需求分析默认模型
            await LLMModelService.set_default_model("requirement_analyze", "deepseek-chat")
            # 设置用例生成默认模型
            await LLMModelService.set_default_model("testcase_generate", "deepseek-chat")
            # 设置用例评审默认模型
            await LLMModelService.set_default_model("testcase_review", "qwen-plus")
        
        # 设置嵌入模型默认配置
        if emb_configs:
            await EmbeddingModelService.set_default_config("qwen-embedding-v3")
        
        return {
            "success": True,
            "message": "默认模型配置初始化成功",
            "llm_models_count": len(llm_models),
            "embedding_configs_count": len(emb_configs),
        }
    except Exception as e:
        logger.error(f"初始化默认模型配置失败: {e}")
        return {
            "success": False,
            "message": f"初始化失败: {str(e)}",
        }
