"""
AutoGen 0.7.5 Runtime管理器

关键特性：
- 使用 SingleThreadedAgentRuntime 作为运行时
- 使用 OpenAIChatCompletionClient 作为模型客户端
- 支持 AssistantAgent 和 Memory
- 支持流式输出
- 支持用户动态选择模型
- 支持从数据库读取模型配置
"""
import asyncio
from typing import Optional, Callable, Any, AsyncGenerator
from loguru import logger

from autogen_core import SingleThreadedAgentRuntime, DefaultTopicId, TopicId
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from autogen_core.memory import ListMemory, MemoryContent, MemoryMimeType

from app.config import settings
from app.schemas.model_config import ModelConfig, ModelProvider


class ModelClientManager:
    """模型客户端管理器 - 单例模式"""

    _instance: Optional["ModelClientManager"] = None
    _deepseek_client: Optional[OpenAIChatCompletionClient] = None
    _moonshot_client: Optional[OpenAIChatCompletionClient] = None
    _qwen_client: Optional[OpenAIChatCompletionClient] = None
    _db_clients: dict = {}  # 从数据库读取的模型客户端缓存

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_deepseek_client(self) -> OpenAIChatCompletionClient:
        """获取DeepSeek模型客户端（已弃用，请使用 get_model_clients 从数据库获取配置）"""
        if self._deepseek_client is None:
            if not settings.deepseek_api_key:
                # 已弃用，不再打印警告
                return self._create_mock_client()

            self._deepseek_client = OpenAIChatCompletionClient(
                model=settings.deepseek_model,
                base_url=settings.deepseek_base_url,
                api_key=settings.deepseek_api_key,
                model_info={
                    "vision": False,
                    "function_calling": True,
                    "json_output": True,
                    "structured_output": True,
                    "family": "unknown",
                }
            )
            logger.info(f"DeepSeek模型客户端已初始化: {settings.deepseek_model}")

        return self._deepseek_client

    def get_moonshot_client(self) -> OpenAIChatCompletionClient:
        """获取Moonshot模型客户端（用于评审）"""
        if self._moonshot_client is None:
            if not settings.moonshot_api_key:
                logger.warning("Moonshot API Key未配置，使用Qwen代替")
                return self.get_qwen_client()

            self._moonshot_client = OpenAIChatCompletionClient(
                model=settings.moonshot_model,
                base_url=settings.moonshot_base_url,
                api_key=settings.moonshot_api_key,
                model_info={
                    "vision": False,
                    "function_calling": True,
                    "json_output": True,
                    "structured_output": True,
                    "family": "unknown",
                }
            )
            logger.info(f"Moonshot模型客户端已初始化: {settings.moonshot_model}")

        return self._moonshot_client

    def get_qwen_client(self) -> OpenAIChatCompletionClient:
        """获取Qwen模型客户端（已弃用，请使用 get_model_clients 从数据库获取配置）"""
        if self._qwen_client is None:
            if not settings.dashscope_api_key:
                # 已弃用，不再打印警告，fallback 到 deepseek
                return self.get_deepseek_client()

            self._qwen_client = OpenAIChatCompletionClient(
                model=settings.qwen_model,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                api_key=settings.dashscope_api_key,
                model_info={
                    "vision": False,
                    "function_calling": True,
                    "json_output": True,
                    "structured_output": True,
                    "family": "unknown",
                }
            )
            logger.info(f"Qwen模型客户端已初始化: {settings.qwen_model}")

        return self._qwen_client

    def get_review_client(self) -> OpenAIChatCompletionClient:
        """
        获取评审模型客户端

        根据配置选择通义千问作为评审模型
        """
        return self.get_qwen_client()

    def get_generate_client(self) -> OpenAIChatCompletionClient:
        """
        获取生成模型客户端

        根据配置选择Qwen作为生成模型
        """
        return self.get_qwen_client()

    async def get_db_model_client(self, purpose: str) -> Optional[OpenAIChatCompletionClient]:
        """
        从数据库获取模型客户端

        Args:
            purpose: 用途，如 requirement_analyze, testcase_generate, testcase_review

        Returns:
            模型客户端，如果未配置则返回 None
        """
        # 检查缓存
        if purpose in self._db_clients:
            return self._db_clients[purpose]

        try:
            from app.services.llm_model_service import LLMModelService

            model = await LLMModelService.get_model_for_purpose(purpose)
            if not model:
                logger.warning(f"未配置 {purpose} 用途的模型")
                return None

            # 创建模型客户端
            client = OpenAIChatCompletionClient(
                model=model.default_model,
                base_url=model.base_url,
                api_key=model.api_key,
                model_info={
                    "vision": False,
                    "function_calling": True,
                    "json_output": True,
                    "structured_output": True,
                    "family": model.provider,
                }
            )

            # 缓存客户端
            self._db_clients[purpose] = client
            logger.info(f"从数据库加载模型客户端: {purpose} -> {model.name}")

            return client
        except Exception as e:
            logger.error(f"从数据库获取模型客户端失败: {e}")
            return None

    def clear_db_client_cache(self):
        """清除数据库模型客户端缓存"""
        self._db_clients.clear()
        logger.info("已清除数据库模型客户端缓存")
    
    def create_dynamic_client(self, config: ModelConfig) -> OpenAIChatCompletionClient:
        """
        根据用户配置动态创建模型客户端
        
        Args:
            config: 用户指定的模型配置
            
        Returns:
            OpenAIChatCompletionClient实例
            
        注意：此同步版本不支持从数据库获取配置，需要使用 create_dynamic_client_async
        """
        # 内置模型配置映射
        provider_defaults = {
            ModelProvider.DEEPSEEK: {
                "default_model": settings.deepseek_model or "deepseek-chat",
                "default_base_url": settings.deepseek_base_url or "https://api.deepseek.com/v1",
                "default_api_key": settings.deepseek_api_key,
            },
            ModelProvider.MOONSHOT: {
                "default_model": settings.moonshot_model or "moonshot-v1-32k",
                "default_base_url": settings.moonshot_base_url or "https://api.moonshot.cn/v1",
                "default_api_key": settings.moonshot_api_key,
            },
            ModelProvider.QWEN: {
                "default_model": settings.qwen_model or "qwen-plus",
                "default_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "default_api_key": settings.dashscope_api_key,
            },
            ModelProvider.OLLAMA: {
                "default_model": config.model or "llama3.2",
                "default_base_url": config.base_url or "http://localhost:11434/v1",
                "default_api_key": "ollama",
            },
        }
        
        if config.provider not in provider_defaults:
            raise ValueError(f"不支持的模型提供商: {config.provider}")
        
        prov_defaults = provider_defaults[config.provider]
        
        # 优先级：用户指定 > 环境变量/默认值
        model = config.model or prov_defaults["default_model"]
        base_url = config.base_url or prov_defaults["default_base_url"]
        api_key = config.api_key or prov_defaults["default_api_key"]
        
        # 对于 Ollama，使用占位符 api_key
        if config.provider == ModelProvider.OLLAMA:
            api_key = api_key or "ollama"
        
        if not api_key:
            logger.warning(f"{config.provider.value} API Key未配置，将使用模拟模式")
            return self._create_mock_client()
        
        client = OpenAIChatCompletionClient(
            model=model,
            base_url=base_url,
            api_key=api_key,
            model_info={
                "vision": False,
                "function_calling": True,
                "json_output": True,
                "structured_output": True,
                "family": config.provider.value,
            }
        )
        
        logger.info(f"动态创建模型客户端: {config.provider.value}/{model} (base_url={base_url})")
        return client
    
    def _create_mock_client(self) -> OpenAIChatCompletionClient:
        """创建模拟客户端（用于测试）"""
        # 使用一个假的API key，让客户端可以创建
        return OpenAIChatCompletionClient(
            model="gpt-3.5-turbo",
            api_key="mock-key",
            base_url="https://api.openai.com/v1",
        )


