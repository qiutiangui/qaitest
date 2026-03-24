"""
Agent提示词模板API
支持CRUD操作和重置功能
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from app.models.agent_prompt import (
    AgentPromptTemplate,
    AgentPromptCreate,
    AgentPromptUpdate,
    AgentPromptResponse,
    init_default_prompts,
    get_all_prompts,
    get_prompt_by_type,
    DEFAULT_PROMPTS,
)

router = APIRouter(prefix="/api/agent-prompts", tags=["Agent提示词管理"])


@router.get("", response_model=List[AgentPromptResponse])
async def list_prompts(
    agent_type: Optional[str] = Query(None, description="按Agent类型筛选"),
    is_active: Optional[bool] = Query(None, description="按启用状态筛选"),
):
    """
    获取所有提示词模板列表

    - **agent_type**: 可选，按Agent类型筛选
    - **is_active**: 可选，按启用状态筛选
    """
    queryset = AgentPromptTemplate.all()

    if agent_type:
        queryset = queryset.filter(agent_type=agent_type)
    if is_active is not None:
        queryset = queryset.filter(is_active=is_active)

    prompts = await queryset.order_by("agent_type")
    return prompts


@router.get("/types")
async def list_prompt_types():
    """
    获取所有提示词类型及其分类

    返回按分类组织的提示词类型列表
    """
    categories = {
        "需求分析": ["requirement_acquire", "requirement_analysis", "requirement_output"],
        "用例生成": ["testcase_generate", "testcase_review", "testcase_finalize"],
    }

    result = []
    for category, types in categories.items():
        items = []
        for t in types:
            prompt = await AgentPromptTemplate.get_or_none(agent_type=t)
            if prompt:
                items.append({
                    "agent_type": t,
                    "name": prompt.name,
                    "description": prompt.description,
                    "is_active": prompt.is_active,
                    "is_editable": prompt.is_editable,
                })
        result.append({
            "category": category,
            "items": items,
        })

    return {"categories": result}


@router.get("/{prompt_id}", response_model=AgentPromptResponse)
async def get_prompt(prompt_id: int):
    """
    获取单个提示词模板详情
    """
    prompt = await AgentPromptTemplate.get_or_none(id=prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="提示词模板不存在")
    return prompt


@router.get("/by-type/{agent_type}")
async def get_prompt_by_type_endpoint(agent_type: str):
    """
    根据Agent类型获取提示词模板
    """
    prompt = await get_prompt_by_type(agent_type)
    if not prompt:
        raise HTTPException(status_code=404, detail=f"类型 {agent_type} 的提示词模板不存在")
    return prompt


@router.post("", response_model=AgentPromptResponse)
async def create_prompt(prompt_data: AgentPromptCreate):
    """
    创建新的提示词模板
    """
    # 检查是否已存在
    existing = await AgentPromptTemplate.get_or_none(agent_type=prompt_data.agent_type)
    if existing:
        raise HTTPException(status_code=400, detail=f"类型 {prompt_data.agent_type} 的模板已存在")

    prompt = await AgentPromptTemplate.create(
        agent_type=prompt_data.agent_type,
        name=prompt_data.name,
        description=prompt_data.description,
        system_prompt=prompt_data.system_prompt,
        user_prompt_template=prompt_data.user_prompt_template,
        variables=prompt_data.variables or [],
        is_active=prompt_data.is_active,
        is_editable=prompt_data.is_editable,
    )
    logger.info(f"创建提示词模板: {prompt.agent_type}")
    return prompt


@router.put("/{prompt_id}", response_model=AgentPromptResponse)
async def update_prompt(prompt_id: int, prompt_data: AgentPromptUpdate):
    """
    更新提示词模板
    """
    prompt = await AgentPromptTemplate.get_or_none(id=prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="提示词模板不存在")

    if not prompt.is_editable:
        raise HTTPException(status_code=403, detail="此提示词模板不可编辑")

    # 更新字段
    update_data = prompt_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(prompt, field, value)

    # 增加版本号
    prompt.version += 1
    await prompt.save()

    logger.info(f"更新提示词模板: {prompt.agent_type}, 版本: {prompt.version}")
    return prompt


@router.delete("/{prompt_id}")
async def delete_prompt(prompt_id: int):
    """
    删除提示词模板（软删除：设置为未激活）
    """
    prompt = await AgentPromptTemplate.get_or_none(id=prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="提示词模板不存在")

    # 软删除
    prompt.is_active = False
    await prompt.save()

    logger.info(f"删除提示词模板: {prompt.agent_type}")
    return {"message": "删除成功"}


@router.post("/{prompt_id}/reset", response_model=AgentPromptResponse)
async def reset_prompt(prompt_id: int):
    """
    重置提示词模板为默认内容
    """
    prompt = await AgentPromptTemplate.get_or_none(id=prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="提示词模板不存在")

    if not prompt.is_editable:
        raise HTTPException(status_code=403, detail="此提示词模板不可重置")

    # 获取默认提示词
    default_config = DEFAULT_PROMPTS.get(prompt.agent_type)
    if not default_config:
        raise HTTPException(status_code=400, detail=f"没有找到 {prompt.agent_type} 的默认提示词")

    # 重置为默认值
    prompt.system_prompt = default_config["system_prompt"]
    prompt.name = default_config["name"]
    prompt.description = default_config["description"]
    prompt.variables = default_config.get("variables", [])
    prompt.user_prompt_template = default_config.get("user_prompt_template")
    prompt.version = 1
    await prompt.save()

    logger.info(f"重置提示词模板: {prompt.agent_type}")
    return prompt


@router.post("/{prompt_id}/enable", response_model=AgentPromptResponse)
async def enable_prompt(prompt_id: int):
    """
    启用提示词模板
    """
    prompt = await AgentPromptTemplate.get_or_none(id=prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="提示词模板不存在")

    prompt.is_active = True
    await prompt.save()

    return prompt


@router.post("/init")
async def init_prompts():
    """
    初始化默认提示词模板

    将DEFAULT_PROMPTS中的所有模板初始化到数据库
    """
    await init_default_prompts()
    prompts = await get_all_prompts()
    return {
        "message": "初始化完成",
        "count": len(prompts),
        "prompts": [{"id": p.id, "agent_type": p.agent_type, "name": p.name} for p in prompts],
    }


@router.get("/variables/template")
async def get_template_variables():
    """
    获取所有支持的模板变量说明

    返回各Agent类型支持的变量定义
    """
    result = {}
    for agent_type, config in DEFAULT_PROMPTS.items():
        variables = config.get("variables", [])
        if variables:
            result[agent_type] = {
                "name": config["name"],
                "variables": variables,
            }
    return result
