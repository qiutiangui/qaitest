"""
测试用例生成Agent流水线 - AutoGen 0.7.5 标准实现

关键特性：
- 使用 @type_subscription 装饰器实现Topic订阅
- 使用 AssistantAgent 调用LLM
- 使用 ListMemory 存储对话历史
- 使用 publish_message 进行消息传递
- 支持流式输出到前端
- 支持人工评审
"""
from typing import List, Dict, Any, Optional
import json
import re
import asyncio
import time

# 模块级事件存储，用于跨Agent触发完成事件
_completion_events: Dict[str, asyncio.Event] = {}


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


def _parse_json_from_text(text: str, max_repair_attempts: int = 3) -> Optional[List[Dict[str, Any]]]:
    """
    从文本中健壮地解析JSON数组，处理各种格式问题（增强版）。
    
    支持的场景：
    1. 标准JSON数组: [{"a": 1}, {"b": 2}]
    2. 带markdown代码块: ```json\n[...]\n```
    3. 不完整的JSON (缺少逗号)
    4. 多余的逗号
    5. 单引号问题
    6. 注释问题
    
    新增功能：
    - 多次修复尝试（默认3次）
    - 智能截取策略
    - 括号平衡修复
    """
    if not text:
        return None
    
    # 先清理特殊字符
    text = clean_json_content(text)
    
    # 策略1: 尝试直接解析
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            if 'testcases' in data:
                return data['testcases']
            if 'cases' in data:
                return data['cases']
            if 'data' in data:
                return data['data']
    except json.JSONDecodeError:
        pass
    
    # 策略2: 提取JSON数组
    json_str = None
    original_text = text
    
    # 2.1 尝试提取 markdown 代码块中的 JSON
    code_block_patterns = [
        r'```json\s*([\s\S]*?)\s*```',  # ```json ... ```
        r'```\s*([\s\S]*?)\s*```',      # ``` ... ``` (不指定语言)
    ]
    for pattern in code_block_patterns:
        match = re.search(pattern, text)
        if match:
            candidate = match.group(1).strip()
            try:
                data = json.loads(candidate)
                if isinstance(data, list):
                    return data
                if isinstance(data, dict):
                    if 'testcases' in data:
                        return data['testcases']
                    if 'cases' in data:
                        return data['cases']
            except json.JSONDecodeError:
                json_str = candidate  # 尝试后续修复
    
    # 2.2 如果没有找到代码块，尝试提取数组
    if json_str is None:
        # 找第一个 [ 和最后一个 ]
        first_bracket = text.find('[')
        last_bracket = text.rfind(']')
        if first_bracket != -1 and last_bracket > first_bracket:
            json_str = text[first_bracket:last_bracket + 1]
    
    if not json_str:
        # 尝试从整个文本中提取任何看起来像JSON数组的内容
        # 查找 {...} 模式并尝试构建数组
        return _parse_json_object_list(text)
    
    # 策略3: 多次修复尝试（新增）
    result = json_str
    for attempt in range(max_repair_attempts):
        fixed_json = _fix_json_format(result)
        
        try:
            data = json.loads(fixed_json)
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                if 'testcases' in data:
                    return data['testcases']
                if 'cases' in data:
                    return data['cases']
        except json.JSONDecodeError:
            pass
        
        # 如果修复后仍然失败，尝试更激进的修复
        if attempt < max_repair_attempts - 1:
            # 移除多余的空白和换行
            result = re.sub(r'\s+', ' ', fixed_json).strip()
            # 尝试补全括号
            bracket_diff = result.count('[') - result.count(']')
            if bracket_diff > 0:
                result += ']' * bracket_diff
    
    # 策略4: 智能截取（新增）- 尝试提取部分有效的JSON
    try:
        parsed = _smart_extract_json(text)
        if parsed is not None:
            return parsed
    except Exception:
        pass
    
    # 策略5: 返回None，使用原始数据
    return None


def _parse_json_object_list(text: str) -> Optional[List[Dict[str, Any]]]:
    """
    从文本中提取对象数组，即使格式不完整也能尝试解析
    """
    # 查找所有 {...} 模式
    objects = []
    
    # 使用栈来匹配括号
    i = 0
    while i < len(text):
        if text[i] == '{':
            # 找对应的 }
            depth = 0
            start = i
            j = i
            while j < len(text):
                if text[j] == '{':
                    depth += 1
                elif text[j] == '}':
                    depth -= 1
                    if depth == 0:
                        # 找到一个完整的对象
                        obj_str = text[start:j+1]
                        try:
                            obj = json.loads(obj_str)
                            if isinstance(obj, dict):
                                objects.append(obj)
                        except:
                            pass
                        break
                j += 1
            i = j + 1
        else:
            i += 1
    
    if objects:
        return objects
    return None


def _smart_extract_json(text: str) -> Optional[List[Dict[str, Any]]]:
    """
    智能提取JSON数组，尝试多种策略
    """
    # 策略1: 尝试找到数组边界
    first_bracket = text.find('[')
    if first_bracket == -1:
        return None
    
    # 策略2: 从第一个 [ 开始，逐步扩展，尝试解析
    # 找到最后一个 ]
    last_bracket = text.rfind(']')
    if last_bracket <= first_bracket:
        # 尝试找到最可能的 ]
        candidates = []
        depth = 0
        for i, c in enumerate(text[first_bracket:], start=first_bracket):
            if c == '[':
                depth += 1
            elif c == ']':
                depth -= 1
                if depth == 0:
                    candidates.append(i)
        
        if candidates:
            last_bracket = candidates[-1]
        else:
            return None
    
    # 尝试不同长度的截取
    for offset in range(0, 500, 50):
        if last_bracket + offset < len(text):
            continue
        candidate = text[first_bracket:last_bracket + 1]
        
        # 补全括号
        bracket_balance = candidate.count('[') - candidate.count(']')
        if bracket_balance > 0:
            candidate += ']' * bracket_balance
        elif bracket_balance < 0:
            candidate = '[' * (-bracket_balance) + candidate
        
        try:
            data = json.loads(candidate)
            if isinstance(data, list) and len(data) > 0:
                return data
        except:
            pass
    
    return None


def _fallback_parse_json(content: str, requirement_name: str = "") -> List[Dict[str, Any]]:
    """
    当所有JSON解析策略都失败时的降级方案
    从非结构化文本中提取测试用例信息
    
    Args:
        content: 原始内容（通常是LLM生成的文本）
        requirement_name: 需求名称（用于生成用例标题）
    
    Returns:
        从文本中提取的测试用例列表
    """
    if not content:
        return []
    
    cases = []
    
    # 1. 尝试提取JSON数组（使用宽松的正则）
    try:
        # 查找所有 {...} 对象
        objects = _parse_json_object_list(content)
        if objects:
            for obj in objects[:20]:  # 最多20个
                case = _normalize_testcase(obj)
                if case:
                    cases.append(case)
            if cases:
                return cases
    except Exception:
        pass
    
    # 2. 尝试提取标题模式（Markdown格式）
    title_patterns = [
        r'用例标题[:：]\s*(.+?)(?:\n|$)',
        r'"title"\s*:\s*"([^"]+)"',
        r'###?\s+(.+?)(?:\n|$)',  # Markdown标题
        r'^\s*[-*]\s+(.+?)$',      # 列表项
        r'\d+[.、]\s*(.+?)(?:\n|$)',  # 数字编号
    ]
    
    titles = []
    for pattern in title_patterns:
        matches = re.findall(pattern, content, re.MULTILINE)
        titles.extend([m.strip() for m in matches if len(m.strip()) > 3 and len(m.strip()) < 100])
    
    # 去重
    titles = list(dict.fromkeys(titles))[:20]  # 最多20个
    
    # 如果找到标题，创建用例
    for i, title in enumerate(titles):
        case = {
            "title": title,
            "desc": f"由「{title}」生成的测试用例",
            "priority": "中",
            "preconditions": "无",
            "test_data": "",
            "steps": [
                {"description": "执行测试步骤", "expected_result": "符合预期结果"}
            ]
        }
        cases.append(case)
    
    # 3. 如果什么都没找到，使用内容摘要作为单个用例
    if not cases and content:
        # 清理Markdown格式
        clean_content = re.sub(r'```[\s\S]*?```', '', content)
        clean_content = re.sub(r'#{1,6}\s+', '', clean_content)
        clean_content = re.sub(r'\*\*(.*?)\*\*', r'\1', clean_content)
        clean_content = re.sub(r'\n+', '\n', clean_content).strip()
        
        # 取前200字符作为标题
        title = clean_content[:80] if len(clean_content) > 80 else clean_content
        desc = clean_content[:500] if len(clean_content) > 500 else clean_content
        
        if title:
            cases.append({
                "title": title or requirement_name or "AI生成的测试用例",
                "desc": desc or "根据需求自动生成的测试用例",
                "priority": "中",
                "preconditions": "无",
                "test_data": "",
                "steps": [
                    {"description": "执行测试步骤", "expected_result": "符合预期结果"}
                ]
            })
    
    return cases