# 全局模型客户端管理器
_model_manager = ModelClientManager()


def get_deepseek_client() -> OpenAIChatCompletionClient:
    """获取DeepSeek模型客户端 - 用于需求分析和测试用例生成"""
    return _model_manager.get_deepseek_client()


def get_moonshot_client() -> OpenAIChatCompletionClient:
    """获取Moonshot模型客户端 - 用于评审"""
    return _model_manager.get_moonshot_client()


def get_qwen_client() -> OpenAIChatCompletionClient:
    """获取Qwen模型客户端 - 用于评审"""
    return _model_manager.get_qwen_client()


async def get_db_model_client(purpose: str) -> Optional[OpenAIChatCompletionClient]:
    """
    从数据库获取模型客户端

    Args:
        purpose: 用途，如 requirement_analyze, testcase_generate, testcase_review

    Returns:
        模型客户端，如果未配置则返回 None
    """
    return await _model_manager.get_db_model_client(purpose)


def clear_db_model_cache():
    """清除数据库模型客户端缓存"""
    _model_manager.clear_db_client_cache()


def get_review_client() -> OpenAIChatCompletionClient:
    """
    获取评审模型客户端
    
    确保评审和生成使用不同的LLM，避免"自己评审自己"
    """
    return _model_manager.get_review_client()


