"""
需求分析Agent流水线 - AutoGen 0.7.5 标准实现

关键特性：
- 使用 @type_subscription 装饰器实现Topic订阅
- 使用 AssistantAgent 调用LLM
- 使用 ListMemory 存储对话历史
- 使用 publish_message 进行消息传递
- 支持流式输出到前端
"""
from typing import List, Dict, Any, Optional
import json
import re
import asyncio
from datetime import datetime


def clean_json_content(content: str) -> str:
    """
    清理内容中的特殊字符，确保JSON解析正确
    修复 LLM 输出中可能包含的特殊引号等问题
    """
    if not content:
        return content
    
    # 替换中文引号为英文引号
    content = content.replace('"', '"').replace('"', '"')
    # 替换中文冒号
    content = content.replace('：', ':')
    # 替换中文逗号
    content = content.replace('，', ',')
    # 替换中文括号
    content = content.replace('（', '(').replace('）', ')')
    
    return content

from autogen_core import (
    RoutedAgent, 
    type_subscription,
    message_handler, 
    MessageContext,
    TopicId,
    SingleThreadedAgentRuntime,
    DefaultTopicId,
)
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.messages import ModelClientStreamingChunkEvent, TextMessage, UserInputRequestedEvent
from autogen_agentchat.base import TaskResult  # TaskResult 在 base 模块中
from autogen_core.memory import ListMemory, MemoryContent, MemoryMimeType
from loguru import logger

from app.agents.messages import (
    RequirementInputMessage,
    RequirementAcquiredMessage,
    RequirementAnalysisMessage,
    RequirementOutputMessage,
    RequirementCompleteMessage,
    TOPIC_REQUIREMENT_INPUT,
    TOPIC_REQUIREMENT_ACQUIRE,
    TOPIC_REQUIREMENT_ANALYSIS,
    TOPIC_REQUIREMENT_OUTPUT,
)
from app.agents.runtime import (
    get_deepseek_client,
    get_qwen_client,
    push_to_websocket,
    create_memory,
    add_to_memory,
    create_dynamic_client,
)
from app.schemas.model_config import ModelConfig, ModelProvider
from app.agents.prompt_loader import PromptLoader


async def push_log(task_id: str, agent_name: str, content: str, message_type: str = "thinking", extra_data: dict = None):
    """推送日志消息到WebSocket并持久化到数据库"""
    try:
        await push_to_websocket(task_id, agent_name, content, message_type, extra_data)

        # 流式消息也需要持久化到数据库，供任务记录页面显示
        await _persist_log(task_id, agent_name, content, message_type)
    except Exception as e:
        logger.error(f"push_log异常: {e}")


async def _persist_log(task_id: str, agent_name: str, content: str, message_type: str = "info"):
    """将日志持久化到任务记录表"""
    try:
        # 流式消息不持久化（太频繁，影响性能）
        if message_type == "stream":
            return
            
        from app.models import AITestTask
        from datetime import datetime
        from app.database import ensure_db_connection

        # 确保数据库连接可用
        if not await ensure_db_connection():
            logger.warning(f"数据库连接不可用，跳过日志持久化: task_id={task_id}")
            return

        # 映射消息类型到日志级别
        level_map = {
            "thinking": "info",
            "response": "info",
            "complete": "success",
            "error": "error",
            "stream": "info",
        }
        level = level_map.get(message_type, "info")

        # Agent 名称映射
        agent_name_map = {
            "RequirementAcquireAgent": "需求获取",
            "RequirementAnalysisAgent": "需求分析",
            "RequirementOutputAgent": "数据保存",
            "TestcaseGenerateAgent": "用例生成",
            "TestcaseReviewAgent": "用例评审",
            "TestcaseFormatAgent": "格式优化",
            "TestcaseInDatabaseAgent": "数据保存",
            "System": "系统",
        }
        display_name = agent_name_map.get(agent_name, agent_name)

        # 查找任务记录（使用统一的 AITestTask）
        task = await AITestTask.filter(task_id=task_id).first()
        if task:
            await task.add_log(agent_name, display_name, content, level, message_type)

    except Exception as e:
        logger.error(f"持久化日志失败: {e}")