def _normalize_testcase(obj: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    规范化测试用例格式，确保所有必要字段存在
    """
    if not isinstance(obj, dict):
        return None
    
    # 提取标题
    title = obj.get('title', obj.get('name', obj.get('用例标题', '')))
    if not title:
        return None
    
    # 提取描述
    desc = obj.get('desc', obj.get('description', obj.get('描述', '')))
    
    # 提取优先级
    priority = obj.get('priority', obj.get('优先级', '中'))
    # 规范化优先级值
    if priority not in ['高', '中', '低', 'high', 'medium', 'low']:
        priority = '中'
    if priority in ['high']:
        priority = '高'
    elif priority in ['medium']:
        priority = '中'
    elif priority in ['low']:
        priority = '低'
    
    # 提取前置条件
    preconditions = obj.get('preconditions', obj.get('前置条件', ''))
    
    # 提取测试数据
    test_data = obj.get('test_data', obj.get('测试数据', ''))
    
    # 提取标签/类型
    tags = obj.get('tags', obj.get('test_type', obj.get('类型', '功能测试')))
    
    # 提取步骤
    steps = obj.get('steps', obj.get('测试步骤', []))
    if not isinstance(steps, list):
        steps = []
    
    # 规范化步骤格式
    normalized_steps = []
    for step in steps:
        if isinstance(step, dict):
            desc = step.get('description', step.get('step', step.get('描述', '')))
            result = step.get('expected_result', step.get('result', step.get('预期结果', '')))
            if desc:
                normalized_steps.append({
                    "description": desc,
                    "expected_result": result or "符合预期"
                })
        elif isinstance(step, str):
            normalized_steps.append({
                "description": step,
                "expected_result": "符合预期"
            })
    
    # 如果没有步骤，添加默认步骤
    if not normalized_steps:
        normalized_steps.append({
            "description": "执行测试步骤",
            "expected_result": "符合预期"
        })
    
    return {
        "title": title,
        "desc": desc,
        "priority": priority,
        "preconditions": preconditions,
        "test_data": test_data,
        "tags": tags,
        "steps": normalized_steps
    }


def _fix_json_format(json_str: str) -> str:
    """
    修复常见的JSON格式问题（增强版）
    
    修复策略：
    1. 移除无效控制字符
    2. 处理字符串值内的未转义换行符
    3. 移除单引号，改用双引号
    4. 移除JavaScript风格注释
    5. 移除尾随逗号
    6. 智能补全缺失逗号（新增）
    7. 处理裸字符串键
    8. 智能修复嵌套结构中的逗号问题（新增）
    """
    result = json_str
    
    # 0. 修复无效的控制字符（必须最先处理）
    # JSON中的控制字符必须是 \n, \r, \t 等转义形式
    # 移除或替换在字符串外部的控制字符
    result = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', result)
    
    # 0.1 智能处理字符串值内的未转义换行符
    # 匹配 "..." 字符串内容，处理其中的字面换行符
    def fix_string_newlines(match):
        content = match.group(1)
        # 将字面换行符替换为转义的 \n
        content = content.replace('\r\n', '\\n').replace('\n', '\\n')
        return '"' + content + '"'
    
    result = re.sub(r'"((?:[^"\\]|\\.)*)"', fix_string_newlines, result)
    
    # 1. 移除单引号，改用双引号 (简单替换)
    # 需要处理中文等Unicode字符不受影响
    result = re.sub(r"'([^'\\]*(?:\\.[^'\\]*)*)'", lambda m: '"' + m.group(1).replace('"', '\\"') + '"', result)
    
    # 2. 移除JavaScript风格的注释 (// 和 /* */)
    result = re.sub(r'//.*?$', '', result, flags=re.MULTILINE)
    result = re.sub(r'/\*.*?\*/', '', result, flags=re.DOTALL)
    
    # 3. 移除尾随逗号 (如 [1, 2, 3,] -> [1, 2, 3])
    result = re.sub(r',(\s*[}\]])', r'\1', result)
    
    # 4. 智能补全缺失逗号（新增）
    # 匹配 {"key": "value"}{"key": "value"} 这种情况（对象之间缺逗号）
    result = re.sub(r'}(\s*)(\{[ \t\r\n]*")', r'},\2', result)
    # 匹配 "value"}{"key" 这种情况（字符串值后紧跟对象）
    result = re.sub(r'"(\s*)(\{[ \t\r\n]*")', r'"\1,\2', result)
    # 匹配 }{" 的情况
    result = re.sub(r'\}(\s*)\{', r'},\1{', result)
    
    # 5. 处理裸字符串 (没有引号包裹的键)
    # 匹配没有引号的键名: { key: value } -> { "key": value }
    result = re.sub(r'([{,]\s*)([a-zA-Z_\u4e00-\u9fff][a-zA-Z0-9_\u4e00-\u9fff]*)\s*:', 
                    r'\1"\2":', result)
    
    # 6. 智能修复嵌套结构中的逗号问题（新增）
    # 修复数组元素之间缺少逗号: "value" "next" -> "value", "next"
    result = re.sub(r'(")(\s*)("[^:,}\]]+")(\s*)([}\]])', r'\1\3\5', result)
    # 修复 }" 的情况
    result = re.sub(r'(\})([^\s,}\]])"', r'\1, "', result)
    
    # 7. 尝试将结果包裹为有效JSON数组
    # 如果不是数组开头，尝试找到第一个数组
    stripped = result.strip()
    if not stripped.startswith('['):
        # 查找第一个 [
        idx = stripped.find('[')
        if idx != -1:
            result = stripped[idx:]
    
    return result


def _parse_json_object_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    从文本中健壮地解析JSON对象。
    """
    if not text:
        return None
    
    # 先清理特殊字符
    text = clean_json_content(text)
    
    # 策略1: 尝试直接解析
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    
    # 策略2: 提取JSON对象
    json_str = None
    
    # 2.1 尝试提取 markdown 代码块中的 JSON
    code_block_patterns = [
        r'```json\s*([\s\S]*?)\s*```',
        r'```\s*([\s\S]*?)\s*```',
    ]
    for pattern in code_block_patterns:
        match = re.search(pattern, text)
        if match:
            candidate = match.group(1).strip()
            try:
                data = json.loads(candidate)
                if isinstance(data, dict):
                    return data
            except json.JSONDecodeError:
                json_str = candidate
    
    # 2.2 如果没有找到代码块，尝试提取对象
    if json_str is None:
        first_brace = text.find('{')
        last_brace = text.rfind('}')
        if first_brace != -1 and last_brace > first_brace:
            json_str = text[first_brace:last_brace + 1]
    
    if not json_str:
        return None
    
    # 策略3: 修复格式问题
    fixed_json = _fix_json_object_format(json_str)
    
    try:
        data = json.loads(fixed_json)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    
    return None


def _fix_json_object_format(json_str: str) -> str:
    """修复JSON对象格式问题"""
    result = json_str
    
    # 移除单引号
    result = re.sub(r"'([^'\\]*(?:\\.[^'\\]*)*)'", lambda m: '"' + m.group(1).replace('"', '\\"') + '"', result)
    
    # 移除注释
    result = re.sub(r'//.*?$', '', result, flags=re.MULTILINE)
    result = re.sub(r'/\*.*?\*/', '', result, flags=re.DOTALL)
    
    # 移除尾随逗号
    result = re.sub(r',(\s*[}\]])', r'\1', result)
    
    # 处理裸字符串键
    result = re.sub(r'([{,]\s*)([a-zA-Z_\u4e00-\u9fff][a-zA-Z0-9_\u4e00-\u9fff]*)\s*:', 
                    r'\1"\2":', result)
    
    return result

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
    RequirementSelectMessage,
    TestCaseInputMessage,
    TestCaseGeneratedMessage,
    TestCaseReviewMessage,
    TestCaseFinalizeMessage,
    TestCaseCompleteMessage,
    TOPIC_TESTCASE_INPUT,
    TOPIC_TESTCASE_GENERATE,
    TOPIC_TESTCASE_REVIEW,
    TOPIC_TESTCASE_FINALIZE,
    TOPIC_TESTCASE_DATABASE,
)
from app.agents.runtime import (
    get_deepseek_client,
    get_review_client,
    push_to_websocket,
    create_memory,
    add_to_memory,
)
from app.agents.prompt_loader import PromptLoader, replace_prompt_variables


def _normalize_text(text) -> str:
    """标准化文本用于比较：转小写、移除空格和标点"""
    if not text:
        return ""
    # 确保是字符串类型
    if isinstance(text, list):
        text = ' '.join(str(item) for item in text)
    elif not isinstance(text, str):
        text = str(text)
    import re
    text = text.lower()
    text = re.sub(r'[\s\W_]', '', text)
    return text


def _get_title_key(title) -> str:
    """提取用例标题的关键部分用于比较"""
    if not title:
        return ""
    # 确保是字符串类型
    if isinstance(title, list):
        title = ' '.join(str(item) for item in title)
    elif not isinstance(title, str):
        title = str(title)
    import re
    title = title.lower()
    title = re.sub(r'[\s\W_]', '', title)
    # 移除常见前缀：测试、验证、检查、输入、提交等
    prefixes = ['测试', '验证', '检查', '输入', '提交', '创建', '编辑', '删除', '查询', '获取']
    for prefix in prefixes:
        if title.startswith(prefix):
            title = title[len(prefix):]
    return title


def _are_steps_similar(steps1: list, steps2: list) -> bool:
    """判断两个用例的步骤是否相似"""
    if not steps1 or not steps2:
        return False
    
    # 提取步骤描述的关键词
    def extract_keywords(steps):
        keywords = set()
        for step in steps:
            desc = _normalize_text(step.get('description', '') if isinstance(step, dict) else str(step))
            if len(desc) > 3:
                keywords.add(desc)
        return keywords
    
    keywords1 = extract_keywords(steps1)
    keywords2 = extract_keywords(steps2)
    
    if not keywords1 or not keywords2:
        return False
    
    # 计算交集比例
    intersection = keywords1 & keywords2
    min_len = min(len(keywords1), len(keywords2))
    
    # 如果超过50%的关键词相同，认为相似
    return len(intersection) >= min_len * 0.5