def create_dynamic_client(config: ModelConfig) -> OpenAIChatCompletionClient:
    """
    根据用户配置动态创建模型客户端
    
    Args:
        config: 用户指定的模型配置
        
    Returns:
        OpenAIChatCompletionClient实例
    """
    return _model_manager.create_dynamic_client(config)


async def get_model_clients(
    requirement_analyze_config: Optional[ModelConfig] = None,
    testcase_generate_config: Optional[ModelConfig] = None,
    testcase_review_config: Optional[ModelConfig] = None,
) -> tuple[OpenAIChatCompletionClient, OpenAIChatCompletionClient, OpenAIChatCompletionClient]:
    """
    获取需求分析、用例生成、用例评审模型客户端（异步版本）

    Args:
        requirement_analyze_config: 需求分析模型配置，为None则使用默认DeepSeek
        testcase_generate_config: 用例生成模型配置，为None则使用默认DeepSeek
        testcase_review_config: 用例评审模型配置，为None则使用默认评审模型

    Returns:
        (requirement_analyze_client, testcase_generate_client, testcase_review_client) 元组
    """
    from app.models.custom_model import CustomModel
    from app.services.llm_model_service import LLMModelService
    
    async def get_custom_model_async(custom_id: int):
        return await CustomModel.get_or_none(id=custom_id)
    
    # 内置模型配置映射
    provider_defaults = {
        ModelProvider.DEEPSEEK: {
            "default_model": settings.deepseek_model or "deepseek-chat",
            "default_base_url": settings.deepseek_base_url or "https://api.deepseek.com/v1",
            "default_api_key": settings.deepseek_api_key,
        },
        ModelProvider.MOONSHOT: {
            "default_model": settings.moonshot_model or "moonshot-v1-32k",
            "default_base_url": settings.moonshot_base_url or "https://api.moonshot.cn/v1",
            "default_api_key": settings.moonshot_api_key,
        },
        ModelProvider.QWEN: {
            "default_model": settings.qwen_model or "qwen-plus",
            "default_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "default_api_key": settings.dashscope_api_key,
        },
        ModelProvider.OLLAMA: {
            "default_model": "llama3.2",
            "default_base_url": "http://localhost:11434/v1",
            "default_api_key": "ollama",
        },
    }
    
    async def create_client_async(config: ModelConfig) -> OpenAIChatCompletionClient:
        # 如果是自定义模型
        if config.provider == ModelProvider.CUSTOM:
            if not config.custom_id:
                raise ValueError("自定义模型必须指定 custom_id")
            custom_model = await get_custom_model_async(config.custom_id)
            if not custom_model:
                raise ValueError(f"自定义模型不存在: {config.custom_id}")
            if not custom_model.enabled:
                raise ValueError(f"自定义模型已禁用: {custom_model.display_name}")
            return OpenAIChatCompletionClient(
                model=config.model or custom_model.default_model,
                base_url=custom_model.base_url,
                api_key=custom_model.api_key,
                model_info={
                    "vision": False,
                    "function_calling": True,
                    "json_output": True,
                    "structured_output": True,
                    "family": "custom",
                }
            )
        
        # 内置模型 - 直接使用配置中的值，无需从数据库查询 provider
        prov_defaults = provider_defaults.get(config.provider, {})
        
        # 优先级：config > provider_defaults > db_model
        model = config.model or prov_defaults.get("default_model")
        base_url = config.base_url or prov_defaults.get("default_base_url")
        api_key = config.api_key or prov_defaults.get("default_api_key")
        
        if config.provider == ModelProvider.OLLAMA:
            api_key = api_key or "ollama"
        
        if not api_key:
            logger.warning(f"{config.provider.value} API Key未配置")
            return OpenAIChatCompletionClient(
                model="gpt-3.5-turbo",
                api_key="mock-key",
                base_url="https://api.openai.com/v1",
            )
        
        return OpenAIChatCompletionClient(
            model=model,
            base_url=base_url,
            api_key=api_key,
            model_info={
                "vision": False,
                "function_calling": True,
                "json_output": True,
                "structured_output": True,
                "family": config.provider.value,
            }
        )
    
    # 需求分析模型
    if requirement_analyze_config:
        requirement_analyze_client = await create_client_async(requirement_analyze_config)
    else:
        # 从数据库获取默认模型配置（按用途获取）
        db_req_model = await LLMModelService.get_model_for_purpose("requirement_analyze")
        if db_req_model:
            req_config = ModelConfig(
                provider=ModelProvider(db_req_model.provider),
                model=db_req_model.default_model,
                base_url=db_req_model.base_url,
                api_key=db_req_model.api_key
            )
            requirement_analyze_client = await create_client_async(req_config)
        else:
            # 没有配置时抛出错误，而不是使用 mock 客户端
            raise ValueError("未配置需求分析模型，请在【设置->模型配置】中配置")

    # 用例生成模型
    if testcase_generate_config:
        testcase_generate_client = await create_client_async(testcase_generate_config)
    else:
        # 从数据库获取默认模型配置（按用途获取）
        db_gen_model = await LLMModelService.get_model_for_purpose("testcase_generate")
        if db_gen_model:
            gen_config = ModelConfig(
                provider=ModelProvider(db_gen_model.provider),
                model=db_gen_model.default_model,
                base_url=db_gen_model.base_url,
                api_key=db_gen_model.api_key
            )
            testcase_generate_client = await create_client_async(gen_config)
        else:
            # 没有配置时抛出错误，而不是使用 mock 客户端
            raise ValueError("未配置用例生成模型，请在【设置->模型配置】中配置")

    # 用例评审模型
    if testcase_review_config:
        testcase_review_client = await create_client_async(testcase_review_config)
    else:
        # 从数据库获取默认模型配置（按用途获取）
        db_rev_model = await LLMModelService.get_model_for_purpose("testcase_review")
        if db_rev_model:
            rev_config = ModelConfig(
                provider=ModelProvider(db_rev_model.provider),
                model=db_rev_model.default_model,
                base_url=db_rev_model.base_url,
                api_key=db_rev_model.api_key
            )
            testcase_review_client = await create_client_async(rev_config)
        else:
            # 没有配置时抛出错误，而不是使用 mock 客户端
            raise ValueError("未配置用例评审模型，请在【设置->模型配置】中配置")

    return requirement_analyze_client, testcase_generate_client, testcase_review_client