async def update_task_progress(task_id: str, phase_code: str, phase_name: str, progress: int = None, status: str = "running"):
    """更新任务进度和阶段"""
    try:
        from app.models import AITestTask
        from datetime import datetime
        from app.database import ensure_db_connection

        # 确保数据库连接可用
        if not await ensure_db_connection():
            logger.warning(f"数据库连接不可用，跳过进度更新: task_id={task_id}")
            return

        # 查找任务
        task = await AITestTask.filter(task_id=task_id).first()
        if task:
            # 根据阶段代码判断是需求分析还是用例生成
            if phase_code.startswith("step1") or phase_code.startswith("step2") or phase_code.startswith("step3"):
                # 需求分析阶段
                if progress is not None:
                    await task.update_requirement_progress(status=status, progress=progress)
            else:
                # 用例生成阶段
                if progress is not None:
                    await task.update_testcase_progress(status=status, progress=progress)
            
            await task.update_phase(phase_code, phase_name, status)

            # 推送进度更新到WebSocket（包含 [PROGRESS] 标签供前端解析）
            progress_tag = f"[PROGRESS]{progress}[/PROGRESS]" if progress is not None else ""
            await push_to_websocket(
                task_id,
                "System",
                f"{progress_tag}阶段更新: {phase_name} - {status}",
                "progress",
                {"phase": phase_code, "progress": progress}
            )

    except Exception as e:
        logger.error(f"更新任务进度失败: {e}")


class StreamBuffer:
    """
    流式输出缓冲器 - 直接实时推送每个chunk
    """
    def __init__(self, task_id: str, agent_name: str, buffer_size: int = 1):
        self.task_id = task_id
        self.agent_name = agent_name
        self.is_started = False
        self.full_content = ""
    
    async def start(self, prefix: str = ""):
        """开始流式输出"""
        if not self.is_started:
            await push_log(self.task_id, self.agent_name, prefix, "stream_start")
            self.is_started = True
    
    async def append(self, chunk: str):
        """直接推送每个chunk"""
        if not chunk:
            return
        self.full_content += chunk
        await push_log(self.task_id, self.agent_name, chunk, "stream")
    
    async def flush(self):
        """手动刷新缓冲区"""
        pass  # 实时模式下不需要flush
    
    async def end(self, suffix: str = ""):
        """结束流式输出"""
        if suffix:
            self.full_content += suffix
            await push_log(self.task_id, self.agent_name, suffix, "stream_end")


def parse_json_response(content: str, max_retries: int = 3) -> List[Dict[str, Any]]:
    """
    健壮的JSON解析函数，支持多种格式和重试机制，能处理截断的JSON
    
    Args:
        content: LLM返回的内容
        max_retries: 最大重试次数（解析JSON数组）
    
    Returns:
        解析后的requirements列表
    """
    if not content:
        return []
    
    # 预处理：移除markdown代码块标记
    content_clean = content.strip()
    if content_clean.startswith('```'):
        # 移除开头的 ```json 或 ```
        content_clean = re.sub(r'^```(?:json)?\s*', '', content_clean)
        # 移除结尾的 ```
        content_clean = re.sub(r'\s*```$', '', content_clean)
    
    # 方法1: 尝试直接解析完整JSON
    try:
        data = json.loads(content_clean)
        if isinstance(data, dict) and "requirements" in data:
            logger.info(f"JSON直接解析成功: {len(data['requirements'])} 个功能点")
            return data["requirements"]
        elif isinstance(data, list):
            logger.info(f"JSON直接解析成功: {len(data)} 个功能点")
            return data
    except json.JSONDecodeError as e:
        logger.debug(f"完整JSON解析失败: {e}")
    
    # 方法2: 提取 requirements 数组部分
    try:
        # 查找 "requirements": [ 开始的位置
        match = re.search(r'"requirements"\s*:\s*\[', content_clean)
        if match:
            start = match.end()
            # 从这里开始提取数组内容
            array_str = content_clean[start-1:]  # 包含 [
            
            # 尝试找到数组的结束位置
            bracket_count = 0
            end_pos = 0
            for i, char in enumerate(array_str):
                if char == '[':
                    bracket_count += 1
                elif char == ']':
                    bracket_count -= 1
                    if bracket_count == 0:
                        end_pos = i + 1
                        break
            
            if end_pos > 0:
                array_content = array_str[:end_pos]
                requirements = json.loads(array_content)
                logger.info(f"提取requirements数组成功: {len(requirements)} 个功能点")
                return requirements
    except Exception as e:
        logger.debug(f"提取requirements数组失败: {e}")
    
    # 方法3: 使用正则表达式逐个提取需求对象
    try:
        # 匹配每个需求对象
        pattern = r'\{\s*"name"\s*:\s*"[^"]+"\s*,.*?\}'
        matches = re.findall(pattern, content_clean, re.DOTALL)
        
        if matches:
            requirements = []
            for match in matches:
                try:
                    req = json.loads(match)
                    if isinstance(req, dict) and "name" in req:
                        requirements.append(req)
                except:
                    continue
            
            if requirements:
                logger.info(f"正则提取需求对象成功: {len(requirements)} 个功能点")
                return requirements
    except Exception as e:
        logger.debug(f"正则提取需求对象失败: {e}")
    
    # 方法4: 处理截断的JSON - 尝试修复
    try:
        # 如果JSON被截断，尝试补全
        if '"requirements"' in content_clean and '[' in content_clean:
            # 找到最后一个完整的对象
            last_brace = content_clean.rfind('}')
            if last_brace > 0:
                # 截取到最后一个完整对象
                truncated = content_clean[:last_brace + 1]
                # 尝试补全JSON
                if truncated.count('[') > truncated.count(']'):
                    truncated += ']'
                if truncated.count('{') > truncated.count('}'):
                    truncated += '}'
                
                data = json.loads(truncated)
                if isinstance(data, dict) and "requirements" in data:
                    logger.info(f"截断JSON修复成功: {len(data['requirements'])} 个功能点")
                    return data["requirements"]
                elif isinstance(data, list):
                    logger.info(f"截断JSON修复成功: {len(data)} 个功能点")
                    return data
    except Exception as e:
        logger.debug(f"截断JSON修复失败: {e}")
    
    logger.warning(f"所有JSON解析方法都失败，返回空列表")
    return []


