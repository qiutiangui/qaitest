"""
Agent提示词加载器

提供统一的接口从数据库加载Agent提示词
支持：
- 异步加载提示词模板
- 变量替换
- 默认值降级
"""
import re
from typing import Optional, Dict, Any, List
from loguru import logger

from app.models.agent_prompt import (
    AgentPromptTemplate,
    DEFAULT_PROMPTS,
    get_prompt_by_type,
)


class PromptLoader:
    """
    提示词加载器

    提供静态方法加载提示词
    """

    # 缓存已加载的提示词（避免频繁查询数据库）
    _cache: Dict[str, str] = {}
    _cache_enabled: bool = True

    @classmethod
    def clear_cache(cls):
        """清除缓存"""
        cls._cache.clear()
        logger.debug("提示词缓存已清除")

    @classmethod
    def enable_cache(cls, enabled: bool = True):
        """启用/禁用缓存"""
        cls._cache_enabled = enabled
        if not enabled:
            cls.clear_cache()

    @classmethod
    async def get_prompt(cls, agent_type: str, use_cache: bool = True) -> str:
        """
        获取Agent提示词

        优先从数据库加载，如果不存在则使用默认提示词

        Args:
            agent_type: Agent类型标识
            use_cache: 是否使用缓存

        Returns:
            提示词文本
        """
        # 检查缓存
        if use_cache and cls._cache_enabled and agent_type in cls._cache:
            return cls._cache[agent_type]

        # 从数据库加载
        try:
            prompt_model = await get_prompt_by_type(agent_type)
            if prompt_model and prompt_model.system_prompt:
                prompt_text = prompt_model.system_prompt
                # 更新缓存
                if use_cache and cls._cache_enabled:
                    cls._cache[agent_type] = prompt_text
                return prompt_text
        except Exception as e:
            logger.warning(f"从数据库加载提示词失败: {e}")

        # 降级到默认提示词
        default_config = DEFAULT_PROMPTS.get(agent_type)
        if default_config:
            logger.info(f"使用默认提示词: {agent_type}")
            return default_config["system_prompt"]

        # 抛出异常
        raise ValueError(f"未找到提示词模板: {agent_type}")

    @classmethod
    async def get_prompt_with_variables(
        cls,
        agent_type: str,
        variables: Dict[str, Any],
        use_cache: bool = True
    ) -> str:
        """
        获取Agent提示词并替换变量

        Args:
            agent_type: Agent类型标识
            variables: 变量字典，如 {"scenario": "业务场景", "description": "描述"}
            use_cache: 是否使用缓存

        Returns:
            替换变量后的提示词文本
        """
        prompt = await cls.get_prompt(agent_type, use_cache)

        # 替换变量
        for key, value in variables.items():
            # 支持 [[variable]] 和 {{variable}} 两种格式
            placeholder1 = f"[[{key}]]"
            placeholder2 = f"{{{{{key}}}}}"
            prompt = prompt.replace(placeholder1, str(value))
            prompt = prompt.replace(placeholder2, str(value))

        return prompt

    @classmethod
    async def get_prompt_metadata(cls, agent_type: str) -> Optional[Dict[str, Any]]:
        """
        获取提示词元数据

        Args:
            agent_type: Agent类型标识

        Returns:
            包含 name, description, variables 等信息的字典
        """
        try:
            prompt_model = await get_prompt_by_type(agent_type)
            if prompt_model:
                return {
                    "agent_type": prompt_model.agent_type,
                    "name": prompt_model.name,
                    "description": prompt_model.description,
                    "variables": prompt_model.variables or [],
                    "is_active": prompt_model.is_active,
                    "is_editable": prompt_model.is_editable,
                    "version": prompt_model.version,
                }
        except Exception as e:
            logger.warning(f"获取提示词元数据失败: {e}")

        # 降级到默认配置
        default_config = DEFAULT_PROMPTS.get(agent_type)
        if default_config:
            return {
                "agent_type": agent_type,
                "name": default_config["name"],
                "description": default_config["description"],
                "variables": default_config.get("variables", []),
                "is_active": True,
                "is_editable": True,
                "version": 1,
            }

        return None

    @classmethod
    async def list_available_agents(cls) -> List[Dict[str, Any]]:
        """
        列出所有可用的Agent

        Returns:
            Agent信息列表
        """
        result = []
        for agent_type in DEFAULT_PROMPTS.keys():
            metadata = await cls.get_prompt_metadata(agent_type)
            if metadata:
                result.append(metadata)
        return result


def replace_prompt_variables(prompt: str, variables: Dict[str, Any]) -> str:
    """
    替换提示词中的变量

    支持的格式：
    - [[variable_name]] - 替换为变量值
    - {{variable_name}} - 替换为变量值

    Args:
        prompt: 原始提示词模板
        variables: 变量字典

    Returns:
        替换后的提示词
    """
    result = prompt

    for key, value in variables.items():
        if value is None:
            continue

        value_str = str(value)
        # 替换 [[key]] 格式
        result = result.replace(f"[[{key}]]", value_str)
        # 替换 {{key}} 格式
        result = result.replace(f"{{{{{key}}}}}", value_str)

    return result


def extract_prompt_variables(prompt: str) -> List[str]:
    """
    从提示词中提取变量名

    Args:
        prompt: 提示词模板

    Returns:
        变量名列表
    """
    variables = set()

    # 提取 [[variable]] 格式
    pattern1 = r'\[\[([^\]]+)\]\]'
    matches1 = re.findall(pattern1, prompt)
    variables.update(matches1)

    # 提取 {{variable}} 格式
    pattern2 = r'\{\{\{([^}]+)\}\}\}'
    matches2 = re.findall(pattern2, prompt)
    variables.update(matches2)

    return list(variables)


# 便捷函数 - 与Agent集成使用

async def get_agent_prompt(agent_type: str) -> str:
    """
    获取Agent提示词的便捷函数

    Args:
        agent_type: Agent类型标识

    Returns:
        提示词文本
    """
    return await PromptLoader.get_prompt(agent_type)


async def load_agent_system_message(
    agent_type: str,
    task: str = None,
    **kwargs
) -> str:
    """
    加载Agent系统消息，支持自动添加用户任务

    Args:
        agent_type: Agent类型标识
        task: 可选的用户任务描述
        **kwargs: 其他变量

    Returns:
        完整的系统消息
    """
    prompt = await PromptLoader.get_prompt(agent_type)

    # 替换其他变量
    if kwargs:
        prompt = replace_prompt_variables(prompt, kwargs)

    return prompt


# ============ Agent 提示词加载函数 ============

async def load_requirement_acquire_prompt() -> str:
    """加载需求获取Agent提示词"""
    return await get_agent_prompt("requirement_acquire")


async def load_requirement_analysis_prompt() -> str:
    """加载需求分析Agent提示词"""
    return await get_agent_prompt("requirement_analysis")


async def load_requirement_output_prompt() -> str:
    """加载需求输出Agent提示词"""
    return await get_agent_prompt("requirement_output")


async def load_testcase_generate_prompt() -> str:
    """加载用例生成Agent提示词"""
    return await get_agent_prompt("testcase_generate")


async def load_testcase_review_prompt() -> str:
    """加载用例评审Agent提示词"""
    return await get_agent_prompt("testcase_review")


async def load_testcase_finalize_prompt() -> str:
    """加载用例定稿Agent提示词"""
    return await get_agent_prompt("testcase_finalize")