# 同步版本（向后兼容）- 使用不同的名称避免与异步版本冲突
def get_model_clients_sync(
    requirement_analyze_config: Optional[ModelConfig] = None,
    testcase_generate_config: Optional[ModelConfig] = None,
    testcase_review_config: Optional[ModelConfig] = None,
) -> tuple[OpenAIChatCompletionClient, OpenAIChatCompletionClient, OpenAIChatCompletionClient]:
    """
    获取需求分析、用例生成、用例评审模型客户端（同步版本）

    注意：此函数已弃用，建议使用异步版本 get_model_clients
    """
    if requirement_analyze_config:
        requirement_analyze_client = _model_manager.create_dynamic_client(requirement_analyze_config)
    else:
        requirement_analyze_client = get_deepseek_client()

    if testcase_generate_config:
        testcase_generate_client = _model_manager.create_dynamic_client(testcase_generate_config)
    else:
        testcase_generate_client = get_deepseek_client()

    if testcase_review_config:
        testcase_review_client = _model_manager.create_dynamic_client(testcase_review_config)
    else:
        testcase_review_client = get_review_client()

    return requirement_analyze_client, testcase_generate_client, testcase_review_client


class AgentRuntimeManager:
    """
    Agent运行时管理器
    
    封装 SingleThreadedAgentRuntime，提供简化的接口
    """
    
    def __init__(self):
        self.runtime: Optional[SingleThreadedAgentRuntime] = None
        self._is_started = False
    
    async def initialize(self):
        """初始化运行时"""
        if self.runtime is None:
            self.runtime = SingleThreadedAgentRuntime()
            logger.info("AgentRuntime已初始化")
    
    def start(self):
        """启动运行时"""
        if self.runtime and not self._is_started:
            self.runtime.start()
            self._is_started = True
            logger.info("AgentRuntime已启动")
    
    async def stop(self):
        """停止运行时"""
        if self.runtime and self._is_started:
            await self.runtime.stop_when_idle()
            self._is_started = False
            logger.info("AgentRuntime已停止")
    
    async def register_agent(self, agent_type: type, agent_name: str, factory: Callable[[], Any]):
        """注册Agent到运行时"""
        if self.runtime is None:
            await self.initialize()
        
        await agent_type.register(self.runtime, agent_name, factory)
        logger.info(f"Agent已注册: {agent_name}")
    
    async def publish_message(self, message: Any, topic_type: str = "default"):
        """发布消息到指定Topic"""
        if self.runtime is None:
            raise RuntimeError("Runtime未初始化")
        
        topic_id = DefaultTopicId(type=topic_type)
        await self.runtime.publish_message(message, topic_id=topic_id)
        logger.debug(f"消息已发布到Topic: {topic_type}")
    
    async def run_until_idle(self):
        """运行直到空闲"""
        if self.runtime:
            await self.runtime.stop_when_idle()