def parse_review_response(content: str) -> Optional[Dict[str, Any]]:
    """
    专门解析评审结果的函数，支持多种格式

    Args:
        content: LLM返回的评审结果内容

    Returns:
        解析后的评审结果字典，或 None
    """
    if not content:
        return None

    # 预处理：移除markdown代码块标记
    content_clean = content.strip()
    if content_clean.startswith('```'):
        content_clean = re.sub(r'^```(?:json)?\s*', '', content_clean)
        content_clean = re.sub(r'\s*```$', '', content_clean)

    # 方法1: 尝试直接解析完整JSON
    try:
        data = json.loads(content_clean)
        if isinstance(data, dict) and "reviewed_requirements" in data:
            logger.info("评审结果JSON直接解析成功")
            return data
    except json.JSONDecodeError:
        pass

    # 方法2: 提取 reviewed_requirements 部分
    try:
        # 查找包含 reviewed_requirements 的 JSON
        match = re.search(r'"reviewed_requirements"\s*:\s*\[', content_clean)
        if match:
            # 尝试找到最外层的结束括号
            start_idx = content_clean.rfind('{', 0, match.start())
            if start_idx >= 0:
                # 尝试扩展到可能的结束位置
                for end_idx in range(len(content_clean) - 1, start_idx, -1):
                    if content_clean[end_idx] == '}':
                        try:
                            candidate = content_clean[start_idx:end_idx + 1]
                            data = json.loads(candidate)
                            if isinstance(data, dict) and "reviewed_requirements" in data:
                                logger.info("评审结果提取解析成功")
                                return data
                        except:
                            continue
    except Exception as e:
        logger.debug(f"提取reviewed_requirements失败: {e}")

    # 方法3: 处理截断的JSON
    try:
        # 找到所有 { 和 } 的位置，尝试找到有效的JSON对象
        brace_positions = []
        for i, char in enumerate(content_clean):
            if char == '{':
                brace_positions.append((i, '{'))
            elif char == '}':
                if brace_positions:
                    brace_positions.append((i, '}'))

        # 尝试从最外层 { 开始匹配
        if brace_positions and brace_positions[0][1] == '{':
            stack = []
            for pos, brace in brace_positions:
                if brace == '{':
                    stack.append(pos)
                elif brace == '}':
                    if stack:
                        start = stack.pop()
                        try:
                            candidate = content_clean[start:pos + 1]
                            data = json.loads(candidate)
                            if isinstance(data, dict) and "reviewed_requirements" in data:
                                logger.info("评审结果截断修复成功")
                                return data
                        except:
                            continue
    except Exception as e:
        logger.debug(f"截断JSON修复失败: {e}")

    logger.warning("评审结果解析失败")
    return None


def extract_missing_items(review_text: str, existing_requirements: List[Dict]) -> List[str]:
    """
    从评审文本中提取遗漏的功能点

    Args:
        review_text: LLM 返回的评审文本
        existing_requirements: 已有的功能点列表

    Returns:
        遗漏的功能点名称列表
    """
    if not review_text:
        return []

    missing = []
    existing_names = [r.get("name", "").lower() for r in existing_requirements]

    # 简单的关键词匹配：寻找可能是遗漏功能的描述
    patterns = [
        r"遗漏[：:]\s*([^。，,\n]+)",
        r"缺少[：:]\s*([^。，,\n]+)",
        r"建议补充[：:]\s*([^。，,\n]+)",
        r"还应包含[：:]\s*([^。，,\n]+)",
        r"missing[：:]\s*([^。，,\n]+)",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, review_text, re.IGNORECASE)
        for match in matches:
            # 清理并检查是否与现有功能点重复
            name = match.strip()
            if name and name.lower() not in existing_names:
                missing.append(name)

    # 去重
    return list(dict.fromkeys(missing))[:5]  # 最多返回5个