def _merge_similar_testcases(cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    合并相似的测试用例，减少冗余
    
    合并策略：
    1. 标题相似（前20个字符相同）且前置条件相同的用例
    2. 步骤基本相同的用例
    
    Args:
        cases: 原始测试用例列表
        
    Returns:
        合并后的测试用例列表
    """
    if not cases:
        return []
    
    merged_cases = []
    merged_indices = set()
    
    for i, case in enumerate(cases):
        if i in merged_indices:
            continue
        
        title = case.get('title', '')
        title_key = _get_title_key(title)
        preconditions = _normalize_text(case.get('preconditions', ''))
        steps = case.get('steps', [])
        
        # 查找可以合并的相似用例
        similar_indices = []
        for j, other_case in enumerate(cases[i + 1:], start=i + 1):
            if j in merged_indices:
                continue
            
            other_title_key = _get_title_key(other_case.get('title', ''))
            other_preconditions = _normalize_text(other_case.get('preconditions', ''))
            other_steps = other_case.get('steps', [])
            
            # 判断是否相似
            is_similar = False
            
            # 条件1：标题前15个字符相同且前置条件相同
            if title_key[:15] == other_title_key[:15] and preconditions == other_preconditions:
                is_similar = True
            
            # 条件2：步骤高度相似
            if _are_steps_similar(steps, other_steps):
                is_similar = True
            
            if is_similar:
                similar_indices.append((j, other_case))
        
        # 合并相似用例
        if similar_indices:
            # 保留当前用例
            merged_case = case.copy()
            merged_case['steps'] = list(merged_case.get('steps', []))
            
            # 合并所有相似用例的步骤（去重）
            all_step_keys = set()
            for step in merged_case['steps']:
                key = _normalize_text(step.get('description', ''))[:30]
                all_step_keys.add(key)
            
            for j, other_case in similar_indices:
                for step in other_case.get('steps', []):
                    key = _normalize_text(step.get('description', ''))[:30]
                    if key not in all_step_keys:
                        merged_case['steps'].append(step)
                        all_step_keys.add(key)
                merged_indices.add(j)
            
            merged_cases.append(merged_case)
            merged_indices.add(i)
        else:
            merged_cases.append(case)
            merged_indices.add(i)
    
    return merged_cases


async def push_log(task_id: str, agent_name: str, content: str, message_type: str = "thinking", extra_data: dict = None):
    """推送日志消息到WebSocket并持久化到数据库"""
    try:
        logger.info(f"[push_log] 开始推送: task_id={task_id}, agent={agent_name}, type={message_type}")
        await push_to_websocket(task_id, agent_name, content, message_type, extra_data)
        
        # 跳过持久化，避免可能的数据库写入阻塞
        # await _persist_log(task_id, agent_name, content, message_type)
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

        level_map = {
            "thinking": "info",
            "response": "info",
            "complete": "success",
            "error": "error",
            "stream": "info",
        }
        level = level_map.get(message_type, "info")

        task = await AITestTask.filter(task_id=task_id).first()
        if task:
            await task.add_log(agent_name, agent_name, content, level, message_type)

    except Exception as e:
        logger.error(f"持久化日志失败: {e}")


class StreamBuffer:
    """
    流式输出缓冲器 - 直接实时推送每个chunk
    """
    def __init__(self, task_id: str, agent_name: str, buffer_size: int = 1):
        self.task_id = task_id
        self.agent_name = agent_name
        self.buffer_size = buffer_size
        self.buffer = ""
        self.last_flush_time = 0
        self.is_started = False
        self.full_content = ""
    
    async def start(self, prefix: str = ""):
        """开始流式输出，发送开始标记"""
        if not self.is_started:
            await push_log(self.task_id, self.agent_name, prefix, "stream_start")
            self.is_started = True
    
    async def append(self, chunk: str):
        """直接推送每个chunk"""
        if not chunk:
            return
        self.full_content += chunk
        await push_log(self.task_id, self.agent_name, chunk, "stream")
    
    async def _flush_buffer(self):
        """刷新缓冲区"""
        if self.buffer:
            await push_log(self.task_id, self.agent_name, self.buffer, "stream")
            self.buffer = ""
    
    async def flush(self):
        """刷新缓冲区，发送剩余内容"""
        await self._flush_buffer()
    
    async def end(self, suffix: str = ""):
        """结束流式输出"""
        if suffix:
            self.full_content += suffix
            await push_log(self.task_id, self.agent_name, suffix, "stream_end")


async def push_finalize_facts(task_id: str, final_testcase: str):
    """
    解析并推送测试用例定稿的事实日志
    
    提取JSON格式测试用例的关键信息
    """
    import json
    
    await push_log(task_id, "格式优化", "✅ 测试用例格式优化完成", "response")
    
    try:
        # 解析JSON
        testcases = []
        try:
            # 尝试直接解析
            data = json.loads(final_testcase.strip())
            if isinstance(data, list):
                testcases = data
            elif isinstance(data, dict) and "testcases" in data:
                testcases = data["testcases"]
        except json.JSONDecodeError:
            # 尝试提取JSON数组
            json_match = re.search(r'\[[\s\S]*\]', final_testcase)
            if json_match:
                testcases = json.loads(json_match.group(0))
        
        if testcases:
            await push_log(
                task_id, 
                "格式优化", 
                f"  ✓ 已格式化 {len(testcases)} 个测试用例", 
                "response"
            )
    except Exception as e:
        await push_log(
            task_id, 
            "格式优化", 
            f"  ✓ 测试用例已准备入库", 
            "response"
        )


async def push_finalized_testcases(task_id: str, final_testcase: str):
    """
    推送最终格式化测试用例到前端（用于前端展示完整的用例JSON）
    """
    import json
    
    # 解析JSON
    testcases = []
    try:
        data = json.loads(final_testcase.strip())
        if isinstance(data, list):
            testcases = data
        elif isinstance(data, dict) and "testcases" in data:
            testcases = data["testcases"]
    except json.JSONDecodeError:
        # 尝试提取JSON数组
        json_match = re.search(r'\[[\s\S]*\]', final_testcase)
        if json_match:
            try:
                testcases = json.loads(json_match.group(0))
            except:
                pass
    
    if testcases:
        # 推送开始标记
        await push_log(
            task_id, 
            "格式优化", 
            f"📋 最终测试用例 (共 {len(testcases)} 个):", 
            "final_cases_start",
            {"count": len(testcases)}
        )
        
        # 逐个推送用例详情
        for i, tc in enumerate(testcases):
            # 格式化用例内容用于显示
            case_content = json.dumps(tc, ensure_ascii=False, indent=2)
            await push_log(
                task_id,
                "格式优化",
                f"--- 用例 {i+1}: {tc.get('title', '未命名')} ---",
                "final_case",
                tc
            )
            await push_log(
                task_id,
                "格式优化",
                case_content,
                "final_case_content",
                tc
            )
        
        # 推送结束标记
        await push_log(
            task_id, 
            "格式优化", 
            f"✅ 已推送 {len(testcases)} 个最终测试用例", 
            "final_cases_end",
            {"total": len(testcases)}
        )
    else:
        # 无法解析时推送原始内容
        await push_log(
            task_id, 
            "格式优化", 
            "📋 最终测试用例:", 
            "final_cases_start"
        )
        await push_log(
            task_id, 
            "格式优化", 
            final_testcase, 
            "final_cases_raw"
        )


async def push_review_facts(task_id: str, review_report: str):
    """
    解析并推送测试用例评审的事实日志
    
    提取评审报告的关键信息并结构化输出
    """
    import re
    
    await push_log(task_id, "用例评审", "📋 测试用例评审报告", "response")
    
    # 提取用例总数
    total_match = re.search(r'用例总数[:：]\s*(\d+)', review_report)
    if total_match:
        await push_log(
            task_id, 
            "用例评审", 
            f"  ✓ 评审用例总数: {total_match.group(1)}", 
            "response"
        )
    
    # 提取覆盖率
    coverage_match = re.search(r'覆盖率[:：]\s*(\d+%?)', review_report)
    if coverage_match:
        await push_log(
            task_id, 
            "用例评审", 
            f"  ✓ 需求覆盖率: {coverage_match.group(1)}", 
            "response"
        )
    
    # 提取严重问题数量
    severe_problems = re.findall(r'🔴.*?(?=🟡|📝|$)', review_report, re.DOTALL)
    if severe_problems:
        await push_log(
            task_id, 
            "用例评审", 
            f"  ⚠️ 发现 {len(severe_problems)} 个严重问题", 
            "response"
        )
    
    # 提取建议优化数量
    suggestions = re.findall(r'🟡.*?(?=📝|$)', review_report, re.DOTALL)
    if suggestions:
        await push_log(
            task_id, 
            "用例评审", 
            f"  💡 {len(suggestions)} 条优化建议", 
            "response"
        )
    
    await push_log(
        task_id, 
        "用例评审", 
        f"✅ 评审完成", 
        "response"
    )


async def push_testcase_facts(task_id: str, testcase_content: str):
    """
    解析并推送测试用例的事实日志
    
    参考需求分析的事实日志输出方式：
    1. 解析Markdown格式的测试用例内容
    2. 提取用例标题和关键信息
    3. 结构化输出事实信息
    """
    import asyncio
    import re
    
    # JSON格式不打印详细内容，只提示状态
    if '```json' in testcase_content or testcase_content.strip().startswith('['):
        await push_log(task_id, "用例生成", "⏳ 正在生成测试用例 (JSON格式)...", "thinking")
        return
    
    await push_log(task_id, "用例生成", "📊 测试用例生成完成", "response")
    
    # 尝试提取用例信息（支持Markdown格式）
    lines = testcase_content.split('\n')
    testcase_count = 0
    current_case = {}
    cases_info = []
    in_case_section = False
    
    for line in lines:
        line = line.strip()
        
        # 检测用例标题（支持多种格式）
        # 格式1: ### [编号] 用例标题
        if line.startswith('### ') or line.startswith('## '):
            if current_case:
                cases_info.append(current_case)
            
            # 移除 ### 或 ## 标记
            title = re.sub(r'^#{2,3}\s*', '', line)
            # 移除编号标记 [1]、[001] 等
            title = re.sub(r'^\[[\d]+\]\s*', '', title).strip()
            # 移除序号 "1. "、"001. " 等
            title = re.sub(r'^[\d]+\.\s*', '', title).strip()
            
            current_case = {'title': title}
            testcase_count += 1
            in_case_section = True
        
        # 格式2: 纯数字开头 "1. 用例标题" 或 "01. 用例标题"
        elif re.match(r'^[\d]+\.', line) and not in_case_section:
            if current_case:
                cases_info.append(current_case)
            
            title = re.sub(r'^[\d]+\.\s*', '', line).strip()
            current_case = {'title': title}
            testcase_count += 1
            in_case_section = True
        
        # 提取测试类型
        elif '测试类型' in line or '**测试类型**' in line:
            type_match = re.search(r'(?:测试类型)[:：]\s*([^\n]+)', line)
            if type_match:
                test_type = type_match.group(1).strip().rstrip(' \t')
                current_case['type'] = test_type
        
        # 提取优先级
        elif '优先级' in line or '**优先级**' in line:
            priority_match = re.search(r'(?:优先级)[:：]\s*([^\n]+)', line)
            if priority_match:
                priority = priority_match.group(1).strip().rstrip(' \t')
                current_case['priority'] = priority
        
        # 检测用例结束（遇到下一个用例标题或空行多行）
        elif line.startswith('### ') or line.startswith('## ') or (re.match(r'^[\d]+\.', line) and not in_case_section):
            if current_case:
                cases_info.append(current_case)
                current_case = {}
            in_case_section = False
        
        elif line == '' and in_case_section:
            # 遇到空行，结束当前用例
            if current_case and current_case.get('title'):
                cases_info.append(current_case)
                current_case = {}
            in_case_section = False
    
    # 添加最后一个用例
    if current_case and current_case.get('title'):
        cases_info.append(current_case)
    
    # 如果没有提取到用例，尝试简单的正则匹配
    if testcase_count == 0:
        # 尝试匹配 "用例标题：" 或 "**用例标题**" 等格式
        title_patterns = [
            r'用例标题[:：]\s*(.+)',
            r'\*\*用例标题\*\*[:：]\s*(.+)',
            r'Title[:：]\s*(.+)',
        ]
        for pattern in title_patterns:
            matches = re.findall(pattern, testcase_content)
            if matches:
                for title in matches:
                    cases_info.append({'title': title.strip()})
                    testcase_count += 1
                break
    
    # 输出统计信息
    await push_log(
        task_id, 
        "用例生成", 
        f"✅ 已生成 {testcase_count} 个测试用例", 
        "response"
    )
    
    # 逐个输出用例信息
    for i, case in enumerate(cases_info, 1):
        display_text = case.get('title', f'测试用例 {i}')
        
        # 添加测试类型和优先级
        metadata = []
        if case.get('type'):
            metadata.append(case['type'])
        if case.get('priority'):
            metadata.append(case['priority'])
        
        if metadata:
            display_text += f" [{', '.join(metadata)}]"
        
        await push_log(task_id, "用例生成", f"  {i}. {display_text}", "response")
        await asyncio.sleep(0.1)  # 短暂延迟，确保前端逐个渲染


# ============ 测试用例生成Agent ============
@type_subscription(topic_type=TOPIC_TESTCASE_GENERATE)
class TestCaseGenerateAgent(RoutedAgent):
    """
    测试用例生成Agent - 基于需求 + RAG知识库生成测试用例
    
    支持：
    - RAG知识检索
    - 人工评审
    - 流式输出
    - 自定义模型
    """
    
    def __init__(
        self,
        input_func: Optional[callable] = None,
        project_id: Optional[int] = None,
        model_client: Optional[Any] = None,  # OpenAIChatCompletionClient
        creator: str = "AI",  # 创建者，即生成测试用例的大模型名称
    ):
        super().__init__("测试用例生成Agent")
        self.input_func = input_func
        self.project_id = project_id
        self.model_client = model_client  # 用户指定的模型客户端
        self.creator = creator
        # 提示词通过动态加载，不再硬编码
        # self._prompt 在 handle_message 中动态加载
    
    @message_handler
    async def handle_message(
        self, 
        message: RequirementSelectMessage, 
        ctx: MessageContext
    ) -> None:
        """处理测试用例生成请求"""
        task_id = message.task_id
        
        await push_log(
            task_id, 
            "用例生成", 
            f"📝 正在为功能点【{message.name}】生成测试用例...", 
            "thinking"
        )
        
        # ========== RAG检索增强 ==========
        rag_context = ""
        if self.project_id and self.project_id > 0:
            try:
                from app.rag import get_index_manager
                
                index_manager = await get_index_manager()
                
                # 构建查询文本：功能点名称 + 描述
                query_text = f"{message.description}\n{getattr(message, 'requirement_name', '')}"
                
                # 检索相关需求文档片段
                rag_results = await index_manager.search_for_testcase_generation(
                    requirement=query_text,
                    project_id=self.project_id,
                    top_k=5,
                    score_threshold=0.65
                )
                
                if rag_results:
                    # 组装 RAG 上下文
                    context_parts = []
                    for i, r in enumerate(rag_results):
                        context_parts.append(
                            f"【相关需求片段 {i+1}】({r.get('chapter', '')})\n{r.get('content', '')}"
                        )
                    rag_context = "\n\n".join(context_parts)
                    
                    await push_log(
                        task_id, 
                        "用例生成", 
                        f"📚 RAG检索完成：找到 {len(rag_results)} 条相关需求片段", 
                        "thinking"
                    )
                else:
                    await push_log(
                        task_id, 
                        "用例生成", 
                        "📚 RAG检索完成：未找到相关需求片段，将基于功能点描述生成用例", 
                        "thinking"
                    )
                    
            except Exception as e:
                logger.warning(f"RAG检索失败: {e}")
                await push_log(
                    task_id, 
                    "用例生成", 
                    f"⚠️ RAG检索失败：{str(e)[:50]}，将直接生成用例", 
                    "thinking"
                )
        
        # 构建业务场景
        scenario = rag_context if rag_context else "暂无相关业务场景信息"
        
        # 动态加载提示词并替换变量
        system_prompt = await PromptLoader.get_prompt("testcase_generate")
        prompt = replace_prompt_variables(system_prompt, {
            "scenario": scenario,
            "description": message.description,
            "task": message.task,
            "requirement_id": str(message.id),
            "project_id": str(message.project_id if message.project_id else 0),
            "creator": self.creator,
        })
        
        # 使用Qwen客户端（擅长生成长文本）
        testcase_generator_agent = AssistantAgent(
            name='testcase_generator_agent',
            model_client=self.model_client or get_qwen_client(),  # 使用Qwen生成
            system_message=prompt,
            model_client_stream=True
        )
        
        testcase_content = ""
        
        # 创建流式缓冲器，实现实时输出（参考豆包聊天）
        stream_buffer = StreamBuffer(task_id, "用例生成", buffer_size=200)
        await stream_buffer.start("⏳ AI正在生成测试用例...\n\n")
        
        # 如果需要人工评审
        if self.input_func:
            user_proxy = UserProxyAgent(
                name="user_proxy",
                input_func=self.input_func
            )
            termination_en = TextMentionTermination("APPROVE")
            termination_cn = TextMentionTermination("同意")
            team = RoundRobinGroupChat(
                [testcase_generator_agent, user_proxy],
                termination_condition=termination_en | termination_cn
            )
            stream = team.run_stream(task=message.task)
            
            update_count = 0
            acquisition_memory = create_memory()
            
            async for msg in stream:
                if isinstance(msg, ModelClientStreamingChunkEvent):
                    # 实时推送流式内容（参考豆包聊天）
                    await stream_buffer.append(msg.content)
                    continue
                
                if isinstance(msg, TextMessage):
                    # 刷新缓冲区，确保所有内容都推送
                    await stream_buffer.flush()
                    
                    await add_to_memory(acquisition_memory, msg.model_dump_json(), MemoryMimeType.JSON)
                    
                    if msg.source == "testcase_generator_agent":
                        update_count += 1
                        testcase_content = msg.content
                        continue
                
                if isinstance(msg, UserInputRequestedEvent):
                    await push_log(task_id, "System", "请输入修改意见 APPROVE/同意:", "thinking")
                    continue
            
            # 流式输出结束
            await stream_buffer.end("\n\n✅ 用例生成完成")
            
            # 如果有多轮修改，进行总结
            if update_count > 1:
                summarize_agent = AssistantAgent(
                    name='summarize_agent',
                    model_client=get_deepseek_client(),
                    memory=[acquisition_memory],
                    system_message="你是一位测试用例优化专家，请根据上下文对话信息，输出用户最终期望的优化后的测试用例",
                    model_client_stream=True
                )
                
                stream = summarize_agent.run_stream(
                    task="结合上下文对话信息，参考指定格式输出优化后的完整的测试用例，用markdown格式输出"
                )
                # 重置缓冲器
                stream_buffer = StreamBuffer(task_id, "用例生成", buffer_size=200)
                await stream_buffer.start("⏳ AI正在优化测试用例...\n\n")
                
                async for msg in stream:
                    if isinstance(msg, ModelClientStreamingChunkEvent):
                        # 实时推送总结内容
                        await stream_buffer.append(msg.content)
                        continue
                    if isinstance(msg, TaskResult):
                        # 刷新缓冲区
                        await stream_buffer.flush()
                        testcase_content = msg.messages[-1].content
                        # 流式输出结束
                        await stream_buffer.end("\n\n✅ 用例优化完成")
                        break
            elif testcase_content:
                # 单次生成完成，刷新缓冲区并输出事实
                await stream_buffer.flush()
                await push_testcase_facts(task_id, testcase_content)
                # 流式输出结束
                await stream_buffer.end("\n\n✅ 用例生成完成")
        else:
            # 不需要人工评审
            stream = testcase_generator_agent.run_stream(task=message.task)
            async for msg in stream:
                if isinstance(msg, ModelClientStreamingChunkEvent):
                    # 实时推送流式内容（参考豆包聊天）
                    await stream_buffer.append(msg.content)
                    continue
                if isinstance(msg, TaskResult):
                    # 刷新缓冲区
                    await stream_buffer.flush()
                    testcase_content = msg.messages[-1].content
                    # 输出生成完成的事实
                    await push_testcase_facts(task_id, testcase_content)
                    # 流式输出结束
                    await stream_buffer.end("\n\n✅ 用例生成完成")
                    continue
        
        # 发送给下一个Agent
        await self.publish_message(
            TestCaseGeneratedMessage(
                task_id=task_id,
                requirement_id=message.id,
                project_id=message.project_id,
                test_cases=[{"content": testcase_content}],
                creator=self.creator,
            ),
            topic_id=TopicId(type=TOPIC_TESTCASE_REVIEW, source=self.id.key)
        )


# ============ 测试用例评审Agent ============
@type_subscription(topic_type=TOPIC_TESTCASE_REVIEW)
class TestCaseReviewAgent(RoutedAgent):
    """
    测试用例评审Agent - 对生成的用例进行质量评审，输出评审报告
    
    支持：
    - 自定义评审模型
    - 流式输出
    """
    
    def __init__(self, model_client: Optional[Any] = None):
        super().__init__("测试用例评审Agent")
        self.model_client = model_client  # 用户指定的评审模型
        # 提示词通过动态加载，不再硬编码
        # self._prompt 在 handle_message 中动态加载
    
    @message_handler
    async def handle_message(
        self, 
        message: TestCaseGeneratedMessage, 
        ctx: MessageContext
    ) -> None:
        """评审测试用例"""
        task_id = message.task_id
        
        await push_log(task_id, "用例评审", "📝 开始用例评审...", "thinking")
        
        # 动态加载提示词
        review_prompt = await PromptLoader.get_prompt("testcase_review")
        
        review_agent = AssistantAgent(
            name="review_agent",
            model_client=self.model_client or get_review_client(),
            system_message=review_prompt,
            model_client_stream=True  # 启用流式输出
        )
        
        task = "请对如下测试用例进行评审，并输出规范的评审报告 :\n" + str(message.test_cases)
        
        # 创建流式缓冲器，实现实时输出
        stream_buffer = StreamBuffer(task_id, "用例评审", buffer_size=200)
        await stream_buffer.start("⏳ AI正在评审测试用例...\n\n")
        
        stream = review_agent.run_stream(task=task)
        review_report = ""
        async for msg in stream:
            if isinstance(msg, ModelClientStreamingChunkEvent):
                await stream_buffer.append(msg.content)
            elif isinstance(msg, TaskResult):
                await stream_buffer.flush()
                review_report = msg.messages[-1].content
                await stream_buffer.end("\n\n✅ 评审完成")
        
        # 解析评审事实
        await push_review_facts(task_id, review_report)
        
        # 发送给下一个Agent
        await self.publish_message(
            TestCaseReviewMessage(
                task_id=task_id,
                project_id=message.project_id,
                test_cases=str(message.test_cases),
                review_report=review_report,
                creator=message.creator,
            ),
            topic_id=TopicId(type=TOPIC_TESTCASE_FINALIZE, source=self.id.key)
        )


# ============ 测试用例定稿Agent ============
@type_subscription(topic_type=TOPIC_TESTCASE_FINALIZE)
class TestCaseFinalizeAgent(RoutedAgent):
    """
    测试用例定稿Agent - 结合评审报告将用例转为最终JSON格式
    
    支持：
    - 自定义评审模型
    - 流式输出
    """
    
    def __init__(self, model_client: Optional[Any] = None):
        super().__init__("测试用例定稿Agent")
        self.model_client = model_client  # 用户指定的评审模型
        # 提示词通过动态加载，不再硬编码
        # self._prompt 在 handle_message 中动态加载
    
    @message_handler
    async def handle_message(
        self, 
        message: TestCaseReviewMessage, 
        ctx: MessageContext
    ) -> None:
        """定稿测试用例"""
        task_id = message.task_id
        
        # 动态加载提示词并替换变量
        finalize_prompt = await PromptLoader.get_prompt("testcase_finalize")
        prompt = replace_prompt_variables(finalize_prompt, {
            "creator": message.creator,
        })
        
        final_agent = AssistantAgent(
            name="final_agent",
            model_client=self.model_client or get_review_client(),  # 使用配置的评审模型
            system_message=prompt,
            model_client_stream=True
        )
        
        await push_log(task_id, "格式优化", "🔄 正在优化测试用例格式...", "thinking")
        
        stream = final_agent.run_stream(
            task="根据如下的测试用例及评审报告，输出最终的高质量的测试用例。测试用例及评审报告如下：\n" 
                 + "--测试用例开始--" + message.test_cases + "--测试用例结束--\n"
                 + "--评审报告开始--" + message.review_report + "--评审报告结束--\n"
        )
        
        final_testcase = ""
        
        # 创建流式缓冲器，实现实时输出（参考豆包聊天）
        stream_buffer = StreamBuffer(task_id, "格式优化", buffer_size=200)
        await stream_buffer.start("⏳ AI正在优化测试用例格式...\n\n")
        
        async for msg in stream:
            if isinstance(msg, ModelClientStreamingChunkEvent):
                # 实时推送流式内容（参考豆包聊天）
                await stream_buffer.append(msg.content)
                continue
            if isinstance(msg, TaskResult):
                # 刷新缓冲区
                await stream_buffer.flush()
                final_testcase = msg.messages[-1].content
                # 解析并输出定稿事实
                await push_finalize_facts(task_id, final_testcase)
                # 流式输出结束
                await stream_buffer.end("\n\n✅ 用例格式优化完成")
                continue
        
        # 推送最终格式化用例JSON到前端
        await push_finalized_testcases(task_id, final_testcase)
        
        # 发送给下一个Agent
        await self.publish_message(
            TestCaseFinalizeMessage(
                task_id=task_id,
                project_id=message.project_id,
                finalized_cases=final_testcase,
                creator=message.creator,
            ),
            topic_id=TopicId(type=TOPIC_TESTCASE_DATABASE, source=self.id.key)
        )


# ============ 测试用例入库Agent ============
@type_subscription(topic_type=TOPIC_TESTCASE_DATABASE)
class TestCaseInDatabaseAgent(RoutedAgent):
    """测试用例入库Agent - 将JSON用例写入数据库"""
    
    def __init__(self):
        super().__init__("测试用例入库Agent")
    
    @message_handler
    async def handle_message(
        self, 
        message: TestCaseFinalizeMessage, 
        ctx: MessageContext
    ) -> None:
        """保存测试用例到数据库"""
        task_id = message.task_id
        logger.info(f"[TESTCASE_SAVE] 开始保存, task_id={task_id}")
        
        await push_log(task_id, "数据保存", "💾 正在保存测试用例到数据库...", "thinking")
        logger.info(f"[TESTCASE_SAVE] 已发送开始日志")
        
        from app.models import TestCase, TestStep
        
        try:
            logger.info(f"[TESTCASE_SAVE] 开始解析JSON")
            # 解析JSON
            testcase_data = json.loads(message.finalized_cases)
            logger.info(f"[TESTCASE_SAVE] JSON解析成功, 用例数: {len(testcase_data) if isinstance(testcase_data, list) else 'N/A'}")
            if isinstance(testcase_data, dict) and "testcases" in testcase_data:
                testcase_data = testcase_data["testcases"]
            
            saved_ids = []
            
            for i, tc_data in enumerate(testcase_data):
                logger.info(f"[TESTCASE_SAVE] 开始保存第 {i+1} 个用例")
                try:
                    steps_data = tc_data.pop("steps", [])
                    logger.info(f"[TESTCASE_SAVE] 第 {i+1} 个用例有 {len(steps_data)} 个步骤")

                    # 处理project_id：优先使用tc_data中的，如果没有则使用message中的
                    actual_project_id = tc_data.get("project_id", message.project_id)
                    # 如果project_id为None或0，则使用None
                    if actual_project_id is not None and actual_project_id == 0:
                        actual_project_id = None

                    logger.info(f"[TESTCASE_SAVE] 创建TestCase, project_id={actual_project_id}")
                    test_case = await TestCase.create(
                        project_id=actual_project_id,
                        requirement_id=tc_data.get("requirement_id"),
                        title=tc_data.get("title", ""),
                        description=tc_data.get("desc", tc_data.get("description", "")),
                        priority=tc_data.get("priority", "中"),
                        test_type=tc_data.get("tags", "功能测试"),
                        preconditions=tc_data.get("preconditions", ""),
                        test_data=tc_data.get("test_data", ""),
                        creator=tc_data.get("creator", message.creator),  # 优先使用JSON中的creator，否则使用消息中的
                        task_id=task_id,
                    )
                    logger.info(f"[TESTCASE_SAVE] TestCase创建成功, id={test_case.id}")
                    
                    # 保存步骤
                    for j, step_data in enumerate(steps_data):
                        await TestStep.create(
                            test_case_id=test_case.id,
                            step_number=j + 1,
                            description=step_data.get("description", ""),
                            expected_result=step_data.get("expected_result", ""),
                        )
                    logger.info(f"[TESTCASE_SAVE] 步骤保存完成")
                    
                    saved_ids.append(test_case.id)
                    
                    # 推送入库的用例详情到前端
                    await push_log(
                        task_id,
                        "数据保存",
                        f"✅ 已入库: {test_case.title} (优先级: {test_case.priority})",
                        "case_saved",
                        {
                            "id": test_case.id,
                            "title": test_case.title,
                            "priority": test_case.priority,
                            "step_count": len(steps_data),
                            "description": test_case.description,
                            "preconditions": test_case.preconditions,
                        }
                    )
                    
                except Exception as e:
                    logger.error(f"保存测试用例失败: {e}")
            
            logger.info(f"[TESTCASE_SAVE] 保存完成, 共 {len(saved_ids)} 个")
            await push_log(
                task_id, 
                "数据保存", 
                f"✅ 已保存 {len(saved_ids)} 个测试用例", 
                "complete"
            )
            
            # 触发完成事件，让主函数继续处理下一个功能点
            if task_id in _completion_events:
                _completion_events[task_id].set()
                logger.info(f"[TESTCASE_SAVE] 已触发完成事件")
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            await push_log(task_id, "数据保存", f"❌ JSON解析失败: {str(e)}", "error")
        except Exception as e:
            logger.error(f"入库失败: {e}")
            await push_log(task_id, "数据保存", f"❌ 入库失败: {str(e)}", "error")


# ============ 便捷函数 ============

async def run_testcase_generation_with_runtime(
    task_id: str,
    project_id: Optional[int],
    requirement_ids: List[int],
    version_id: Optional[int] = None,
    input_func: Optional[callable] = None,
    llm_config: Optional[Any] = None,  # ModelConfigRequest类型
) -> List[int]:
    """
    运行用例生成流水线（使用Runtime模式）
    
    使用独立线程中运行 Runtime，避免与 FastAPI 事件循环冲突
    """
    import concurrent.futures
    
    logger.info(f"开始用例生成(Runtime模式): task_id={task_id}, project_id={project_id}")

    from app.agents.runtime import get_model_clients

    # 获取模型配置
    generate_config = llm_config.testcase_generate_model if llm_config else None
    review_config = llm_config.testcase_review_model if llm_config else None
    req_analyze_config = llm_config.requirement_analyze_model if llm_config else None

    # 记录使用的模型
    req_model_name = req_analyze_config.model if req_analyze_config else "deepseek(default)"
    gen_model_name = generate_config.model if generate_config else "deepseek(default)"
    rev_model_name = review_config.model if review_config else "default(review)"

    await push_log(
        task_id,
        "System",
        f"🚀 Runtime模式流水线启动\n需求分析模型: {req_model_name}\n用例生成模型: {gen_model_name}\n用例评审模型: {rev_model_name}",
        "thinking"
    )
    
    # 获取需求列表
    from app.models import Requirement
    requirements_data = []
    for req_id in requirement_ids:
        requirement = await Requirement.get_or_none(id=req_id)
        if requirement:
            requirements_data.append({
                "id": requirement.id,
                "name": requirement.name,
                "description": requirement.description,
                "category": requirement.category,
                "module": requirement.module,
                "priority": requirement.priority,
                "acceptance_criteria": requirement.acceptance_criteria,
                "keywords": requirement.keywords,
                "project_id": requirement.project_id,
            })
    
    # 在独立线程中运行 Runtime
    def _run_in_thread():
        """在线程中执行异步 Runtime"""
        import asyncio
        
        async def _run_runtime():
            """在新事件循环中运行 Runtime"""
            # 获取模型客户端
            _, generate_client, review_client = await get_model_clients(
                requirement_analyze_config=req_analyze_config,
                testcase_generate_config=generate_config,
                testcase_review_config=review_config
            )
            
            runtime = SingleThreadedAgentRuntime()
            
            # 注册Agent
            await TestCaseGenerateAgent.register(
                runtime,
                "testcase_generate_agent",
                lambda creator=gen_model_name: TestCaseGenerateAgent(
                    input_func=input_func, 
                    project_id=project_id,
                    model_client=generate_client,
                    creator=creator
                )
            )
            await TestCaseReviewAgent.register(
                runtime,
                "testcase_review_agent",
                lambda: TestCaseReviewAgent(model_client=review_client)
            )
            await TestCaseFinalizeAgent.register(
                runtime,
                "testcase_finalize_agent",
                lambda: TestCaseFinalizeAgent(model_client=review_client)
            )
            await TestCaseInDatabaseAgent.register(
                runtime,
                "testcase_database_agent",
                lambda: TestCaseInDatabaseAgent()
            )
            
            # 启动
            runtime.start()
            
            # 为每个需求发布消息
            for req in requirements_data:
                message = RequirementSelectMessage(
                    task_id=task_id,
                    id=req["id"],
                    name=req["name"],
                    description=req["description"] or "",
                    category=req["category"] or "",
                    module=req["module"] or "",
                    priority=req["priority"] or "中",
                    acceptance_criteria=req["acceptance_criteria"] or "",
                    keywords=req["keywords"] or "",
                    project_id=req["project_id"],
                    task="请根据需求描述，生成测试用例，请使用markdown格式输出"
                )
                
                await runtime.publish_message(
                    message,
                    topic_id=DefaultTopicId(type=TOPIC_TESTCASE_GENERATE)
                )
            
            # 等待完成
            await runtime.stop_when_idle()
            logger.info(f"Runtime执行完成: task_id={task_id}")

        # 创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_run_runtime())
        finally:
            loop.close()

    # 在线程池中执行
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_run_in_thread)
        future.result()

    # 返回结果
    from app.models import TestCase
    saved_testcases = await TestCase.filter(task_id=task_id).order_by("id")
    saved_ids = [tc.id for tc in saved_testcases]
    logger.info(f"查询到测试用例: {len(saved_ids)} 个, IDs={saved_ids}")
    return saved_ids


async def run_testcase_generation(
    task_id: str,
    project_id: Optional[int],
    requirement_ids: List[int],
    version_id: Optional[int] = None,
    llm_config: Optional[Any] = None,
) -> List[int]:
    """
    运行用例生成流水线（RAG预检索 + 串行流式生成 + 合并评审 + 结构化输出）

    流程：
    1. 输出功能点列表（从数据库查询）
    2. RAG预检索（批量并行） + 缓存
    3. 串行流式生成测试用例（逐功能点）
    4. 合并评审（输出结构化JSON结论）
    5. 定稿入库
    6. 输出最终测试用例（从数据库查询）
    """
    from app.models import AITestTask, Requirement, TestCase, TestStep
    from app.agents.runtime import get_model_clients
    from datetime import datetime

    logger.info(f"[run_testcase_generation] 函数开始执行: task_id={task_id}")
    logger.info(f"[run_testcase_generation] 参数: requirement_ids={requirement_ids}, project_id={project_id}, llm_config={llm_config}")

    start_time = datetime.now()

    def format_duration(seconds: float) -> str:
        if seconds < 1:
            return f"{int(seconds * 1000)}ms"
        elif seconds < 60:
            return f"{seconds:.1f}s"
        else:
            mins = int(seconds // 60)
            secs = seconds % 60
            return f"{mins}m {secs:.1f}s"

    task = await AITestTask.get_or_none(task_id=task_id)
    if task:
        await task.update_testcase_progress(status="running", progress=5)

    # 进度映射表
    STEP_PROGRESS_MAP = {
        'TestCaseGenerateAgent': 60,      # 用例生成
        'TestCaseReviewAgent': 80,         # 用例评审
        'TestCaseFinalizeAgent': 85,       # 整体定稿优化
        'TestCaseInDatabaseAgent': 95,     # 数据保存
    }

    async def update_step(agent_code: str, step_name: str):
        """更新步骤并推送到前端（统一使用Agent名称）"""
        progress = STEP_PROGRESS_MAP.get(agent_code, 50)
        if task:
            await task.update_testcase_progress(status="running", progress=progress)
        # 推送Agent名称，前端自动更新节点状态
        await push_log(task_id, "System", f"[AGENT]{agent_code}[/AGENT]{step_name}", "thinking")

    async def update_progress(progress: int):
        """更新进度并推送到前端（兼容旧逻辑）"""
        if task:
            await task.update_testcase_progress(status="running", progress=progress)
        await push_log(task_id, "System", f"[PROGRESS]{progress}[/PROGRESS]", "thinking")

    await update_progress(55)
    
    try:
        generate_config = llm_config.testcase_generate_model if llm_config else None
        review_config = llm_config.testcase_review_model if llm_config else None
        req_analyze_config = llm_config.requirement_analyze_model if llm_config else None
        _, generate_client, review_client = await get_model_clients(
            requirement_analyze_config=req_analyze_config,
            testcase_generate_config=generate_config,
            testcase_review_config=review_config
        )

        req_model_name = req_analyze_config.model if req_analyze_config else "deepseek-chat"
        gen_model_name = generate_config.model if generate_config else "deepseek-chat"
        rev_model_name = review_config.model if review_config else "qwen-plus"

        # 保存模型信息（用于完成消息）
        model_info = {
            "requirement_analyze_model": req_model_name,
            "testcase_generate_model": gen_model_name,
            "testcase_review_model": rev_model_name,
        }
        
        # ========== 阶段1：需求分析 ==========
        stage_timings = {}  # 记录各阶段耗时
        stage1_start = time.time()
        
        await update_progress(58)

        requirements = await Requirement.filter(id__in=requirement_ids).prefetch_related("project")
        
        # 发送功能点数据到前端（美观的卡片展示）
        func_points_data = [
            {
                "id": req.id,
                "name": req.name,
                "description": req.description,
                "category": req.category,
                "module": req.module,
                "priority": req.priority,
            }
            for req in requirements
        ]
        # 1.2 分析需求并提取功能点
        # await push_log(task_id, "System", f"✅ 需求分析完成，已提取 {len(requirements)} 个功能点", "response")

        # 1.3 RAG预检索
        # await push_log(task_id, "System", "⏳ RAG预检索中... (为每个功能点检索相关文档)", "thinking")

        await update_progress(60)
        all_generated_cases: List[Dict[str, Any]] = []
        total_requirements = len(requirement_ids)

        # ========== 阶段2：批量RAG预检索 ==========
        rag_cache: Dict[int, str] = {}  # {req_id: rag_context}
        
        # 修改：不再要求 project_id > 0，支持无项目的情况
        try:
            from app.rag import get_index_manager
            
            index_manager = await get_index_manager()
            
            # 并发控制：限制同时检索的数量，避免API限流
            rag_semaphore = asyncio.Semaphore(2)  # 最多2个并发
            
            # 批量检索：并行检索所有功能点的相关文档
            async def _rag_search_for_requirement(req: Any) -> tuple:
                """为单个功能点检索相关文档（带超时和错误处理）"""
                async with rag_semaphore:
                    try:
                        query_text = f"{req.name}\n{req.description or ''}"
                        # 添加超时控制（每个功能点最多5秒，更快失败）
                        results = await asyncio.wait_for(
                            index_manager.search_for_testcase_generation(
                                requirement=query_text,
                                project_id=project_id,  # 可以为 None
                                version_id=version_id,
                                task_id=req.task_id,  # 从 requirement 对象获取 task_id
                                top_k=5,
                                score_threshold=0.30  # 降低阈值，更容易找到相关文档
                            ),
                            timeout=5.0  # 单个功能点最多5秒
                        )
                        return req.id, results
                    except asyncio.TimeoutError:
                        logger.warning(f"功能点 {req.id} RAG检索超时（5秒）")
                        return req.id, []
                    except Exception as e:
                        logger.warning(f"功能点 {req.id} RAG检索失败: {e}")
                        return req.id, []
            
            # 并行检索（带回退机制）
            rag_tasks = [
                _rag_search_for_requirement(req)
                for req in requirements
            ]
            
            try:
                # 添加整体超时控制（所有功能点最多30秒）
                rag_results_list = await asyncio.wait_for(
                    asyncio.gather(*rag_tasks, return_exceptions=True),
                    timeout=30.0
                )
                
                # 处理结果（过滤掉异常）
                valid_results = []
                for result in rag_results_list:
                    if isinstance(result, Exception):
                        logger.warning(f"RAG检索任务异常: {result}")
                    else:
                        valid_results.append(result)
                rag_results_list = valid_results
                
            except asyncio.TimeoutError:
                logger.warning("批量RAG检索整体超时（30秒），跳过RAG增强")
                await push_log(task_id, "System", "⚠️ RAG检索超时，跳过RAG增强", "thinking")
                rag_results_list = []
            except Exception as e:
                logger.warning(f"RAG检索异常: {e}")
                await push_log(task_id, "System", f"⚠️ RAG检索异常: {str(e)[:50]}，跳过RAG增强", "thinking")
                rag_results_list = []
            
            # 构建缓存
            for req_id, rag_results in rag_results_list:
                if rag_results:
                    context_parts = []
                    seen_docs = set()  # 每个功能点独立去重
                    
                    for r in rag_results:
                        # 去重：同一个功能点内避免相同文档片段
                        doc_id = f"{r.get('chapter', '')}_{r.get('content', '')[:50]}"
                        if doc_id not in seen_docs:
                            seen_docs.add(doc_id)
                            context_parts.append(
                                f"【相关需求片段】({r.get('chapter', '')})\n{r.get('content', '')}"
                            )
                    
                    if context_parts:
                        rag_cache[req_id] = "\n\n".join(context_parts[:3])  # 最多3个片段
            
            await push_log(task_id, "System", f"✅ RAG预检索完成：已缓存 {len(rag_cache)} 个功能点的上下文", "complete")
            
        except Exception as e:
            logger.warning(f"批量RAG检索失败: {e}")
            await push_log(task_id, "System", f"⚠️ RAG检索失败: {str(e)[:30]}，将跳过RAG增强", "thinking")
        
        stage_timings['requirement_analysis'] = time.time() - stage1_start
        
        # ========== 阶段2：用例生成 ==========
        stage2_start = time.time()
        await push_log(task_id, "System", f"⏳ 正在生成测试用例... (共 {total_requirements} 个功能点)", "thinking")
        await update_progress(65)
        
        # 创建流式缓冲器
        stream_buffer = StreamBuffer(task_id, "用例生成", buffer_size=100)
        
        # 串行流式执行（逐个功能点生成）
        all_generated_cases = []
        
        for idx, req_id in enumerate(requirement_ids):
            requirement = await Requirement.get_or_none(id=req_id)
            if not requirement:
                continue
            
            # 输出当前处理状态
            await push_log(task_id, "用例生成", f"⏳ 正在为「{requirement.name}」生成用例... ({idx+1}/{total_requirements})", "thinking")
            
            # 获取RAG上下文
            rag_context = rag_cache.get(req_id, "")
            
            # 构建prompt
            if rag_context:
                system_prompt = f"""你是测试用例专家。请根据需求和相关的需求文档片段生成测试用例。

相关需求文档片段：
{rag_context}

请以JSON数组格式输出测试用例：
[{{"title":"用例标题","desc":"描述","priority":"高","preconditions":"前置条件","test_data":"测试数据","steps":[{{"description":"步骤","expected_result":"预期结果"}}]}}]"""
            else:
                system_prompt = """你是测试用例专家。请根据需求生成测试用例，以JSON数组格式输出：
[{"title":"用例标题","desc":"描述","priority":"高","preconditions":"前置条件","test_data":"测试数据","steps":[{"description":"步骤","expected_result":"预期结果"}]}]"""
            
            generate_agent = AssistantAgent(
                name=f'generate_agent_{idx}',
                model_client=generate_client,
                system_message=system_prompt,
                model_client_stream=True  # 启用流式输出
            )
            
            task_prompt = f"请根据以下需求生成测试用例：\n\n需求名称：{requirement.name}\n描述：{requirement.description or '无'}"
            
            # 使用 run_stream 实现流式输出
            stream = generate_agent.run_stream(task=task_prompt)
            testcase_content = ""
            
            async for msg in stream:
                if isinstance(msg, ModelClientStreamingChunkEvent):
                    await stream_buffer.append(msg.content)
                elif isinstance(msg, TaskResult):
                    testcase_content = msg.messages[-1].content
                    await stream_buffer.end("")
            
            # 解析JSON (使用健壮的解析器)
            testcases_data = []
            try:
                # 尝试健壮解析
                parsed = _parse_json_from_text(testcase_content)
                if parsed:
                    testcases_data = parsed
                else:
                    # 备用方案：直接尝试解析
                    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', testcase_content)
                    if json_match:
                        testcase_content = json_match.group(1)
                    testcases_data = json.loads(testcase_content.strip())
                
                if isinstance(testcases_data, dict):
                    testcases_data = testcases_data.get("testcases", [testcases_data])
                
                if not isinstance(testcases_data, list):
                    testcases_data = []
                    
                for tc_data in testcases_data:
                    tc_data["requirement_id"] = req_id
                    tc_data["requirement_name"] = requirement.name
                    all_generated_cases.append(tc_data)
                
                # 美化输出：格式化JSON预览
                formatted_preview = json.dumps(testcases_data[:1], ensure_ascii=False, indent=2)
                if len(testcases_data) > 1:
                    formatted_preview += f"\n... 还有 {len(testcases_data) - 1} 个用例"
                
                await push_log(task_id, "用例生成", f"📋 预览:\n```json\n{formatted_preview}\n```", "response")
                await push_log(task_id, "用例生成", f"✅ 「{requirement.name}」生成 {len(testcases_data)} 个用例", "response")

            except Exception as e:
                # 降级方案：使用降级解析器尝试提取用例
                logger.warning(f"JSON解析失败，尝试降级方案: {e}")
                fallback_cases = _fallback_parse_json(testcase_content, requirement.name)
                
                if fallback_cases:
                    testcases_data = fallback_cases
                    for tc_data in testcases_data:
                        tc_data["requirement_id"] = req_id
                        tc_data["requirement_name"] = requirement.name
                        all_generated_cases.append(tc_data)
                    await push_log(
                        task_id,
                        "用例生成",
                        f"⚠️ 「{requirement.name}」JSON解析失败，使用降级方案生成 {len(testcases_data)} 个用例",
                        "thinking"
                    )
                else:
                    # 确实无法解析时，创建一个默认用例
                    logger.warning(f"降级方案也失败，创建默认用例: {e}")
                    default_case = {
                        "title": f"{requirement.name} - 测试用例",
                        "desc": f"由需求「{requirement.name}」自动生成的测试用例",
                        "priority": "中",
                        "preconditions": "无",
                        "test_data": "",
                        "steps": [
                            {"description": "执行测试步骤", "expected_result": "符合预期结果"}
                        ],
                        "requirement_id": req_id,
                        "requirement_name": requirement.name
                    }
                    all_generated_cases.append(default_case)
                    await push_log(
                        task_id,
                        "用例生成",
                        f"⚠️ 「{requirement.name}」创建默认测试用例",
                        "thinking"
                    )

        stage_timings['testcase_generation'] = time.time() - stage2_start
        
        # ========== 阶段3：AI评审 ==========
        # 静默执行，不打印阶段转换日志
        # await push_log(task_id, "System", f"✅ 并行生成完成，共 {len(all_generated_cases)} 个测试用例", "response")
        logger.info(f"[AI评审] 开始评审阶段，用例数量: {len(all_generated_cases)}")
        await update_step('TestCaseReviewAgent', "正在评审测试用例...")

        # 创建流式缓冲器（新增流式输出）
        review_stream_buffer = StreamBuffer(task_id, "用例评审", buffer_size=200)
        logger.info(f"[AI评审] 创建流式缓冲器完成")
        await review_stream_buffer.start("⏳ AI正在评审测试用例...\n\n")
        logger.info(f"[AI评审] 流式开始消息已发送")

        review_agent = AssistantAgent(
            name='review_agent',
            model_client=review_client,
            system_message=await PromptLoader.get_prompt("testcase_batch_review"),
            model_client_stream=True  # 启用流式
        )

        cases_text = json.dumps(all_generated_cases, ensure_ascii=False, indent=2)
        review_task = f"请评审以下{len(all_generated_cases)}个测试用例：\n{cases_text}"

        # 流式输出
        stream = review_agent.run_stream(task=review_task)
        review_content = ""
        chunk_count = 0
        msg_types_seen = []  # 记录见过的消息类型

        async for msg in stream:
            msg_type = type(msg).__name__
            if msg_type not in msg_types_seen:
                msg_types_seen.append(msg_type)
                logger.info(f"[AI评审] 收到新类型消息: {msg_type}")
            
            if isinstance(msg, ModelClientStreamingChunkEvent):
                chunk_count += 1
                if chunk_count == 1:  # 只在第一个chunk打印日志
                    logger.info(f"[AI评审] 收到第一个chunk")
                await review_stream_buffer.append(msg.content)
            elif isinstance(msg, TaskResult):
                logger.info(f"[AI评审] TaskResult完成，收到 {chunk_count} 个chunks")
                await review_stream_buffer.flush()
                review_content = msg.messages[-1].content
                await review_stream_buffer.end("\n\n✅ 评审完成")
                logger.info(f"[AI评审] 流式结束消息已发送")
            else:
                # 打印其他消息类型的内容摘要
                if hasattr(msg, 'content'):
                    content_preview = str(msg.content)[:100] if msg.content else "None"
                    logger.info(f"[AI评审] 其他消息类型: {msg_type}, content: {content_preview}...")

        # 解析评审结果
        review_conclusion = {
            "approved": True,
            "summary": "评审通过",
            "total_testcases": len(all_generated_cases),
            "coverage_rate": "100%",
            "issues": [],
            "suggestions": []
        }

        try:
            # 尝试提取JSON (使用健壮的解析器)
            parsed_review = _parse_json_object_from_text(review_content)
            if parsed_review:
                review_conclusion = {
                    "approved": parsed_review.get("approved", True),
                    "summary": parsed_review.get("summary", "评审通过"),
                    "total_testcases": parsed_review.get("total_testcases", len(all_generated_cases)),
                    "coverage_rate": parsed_review.get("coverage_rate", "100%"),
                    "issues": parsed_review.get("issues", []),
                    "suggestions": parsed_review.get("suggestions", [])
                }
            else:
                # 使用默认评审结论
                logger.warning("无法解析评审结果JSON，使用默认结论")
                review_conclusion = {
                    "approved": True,
                    "summary": "评审通过",
                    "total_testcases": len(all_generated_cases),
                    "coverage_rate": "100%",
                    "issues": [],
                    "suggestions": []
                }
        except Exception as e:
            logger.warning(f"解析评审结果失败: {e}")

        # 输出评审完成消息（简化版）
        coverage_rate = review_conclusion.get('coverage_rate', '100%')
        if isinstance(coverage_rate, str):
            # 处理中文数字和特殊字符，如 "约85%"、"85%"、"80%" 等
            numeric_part = re.search(r'[\d.]+', coverage_rate)
            if numeric_part:
                value = float(numeric_part.group())
                # 如果包含百分号%，则转换为小数；否则直接使用数值
                if '%' in coverage_rate:
                    coverage_rate = value / 100
                else:
                    coverage_rate = value  # 直接作为百分比数值
            else:
                coverage_rate = 100.0  # 默认100%
        
        # 转换为百分比并限制在合理范围 (0-100%)
        if isinstance(coverage_rate, float):
            coverage_percent = min(max(coverage_rate, 0), 100)
        else:
            coverage_percent = 100

        await push_log(task_id, "用例评审", f"✅ AI评审完成 (覆盖率: {coverage_percent:.1f}%)", "response")

        # ========== 发送第一版测试用例到前端（美观的卡片展示）==========
        # await push_log(task_id, "第一版用例", f"[FIRST_TC]{json.dumps(all_generated_cases, ensure_ascii=False)}[/FIRST_TC]", "stream")

        # ========== 发送评审结论到前端（美观的卡片展示）==========
        # await push_log(task_id, "评审结论", f"[REVIEW_RESULT]{json.dumps(review_conclusion, ensure_ascii=False)}[/REVIEW_RESULT]", "response")

        # ========== 阶段4：整体定稿优化 ==========
        await update_step('TestCaseFinalizeAgent', "正在整体优化测试用例...")

        # 创建流式缓冲器
        finalize_stream_buffer = StreamBuffer(task_id, "格式优化", buffer_size=200)
        await finalize_stream_buffer.start("⏳ AI正在整体优化测试用例...\n\n")

        finalize_agent = AssistantAgent(
            name='finalize_agent',
            model_client=review_client,
            system_message=await PromptLoader.get_prompt("testcase_finalize"),
            model_client_stream=True  # 启用流式
        )

        finalize_task = f"""请根据以下测试用例及评审报告，一次性优化所有用例：

--测试用例开始--
{cases_text}
--测试用例结束--

--评审报告开始--
{review_content}
--评审报告结束--

请输出优化后的完整测试用例JSON数组："""

        final_testcase = ""

        stream = finalize_agent.run_stream(task=finalize_task)
        async for msg in stream:
            if isinstance(msg, ModelClientStreamingChunkEvent):
                await finalize_stream_buffer.append(msg.content)
            elif isinstance(msg, TaskResult):
                await finalize_stream_buffer.flush()
                final_testcase = msg.messages[-1].content
                await finalize_stream_buffer.end("\n\n✅ 优化完成")

        # 解析优化后的用例
        final_cases = []
        try:
            final_cases = _parse_json_from_text(final_testcase) or []
        except Exception as e:
            logger.warning(f"定稿JSON解析失败: {e}")
        
        # 如果没有解析到用例，使用原始用例
        if not final_cases:
            logger.info("使用原始用例继续处理")
            final_cases = all_generated_cases

        await push_log(task_id, "格式优化", f"✅ 整体优化完成，生成 {len(final_cases)} 个测试用例", "complete")

        # ========== 阶段5：合并去重 + 入库 ==========
        await update_step('TestCaseInDatabaseAgent', "正在保存用例...")

        logger.info(f"[TESTCASE_SAVE] 开始保存阶段, final_cases数量: {len(final_cases)}")

        saved_ids: List[int] = []
        # 使用整体定稿后的用例进行合并去重
        try:
            final_cases = _merge_similar_testcases(final_cases)
            logger.info(f"[TESTCASE_SAVE] 合并完成, 合并后用例数量: {len(final_cases)}")
        except Exception as e:
            logger.error(f"[TESTCASE_SAVE] 合并失败: {e}")
            await push_log(task_id, "System", f"⚠️ 用例合并失败: {str(e)}", "error")
        
        # 如果合并后用例数量显著减少，记录日志
        original_count = len(final_cases) if hasattr(final_cases, '__len__') else len(all_generated_cases)
        if len(final_cases) < original_count:
            await push_log(
                task_id,
                "用例优化",
                f"🔄 用例去重合并：{original_count} → {len(final_cases)} 个",
                "thinking"
            )
        
        try:
            for idx, tc_data in enumerate(final_cases):
                logger.info(f"[TESTCASE_SAVE] 正在保存第 {idx+1}/{len(final_cases)} 个用例")
                steps_data = tc_data.pop("steps", [])
                
                actual_project_id = tc_data.get("project_id", project_id)
                if actual_project_id is not None and actual_project_id == 0:
                    actual_project_id = project_id

                test_case = await TestCase.create(
                    project_id=actual_project_id,
                    requirement_id=tc_data.get("requirement_id"),
                    version_id=version_id,
                    title=tc_data.get("title", ""),
                    description=tc_data.get("desc", tc_data.get("description", "")),
                    priority=tc_data.get("priority", "中"),
                    test_type=tc_data.get("tags", "功能测试"),
                    preconditions=tc_data.get("preconditions", ""),
                    test_data=tc_data.get("test_data", ""),
                    creator=tc_data.get("creator", gen_model_name),
                    task_id=task_id,
                )

                for i, step_data in enumerate(steps_data, 1):
                    await TestStep.create(
                        test_case_id=test_case.id,
                        step_number=i,
                        description=step_data.get("description", ""),
                        expected_result=step_data.get("expected_result", ""),
                    )

                saved_ids.append(test_case.id)
                logger.info(f"[TESTCASE_SAVE] 已保存用例: {test_case.id}")

        except Exception as e:
            logger.error(f"入库失败: {e}")
            await push_log(task_id, "System", f"❌ 入库失败: {str(e)}", "error")
            raise  # 抛出异常，交由外层统一处理（testcases.py 第273行）

        # 无论成功失败都继续执行
        await push_log(task_id, "数据保存", f"💾 已保存 {len(saved_ids)} 个测试用例到数据库", "complete")

        # ========== 完成 ==========
        logger.info(f"[TESTCASE_SAVE] 保存完成，准备更新任务状态...")
        stage_timings['total'] = stage_timings['requirement_analysis'] + stage_timings['testcase_generation']
        total_duration = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"[TESTCASE_SAVE] 更新进度为100...")
        if task:
            # 直接更新为完成状态
            await task.update_testcase_progress(
                status="completed",
                progress=100,
                saved_count=len(saved_ids),
                saved_ids=saved_ids
            )
            # 保存评审结论、功能点ID和耗时统计到 result 字段
            await task.mark_complete(result={
                "review_conclusion": review_conclusion,  # 评审结论（包含问题、建议）
                "function_ids": requirement_ids,  # 功能点ID列表
                "stage_timings": stage_timings,  # 各阶段耗时统计
            })
        logger.info(f"[TESTCASE_SAVE] 任务状态更新完成")

        logger.info(f"[TESTCASE_SAVE] 推送完成日志...")
        await push_log(task_id, "System", f"🎉 测试用例生成完成！", "complete")
        logger.info(f"[TESTCASE_SAVE] 完成日志推送完成")
        
        # 发送完成消息给前端（使用数据保存，对应第7个智能体）
        logger.info(f"[TESTCASE_SAVE] 推送WebSocket完成消息...")
        from app.api.websocket import push_to_websocket
        await push_to_websocket(
            task_id,
            "数据保存",
            "complete",
            "complete",
            {
                "saved_ids": saved_ids, 
                "count": len(saved_ids),
                "function_ids": requirement_ids,  # 功能点ID列表
                "function_count": len(requirement_ids),
                "stage_timings": stage_timings,  # 各阶段耗时统计
                "review_conclusion": review_conclusion,  # 评审结论
                "model_info": model_info,  # AI模型信息
            }
        )
        logger.info(f"[TESTCASE_SAVE] WebSocket完成消息推送完成")

        return saved_ids

    except Exception as e:
        logger.error(f"用例生成失败: {e}")
        if task:
            await task.mark_failed(error_message=str(e))
        raise