# 全局运行时管理器
_runtime_manager: Optional[AgentRuntimeManager] = None


async def get_runtime_manager() -> AgentRuntimeManager:
    """获取运行时管理器实例"""
    global _runtime_manager
    if _runtime_manager is None:
        _runtime_manager = AgentRuntimeManager()
        await _runtime_manager.initialize()
    return _runtime_manager


# ============ 辅助函数 ============

async def push_to_websocket(
    task_id: str,
    agent_name: str,
    content: str,
    message_type: str = "thinking",
    extra_data: dict = None
):
    """推送消息到WebSocket"""
    try:
        from app.api.websocket import push_agent_message
        await push_agent_message(task_id, agent_name, content, message_type, extra_data)
    except Exception as e:
        logger.warning(f"WebSocket推送失败: {e}, task_id={task_id}")


def create_assistant_agent(
    name: str,
    system_message: str,
    model_client: Optional[OpenAIChatCompletionClient] = None,
    memory: Optional[ListMemory] = None,
    stream: bool = True,
) -> AssistantAgent:
    """
    创建AssistantAgent实例
    
    Args:
        name: Agent名称
        system_message: 系统提示词
        model_client: 模型客户端，默认使用DeepSeek
        memory: 记忆存储
        stream: 是否支持流式输出
    
    Returns:
        AssistantAgent实例
    """
    if model_client is None:
        model_client = get_deepseek_client()
    
    return AssistantAgent(
        name=name,
        model_client=model_client,
        system_message=system_message,
        memory=memory,
        model_client_stream=stream,
    )


def create_memory() -> ListMemory:
    """创建记忆存储"""
    return ListMemory()


async def add_to_memory(memory: ListMemory, content: str, mime_type: MemoryMimeType = MemoryMimeType.TEXT):
    """添加内容到记忆"""
    await memory.add(MemoryContent(content=content, mime_type=mime_type))


# ============ 向后兼容的LLMClient ============

class LLMClient:
    """
    LLM客户端兼容层
    
    注意：此类保留用于向后兼容，新代码应使用 get_deepseek_client()
    """
    
    def __init__(self):
        self._client = get_deepseek_client()
        self._mock_mode = not bool(settings.deepseek_api_key)
    
    async def chat(
        self, 
        messages: list, 
        temperature: float = 0.7,
        max_tokens: int = 4000,
        stream: bool = False
    ) -> str:
        """调用LLM聊天接口"""
        if self._mock_mode:
            return self._mock_response(messages)
        
        try:
            from autogen_core.models import UserMessage
            
            # 构建消息
            user_message = UserMessage(content=messages[-1]["content"], source="user")
            
            # 调用模型
            response = await self._client.create(messages=[user_message])
            
            return response.content
            
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            return self._mock_response(messages)
    
    async def chat_stream(
        self,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> AsyncGenerator[str, None]:
        """流式调用LLM"""
        if self._mock_mode:
            yield self._mock_response(messages)
            return
        
        try:
            from autogen_core.models import UserMessage
            
            user_message = UserMessage(content=messages[-1]["content"], source="user")
            
            # 创建流式请求
            async for chunk in self._client.create_stream(messages=[user_message]):
                if hasattr(chunk, 'content') and chunk.content:
                    yield chunk.content
                    
        except Exception as e:
            logger.error(f"LLM流式调用失败: {e}")
            yield self._mock_response(messages)
    
    def _mock_response(self, messages: list) -> str:
        """模拟响应（用于测试）"""
        last_message = messages[-1]["content"] if messages else ""
        return f"[模拟响应] 已处理您的请求: {last_message[:100]}..."


# 全局LLM客户端（向后兼容）
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """获取LLM客户端实例（向后兼容）"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