# ============ 需求获取Agent ============
@type_subscription(topic_type=TOPIC_REQUIREMENT_INPUT)
class RequirementAcquireAgent(RoutedAgent):
    """
    需求获取Agent - 第一步：获取需求文档并进行摘要
    
    支持：
    - 文档解析和RAG索引
    - 一次LLM调用完成摘要提取
    - 完成后发送摘要到分析Agent
    """
    
    def __init__(self, input_func: Optional[callable] = None, project_id: Optional[int] = None, version_id: Optional[int] = None, model_client=None):
        super().__init__("需求获取Agent")
        self.input_func = input_func
        self.project_id = project_id
        self.version_id = version_id
        # 默认使用 DeepSeek，如果指定了 model_client 则使用指定的
        self.model_client = model_client if model_client else get_deepseek_client()
        # 提示词通过动态加载，不再硬编码
        # self._summary_prompt 在 handle_message 中动态加载
    
    @message_handler
    async def handle_message(
        self, 
        message: RequirementInputMessage, 
        ctx: MessageContext
    ) -> None:
        """处理需求输入"""
        logger.info(f"RequirementAcquireAgent: 收到消息，task_id={message.task_id}")
        task_id = message.task_id
        
        # 更新阶段为需求获取
        await update_task_progress(task_id, "acquire", "需求获取", progress=10)
        await push_log(task_id, "RequirementAcquireAgent", "📖 开始获取和解析需求内容...", "thinking")
        
        try:
            # 合并文档和描述
            combined_input = ""
            if message.document_content:
                combined_input += f"【需求文档内容】\n{message.document_content}\n\n"
            if message.description:
                combined_input += f"【需求描述】\n{message.description}"
            
            # RAG 索引步骤
            chunk_count = 0
            rag_index_result = None
            if message.document_content or message.description:
                try:
                    await push_log(task_id, "RAGIndexAgent", "⏳ 正在创建文档向量索引...", "thinking")
                    
                    from app.rag import get_index_manager
                    index_manager = await get_index_manager()
                    
                    rag_content = message.document_content if message.document_content else message.description
                    logger.info(f"[RAG索引] 开始索引, content长度={len(rag_content)}, project_id={message.project_id}")
                    
                    index_result = await index_manager.index_requirement_document(
                        project_id=message.project_id,
                        task_id=task_id,
                        content=rag_content,
                        filename="requirement_document.md",
                        version_id=message.version_id,
                        requirement_name=message.requirement_name,
                        chunk_size=500,
                        overlap=100
                    )
                    
                    rag_index_result = index_result
                    logger.info(f"[RAG索引] 结果: {index_result}")
                    
                    if index_result.get("success"):
                        chunk_count = index_result.get('indexed', 0)
                        await push_log(
                            task_id, 
                            "RAGIndexAgent", 
                            f"✅ 文档索引完成：{chunk_count} 个文本块", 
                            "response"
                        )
                    else:
                        await push_log(
                            task_id, 
                            "RAGIndexAgent", 
                            f"⚠️ 文档索引跳过：{index_result.get('error', '未知错误')}", 
                            "thinking"
                        )
                except Exception as e:
                    logger.error(f"RAG索引失败（不影响需求分析）: {e}")
                    import traceback
                    logger.error(f"RAG索引详细错误: {traceback.format_exc()}")
                    await push_log(task_id, "RAGIndexAgent", f"⚠️ RAG索引失败：{e}", "thinking")
            else:
                logger.info(f"[RAG索引] 跳过，文档内容和描述都为空")
            
            # 统计信息
            doc_length = len(message.document_content) if message.document_content else 0
            desc_length = len(message.description) if message.description else 0
            total_length = doc_length + desc_length
            
            await push_log(
                task_id, 
                "RequirementAcquireAgent", 
                f"✅ 需求内容获取完成 (文档: {doc_length}字, 描述: {desc_length}字, 共: {total_length}字)", 
                "response"
            )
            
            # 动态加载提示词
            summary_prompt = await PromptLoader.get_prompt("requirement_acquire")
            
            # 创建摘要Agent（第一次LLM调用：只做摘要）
            summary_agent = AssistantAgent(
                name='summary_agent',
                model_client=self.model_client,
                system_message=summary_prompt,
                model_client_stream=True  # 启用流式输出
            )
            
            # 创建流式缓冲器
            stream_buffer = StreamBuffer(task_id, "RequirementAcquireAgent", buffer_size=100)
            
            # ========== 大小检测 + 分段处理 ==========
            THRESHOLD = 5000  # 阈值：超过此字数分段处理
            
            if total_length > THRESHOLD:
                await push_log(task_id, "RequirementAcquireAgent", f"⏳ 文档较大({total_length}字)，开始分段摘要...", "thinking")
                
                # 分段处理
                sections = split_content(combined_input, max_chars=4000)
                section_summaries = []
                
                for i, section in enumerate(sections):
                    await push_log(task_id, "RequirementAcquireAgent", f"⏳ 摘要第 {i+1}/{len(sections)} 段...", "thinking")
                    
                    # 启用流式输出
                    stream = summary_agent.run_stream(task=f"请摘要以下需求文档（第 {i+1}/{len(sections)} 段）:\n\n{section}")
                    await stream_buffer.start("📋 摘要中...\n\n")
                    
                    async for msg in stream:
                        if isinstance(msg, ModelClientStreamingChunkEvent):
                            await stream_buffer.append(msg.content)
                        elif isinstance(msg, TaskResult):
                            await stream_buffer.flush()
                            await stream_buffer.end("\n✅")
                            section_summaries.append(f"## 第 {i+1} 段摘要\n{msg.messages[-1].content}")
                
                # 合并各段摘要
                await push_log(task_id, "RequirementAcquireAgent", "⏳ 合并分段摘要...", "thinking")
                
                # 重置缓冲器
                stream_buffer = StreamBuffer(task_id, "RequirementAcquireAgent", buffer_size=100)
                await stream_buffer.start("🔄 合并摘要结果...\n\n")
                
                merge_stream = summary_agent.run_stream(
                    task=f"请将以下分段摘要合并为一个完整的需求摘要：\n\n" + "\n\n---\n\n".join(section_summaries)
                )
                
                async for msg in merge_stream:
                    if isinstance(msg, ModelClientStreamingChunkEvent):
                        await stream_buffer.append(msg.content)
                    elif isinstance(msg, TaskResult):
                        await stream_buffer.flush()
                        await stream_buffer.end("\n✅ 合并完成")
                        summary_report = msg.messages[-1].content
                
                await push_log(task_id, "RequirementAcquireAgent", f"✅ 分段摘要完成（{len(sections)}段）", "complete")
            else:
                await push_log(task_id, "RequirementAcquireAgent", "⏳ 正在生成需求摘要...", "thinking")
                
                # 启用流式输出
                stream = summary_agent.run_stream(task=f"请摘要以下需求文档内容:\n\n{combined_input}")
                await stream_buffer.start("📝 AI摘要中...\n\n")
                
                async for msg in stream:
                    if isinstance(msg, ModelClientStreamingChunkEvent):
                        await stream_buffer.append(msg.content)
                    elif isinstance(msg, TaskResult):
                        await stream_buffer.flush()
                        await stream_buffer.end("\n✅ 摘要完成")
                        summary_report = msg.messages[-1].content
                
                await push_log(task_id, "RequirementAcquireAgent", "✅ 需求摘要完成", "complete")
            
            # 发送到分析Agent（第二次LLM调用：深度分析）
            await self.publish_message(
                RequirementAcquiredMessage(
                    task_id=task_id,
                    project_id=message.project_id,
                    version_id=message.version_id,
                    requirement_name=message.requirement_name,
                    raw_content=combined_input,
                    document=message.document_content or "",
                    description=message.description or "",
                    stats={"doc_length": doc_length, "desc_length": desc_length, "total_length": total_length},
                    chunk_count=chunk_count,
                ),
                topic_id=TopicId(type=TOPIC_REQUIREMENT_ANALYSIS, source=self.id.key)
            )

            # 需求获取阶段完成
            await update_task_progress(task_id, "acquire", "需求获取", progress=20, status="completed")
            await push_log(task_id, "RequirementAcquireAgent", "✅ 需求获取完成，开始深度分析...", "complete")
            
        except Exception as e:
            err_msg = f"需求获取过程报错：{str(e)}"
            logger.error(err_msg)
            await push_log(task_id, "RequirementAcquireAgent", f"❌ {err_msg}", "error")


def split_content(content: str, max_chars: int = 4000) -> List[str]:
        """
        按章节分段（按 ## 标题分割）
        """
        import re
        
        # 先按 ## 标题分割成章节
        sections = re.split(r'\n(?=## )', content)
        
        result = []
        current = ""
        
        for section in sections:
            if len(current) + len(section) <= max_chars:
                current += section + "\n"
            else:
                if current.strip():
                    result.append(current.strip())
                # 如果单个章节超过限制，按段落继续分割
                if len(section) > max_chars:
                    paragraphs = re.split(r'\n\n+', section)
                    current = ""
                    for para in paragraphs:
                        if len(current) + len(para) <= max_chars:
                            current += para + "\n\n"
                        else:
                            if current.strip():
                                result.append(current.strip())
                            current = para + "\n\n"
                else:
                    current = section + "\n"
        
        if current.strip():
            result.append(current.strip())
        
        return result if result else [content]


# ============ 需求分析Agent ============
@type_subscription(topic_type=TOPIC_REQUIREMENT_ANALYSIS)
class RequirementAnalysisAgent(RoutedAgent):
    """
    需求分析Agent - 第二步：接收摘要，进行深度结构化分析
    
    支持：
    - 基于摘要进行深度分析
    - 功能需求分解（核心功能★、高风险功能⚠️）
    - 可测试性评估和测试策略建议
    - 风险热点识别
    """
    
    def __init__(self, model_client=None):
        super().__init__("需求分析Agent")
        self.model_client = model_client if model_client else get_deepseek_client()
        # 提示词通过动态加载，不再硬编码
        # self._analysis_prompt 在 handle_message 中动态加载
    
    @message_handler
    async def handle_message(
        self, 
        message: RequirementAcquiredMessage, 
        ctx: MessageContext
    ) -> None:
        """处理需求分析"""
        logger.info(f"RequirementAnalysisAgent: 收到消息，task_id={message.task_id}")
        task_id = message.task_id
        
        # 更新阶段为需求分析
        await update_task_progress(task_id, "analysis", "需求分析", progress=25)
        await push_log(task_id, "RequirementAnalysisAgent", "📊 开始深度分析需求...", "thinking")
        
        try:
            # 动态加载提示词
            analysis_prompt = await PromptLoader.get_prompt("requirement_analysis")
            
            # 创建分析Agent（第二次LLM调用：深度分析）
            analyst_agent = AssistantAgent(
                name='analyst_agent',
                model_client=self.model_client,
                system_message=analysis_prompt,
                model_client_stream=True  # 启用流式输出
            )
            
            # 创建流式缓冲器
            stream_buffer = StreamBuffer(task_id, "RequirementAnalysisAgent", buffer_size=100)
            
            # 使用原始内容和摘要作为输入
            raw_content = message.raw_content or (message.document + "\n\n" + message.description)
            
            await push_log(task_id, "RequirementAnalysisAgent", "⏳ 正在进行深度需求分析...", "thinking")
            
            # 启用流式输出
            stream = analyst_agent.run_stream(task=f"请分析以下需求内容:\n\n{raw_content}")
            await stream_buffer.start("📝 AI深度分析中...\n\n")
            
            analysis_report = ""
            async for msg in stream:
                if isinstance(msg, ModelClientStreamingChunkEvent):
                    await stream_buffer.append(msg.content)
                elif isinstance(msg, TaskResult):
                    await stream_buffer.flush()
                    await stream_buffer.end("\n✅ 分析完成")
                    analysis_report = msg.messages[-1].content
            
            await push_log(task_id, "RequirementAnalysisAgent", "✅ 需求深度分析完成", "complete")
            
            # 发送到输出Agent
            await self.publish_message(
                RequirementAnalysisMessage(
                    task_id=task_id,
                    project_id=message.project_id,
                    version_id=message.version_id,
                    requirement_name=message.requirement_name,
                    requirements=[{"analysis_report": analysis_report}],
                    chunk_count=message.chunk_count,
                ),
                topic_id=TopicId(type=TOPIC_REQUIREMENT_OUTPUT, source=self.id.key)
            )
            
            # 需求分析阶段完成
            await update_task_progress(task_id, "analysis", "需求分析", progress=30, status="completed")
            await push_log(task_id, "RequirementAnalysisAgent", "✅ 需求分析完成，开始生成功能点...", "complete")
            
        except Exception as e:
            err_msg = f"需求分析过程报错：{str(e)}"
            logger.error(err_msg)
            await push_log(task_id, "RequirementAnalysisAgent", f"❌ {err_msg}", "error")




# ============ 需求输出Agent ============
@type_subscription(topic_type=TOPIC_REQUIREMENT_OUTPUT)
class RequirementOutputAgent(RoutedAgent):
    """
    需求输出Agent - 第三步：将分析报告转为结构化的功能点JSON并保存到数据库
    """
    
    def __init__(self, model_client=None):
        super().__init__("需求输出Agent")
        # 默认使用 DeepSeek，如果指定了 model_client 则使用指定的
        self.model_client = model_client if model_client else get_deepseek_client()
        # 提示词通过动态加载，不再硬编码
        # self._prompt 在 handle_message 中动态加载
    
    @message_handler
    async def handle_message(
        self, 
        message: RequirementAnalysisMessage, 
        ctx: MessageContext
    ) -> None:
        """处理需求输出"""
        logger.info(f"RequirementOutputAgent: 收到消息，task_id={message.task_id}")
        task_id = message.task_id

        # 更新阶段为需求输出
        await update_task_progress(task_id, "output", "需求输出", progress=40)

        await push_log(task_id, "RequirementOutputAgent", "📝 开始进行需求功能点的结构化输出...", "thinking")
        
        # 动态加载提示词
        output_prompt = await PromptLoader.get_prompt("requirement_output")
        
        # 使用配置的模型客户端（默认 deepseek-chat）
        # 使用流式输出模式，实时显示生成进度
        output_agent = AssistantAgent(
            name='output_agent',
            model_client=self.model_client,
            system_message=output_prompt,
            model_client_stream=True  # 启用流式输出
        )
        
        analysis_content = message.requirements[0].get("analysis_report", "") if message.requirements else ""
        task = f"根据以下需求分析报告，生成结构化需求列表：\n\n{analysis_content}"
        
        try:
            # 使用流式输出
            stream = output_agent.run_stream(task=task)
            
            # 创建流式缓冲器
            stream_buffer = StreamBuffer(task_id, "RequirementOutputAgent", buffer_size=100)
            await stream_buffer.start("📋 AI正在生成功能点...\n\n")
            
            output_content = ""
            async for msg in stream:
                if isinstance(msg, ModelClientStreamingChunkEvent):
                    await stream_buffer.append(msg.content)
                elif isinstance(msg, TaskResult):
                    await stream_buffer.flush()
                    await stream_buffer.end("\n✅ 生成完成")
                    output_content = msg.messages[-1].content
            
            # 解析JSON - 多种策略
            requirements = self._parse_requirements_json(output_content)
            
            # 如果解析失败且返回空列表，尝试基于文档内容创建默认功能点
            if not requirements and output_content and len(output_content.strip()) > 50:
                logger.warning("JSON解析失败，使用内容摘要作为功能点")
                requirements = self._create_default_requirements(output_content, message.requirement_name)
            
            await push_log(
                task_id, 
                "RequirementOutputAgent", 
                f"✅ 功能点提取完成，共 {len(requirements)} 个", 
                "complete"
            )
            
            # 批量保存到数据库
            from app.models import Requirement
            
            project_id = message.project_id
            version_id = message.version_id
            
            # 批量创建功能点（性能优化）
            new_requirements = []
            for req_data in requirements:
                new_requirements.append(Requirement(
                    project_id=req_data.get("project_id", project_id),
                    version_id=version_id,
                    requirement_name=message.requirement_name or "",
                    name=req_data.get("name", ""),
                    description=req_data.get("description", ""),
                    category=req_data.get("category", ""),
                    module=req_data.get("module", ""),
                    priority=req_data.get("level", "中"),
                    acceptance_criteria=req_data.get("criteria", ""),
                    keywords=req_data.get("keywords", ""),
                    task_id=task_id,
                ))
            
            saved_ids = []
            if new_requirements:
                try:
                    saved = await Requirement.bulk_create(new_requirements)
                    saved_ids = [r.id for r in saved]
                except Exception as e:
                    logger.error(f"批量保存失败，回退到逐条保存: {e}")
                    for req in new_requirements:
                        try:
                            saved = await Requirement.create(**req.__dict__)
                            saved_ids.append(saved.id)
                        except:
                            pass
            
            await push_log(
                task_id, 
                "RequirementOutputAgent", 
                f"✅ 已保存 {len(saved_ids)} 个功能点到数据库", 
                "complete",
                {
                    "saved_ids": saved_ids, 
                    "count": len(saved_ids),
                    "chunkCount": message.chunk_count  # 传递文档分块数量给前端
                }
            )
            
            # 发布完成消息
            await self.publish_message(
                RequirementCompleteMessage(
                    task_id=task_id,
                    saved_ids=saved_ids,
                    failed_count=len(requirements) - len(saved_ids),
                ),
                topic_id=TopicId(type="requirement_complete", source=self.id.key)
            )

            # 需求输出阶段完成
            await update_task_progress(task_id, "output", "需求输出", progress=50, status="completed")
            await push_log(
                task_id, 
                "RequirementOutputAgent", 
                f"✅ 需求分析全部完成！共提取 {len(saved_ids)} 个功能点", 
                "complete",
                {
                    "saved_ids": saved_ids, 
                    "count": len(saved_ids),
                    "chunkCount": message.chunk_count,  # 传递文档分块数量给前端
                    "functionCount": len(saved_ids)  # 传递功能点数量
                }
            )
            
        except Exception as e:
            logger.error(f"需求输出失败: {e}")
            await push_log(task_id, "RequirementOutputAgent", f"❌ 需求输出失败: {str(e)}", "error")
    
    def _parse_requirements_json(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse requirements JSON - multiple strategies
        """
        requirements = []
        
        # 先清理特殊字符
        content = clean_json_content(content)
        
        # 策略1: 标准JSON解析
        try:
            data = json.loads(content.strip())
            if isinstance(data, list):
                requirements = data
            elif isinstance(data, dict):
                requirements = data.get("requirements", data.get("data", []))
            if requirements:
                return requirements
        except json.JSONDecodeError:
            pass
        
        # 策略2: 提取markdown代码块中的JSON
        try:
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
            if json_match:
                json_str = json_match.group(1).strip()
                data = json.loads(json_str)
                if isinstance(data, list):
                    requirements = data
                elif isinstance(data, dict):
                    requirements = data.get("requirements", data.get("data", []))
                if requirements:
                    return requirements
        except (json.JSONDecodeError, AttributeError):
            pass
        
        # 策略3: 查找数组开始位置，尝试截取完整JSON
        try:
            # 尝试找到 "requirements": [...] 或 "data": [...] 部分
            patterns = [
                r'"requirements"\s*:\s*(\[[\s\S]*?\])',
                r'"data"\s*:\s*(\[[\s\S]*?\])',
                r'(\[[\s\S]*?\])',
            ]
            for pattern in patterns:
                match = re.search(pattern, content)
                if match:
                    try:
                        arr_str = match.group(1)
                        requirements = json.loads(arr_str)
                        if requirements:
                            return requirements
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass
        
        # 策略4: 尝试提取对象数组
        try:
            # 查找所有 {...} 格式
            obj_pattern = r'\{[^{}]*"name"[^{}]*\}'
            matches = re.findall(obj_pattern, content)
            for match in matches:
                try:
                    obj = json.loads(match)
                    requirements.append(obj)
                except:
                    pass
            if requirements:
                return requirements
        except Exception:
            pass
        
        return []

    def _create_default_requirements(self, content: str, requirement_name: str = "") -> List[Dict[str, Any]]:
        """
        When JSON parsing fails, create default requirements from content
        """
        requirements = []
        
        # 清理内容，移除markdown格式
        clean_content = re.sub(r'```[\s\S]*?```', '', content)
        clean_content = re.sub(r'#{1,6}\s+', '', clean_content)
        clean_content = re.sub(r'\*\*(.*?)\*\*', r'\1', clean_content)
        
        # 尝试按段落分割，每段创建一个功能点
        paragraphs = re.split(r'\n\s*\n', clean_content)
        for i, para in enumerate(paragraphs):
            para = para.strip()
            if not para or len(para) < 20:
                continue
            
            # 截取前100字符作为名称
            first_line = para.split('\n')[0].strip()
            name = first_line[:80] if len(first_line) > 80 else first_line
            if not name:
                name = f"功能点_{i+1}"
            
            # 截取描述（保留前500字符）
            description = para[:500]
            
            requirements.append({
                "name": name,
                "description": description,
                "category": "功能需求",
                "module": "",
                "level": "中"
            })
        
        # 限制数量
        if len(requirements) > 20:
            requirements = requirements[:20]
        
        logger.info(f"创建默认功能点: {len(requirements)} 个")
        return requirements


# ============ 便捷函数 ============

async def run_requirement_analysis_with_runtime(
    task_id: str,
    project_id: Optional[int],
    requirement_name: Optional[str] = None,
    document_content: str = "",
    description: str = "",
    version_id: Optional[int] = None,
    input_func: Optional[callable] = None,
    llm_config: Optional[Any] = None,  # ModelConfigRequest类型
) -> List[int]:
    """
    Run requirement analysis pipeline (Runtime mode)

    直接在当前事件循环中运行 Runtime
    """
    logger.info(f"开始需求分析(Runtime模式): task_id={task_id}, project_id={project_id}")

    # 获取模型配置
    from app.agents.runtime import get_model_clients
    requirement_config = llm_config.requirement_analyze_model if llm_config else None

    # 记录使用的模型
    req_model_name = requirement_config.model if requirement_config else "deepseek-chat(default)"
    logger.info(f"需求分析使用模型: {req_model_name}")

    try:
        await push_log(task_id, "System", f"🚀 Runtime模式需求分析流水线启动\n需求分析模型: {req_model_name}", "thinking")
    except Exception as e:
        logger.error(f"push_log失败: {e}")

    # 获取模型客户端
    req_analyze_client, _, _ = await get_model_clients(
        requirement_analyze_config=requirement_config
    )

    # 直接在当前事件循环中运行 Runtime
    runtime = SingleThreadedAgentRuntime()

    # 注册Agent
    await RequirementAcquireAgent.register(
        runtime,
        "requirement_acquire_agent",
        lambda: RequirementAcquireAgent(input_func=input_func, model_client=req_analyze_client)
    )
    await RequirementAnalysisAgent.register(
        runtime,
        "requirement_analysis_agent",
        lambda: RequirementAnalysisAgent(model_client=req_analyze_client)
    )
    await RequirementOutputAgent.register(
        runtime,
        "requirement_output_agent",
        lambda: RequirementOutputAgent(model_client=req_analyze_client)
    )
    
    # 启动
    runtime.start()
    
    # 发布消息
    input_message = RequirementInputMessage(
        task_id=task_id,
        project_id=project_id,
        requirement_name=requirement_name,
        document_content=document_content,
        description=description,
        version_id=version_id,
    )
    await runtime.publish_message(
        input_message,
        topic_id=DefaultTopicId(type=TOPIC_REQUIREMENT_INPUT)
    )
    
    # 等待完成
    await runtime.stop_when_idle()
    logger.info(f"Runtime执行完成: task_id={task_id}")

    # 返回结果
    from app.models import Requirement
    requirements = await Requirement.filter(task_id=task_id).order_by("id")
    saved_ids = [r.id for r in requirements]
    logger.info(f"查询到功能点: {len(saved_ids)} 个, IDs={saved_ids}")
    return saved_ids


