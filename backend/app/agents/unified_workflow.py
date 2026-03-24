"""
统一AI测试工作流 - 需求分析 + 用例生成一体化流程

流程：
1. 阶段1 - 需求分析（占40%进度）
   1.1 文档获取与解析
   1.2 需求文档分析
   1.3 功能点提取与保存
2. 阶段2 - 用例生成（占60%进度）
   2.1 RAG预检索
   2.2 并行用例生成
   2.3 AI评审
   2.4 用例保存
"""
from typing import List, Dict, Any, Optional
import json
import re
import asyncio
import time
from datetime import datetime
from loguru import logger

from app.models import AITestTask, Requirement, TestCase, TestStep
from app.api.websocket import push_to_websocket
from app.agents.prompt_loader import PromptLoader


# ============ 日志推送 ============

async def push_log(task_id: str, agent_name: str, content: str, message_type: str = "thinking", extra_data: dict = None):
    """推送日志消息到WebSocket并持久化到数据库"""
    try:
        await push_to_websocket(task_id, agent_name, content, message_type, extra_data)
        
        # 持久化到数据库
        task = await AITestTask.get_or_none(task_id=task_id)
        if task:
            level_map = {
                "thinking": "info",
                "response": "info",
                "complete": "success",
                "error": "error",
                "stream": "info",
            }
            level = level_map.get(message_type, "info")
            await task.add_log(agent_name, agent_name, content, level, message_type)
    except Exception as e:
        logger.error(f"push_log异常: {e}")


async def update_task_progress(task_id: str, phase_code: str, phase_name: str, 
                              progress: int = None, status: str = "running",
                              requirement_status: str = None, requirement_progress: int = None,
                              testcase_status: str = None, testcase_progress: int = None,
                              saved_requirements: int = None, saved_testcases: int = None):
    """更新任务进度"""
    try:
        task = await AITestTask.get_or_none(task_id=task_id)
        if not task:
            return
        
        # 更新阶段信息
        if phase_code:
            await task.update_phase(phase_code, phase_name, status)
        
        # 更新需求分析阶段
        if requirement_status:
            task.requirement_phase_status = requirement_status
            if requirement_progress is not None:
                task.requirement_phase_progress = requirement_progress
        
        # 更新用例生成阶段
        if testcase_status:
            task.testcase_phase_status = testcase_status
            if testcase_progress is not None:
                task.testcase_phase_progress = testcase_progress
        
        # 更新保存数量
        if saved_requirements is not None:
            task.saved_requirements = saved_requirements
        if saved_testcases is not None:
            task.saved_testcases = saved_testcases
        
        # 计算整体进度
        if requirement_status == "completed" and testcase_status == "completed":
            task.progress = 100
            task.status = "completed"
        elif requirement_status == "running":
            task.progress = int((requirement_progress or 0) * 0.4)
            task.status = "running"
        elif requirement_status == "completed":
            task.progress = 40
            if testcase_status == "running":
                task.progress = 40 + int((testcase_progress or 0) * 0.6)
                task.status = "running"
            elif testcase_status == "completed":
                task.progress = 100
                task.status = "completed"
        elif requirement_status == "failed":
            task.status = "failed"
        elif testcase_status == "failed":
            task.status = "failed"
        
        # 记录开始时间
        if task.status == "running" and task.started_at is None:
            task.started_at = datetime.now()
        
        await task.save()
        
        # 推送进度到WebSocket
        progress_tag = f"[PROGRESS]{task.progress}[/PROGRESS]" if task.progress is not None else ""
        await push_to_websocket(
            task_id,
            "System",
            f"{progress_tag}阶段更新: {phase_name} - {status}",
            "progress",
            {"phase": phase_code, "progress": task.progress}
        )
        
    except Exception as e:
        logger.error(f"更新任务进度失败: {e}")


# ============ JSON解析工具 ============

def parse_json_response(content: str) -> List[Dict[str, Any]]:
    """健壮的JSON解析函数"""
    if not content:
        return []
    
    content_clean = content.strip()
    if content_clean.startswith('```'):
        content_clean = re.sub(r'^```(?:json)?\s*', '', content_clean)
        content_clean = re.sub(r'\s*```$', '', content_clean)
    
    # 方法1: 直接解析
    try:
        data = json.loads(content_clean)
        if isinstance(data, dict) and "requirements" in data:
            return data["requirements"]
        elif isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass
    
    # 方法2: 提取数组部分
    try:
        match = re.search(r'"requirements"\s*:\s*\[', content_clean)
        if match:
            start = match.end()
            array_str = content_clean[start-1:]
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
                return json.loads(array_str[:end_pos])
    except Exception:
        pass
    
    # 方法3: 正则提取
    try:
        pattern = r'\{\s*"name"\s*:\s*"[^"]+"\s*,.*?\}'
        matches = re.findall(pattern, content_clean, re.DOTALL)
        requirements = []
        for match in matches:
            try:
                req = json.loads(match)
                if isinstance(req, dict) and "name" in req:
                    requirements.append(req)
            except:
                continue
        return requirements
    except Exception:
        pass
    
    return []


def parse_testcase_json(content: str) -> List[Dict[str, Any]]:
    """解析测试用例JSON"""
    if not content:
        return []
    
    content_clean = content.strip()
    if content_clean.startswith('```'):
        content_clean = re.sub(r'^```(?:json)?\s*', '', content_clean)
        content_clean = re.sub(r'\s*```$', '', content_clean)
    
    try:
        data = json.loads(content_clean)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "testcases" in data:
            return data["testcases"]
    except json.JSONDecodeError:
        pass
    
    # 尝试提取JSON数组
    try:
        json_match = re.search(r'\[[\s\S]*\]', content_clean)
        if json_match:
            return json.loads(json_match.group(0))
    except Exception:
        pass
    
    return []


# ============ 阶段1: 需求分析 ============

async def run_requirement_analysis(task_id: str, project_id: Optional[int], version_id: Optional[int],
                                   requirement_name: str, document_content: str, description: str):
    """
    执行需求分析阶段
    """
    from app.agents.runtime import get_deepseek_client, get_qwen_client
    from autogen_agentchat.agents import AssistantAgent
    
    # 更新阶段状态
    await update_task_progress(
        task_id, "requirement_acquire", "需求获取", 
        requirement_status="running", requirement_progress=5
    )
    await push_log(task_id, "System", "🚀 阶段1：需求分析开始", "thinking")
    
    # ========== 1.1 文档获取 ==========
    await push_log(task_id, "需求获取", "📖 开始获取需求内容...", "thinking")
    
    combined_input = ""
    if document_content:
        combined_input += f"【需求文档内容】\n{document_content}\n\n"
    if description:
        combined_input += f"【需求描述】\n{description}"
    
    # RAG索引
    chunk_count = 0
    if document_content or description:
        try:
            await push_log(task_id, "RAG索引", "⏳ 正在创建文档向量索引...", "thinking")
            
            from app.rag import get_index_manager
            index_manager = await get_index_manager()
            
            rag_content = document_content if document_content else description
            index_result = await index_manager.index_requirement_document(
                project_id=project_id,
                task_id=task_id,
                content=rag_content,
                filename="requirement_document.md",
                version_id=version_id,
                requirement_name=requirement_name,
                chunk_size=500,
                overlap=100
            )
            
            if index_result.get("success"):
                chunk_count = index_result.get('indexed', 0)
                await push_log(task_id, "RAG索引", f"✅ 文档索引完成：{chunk_count} 个文本块", "response")
            else:
                await push_log(task_id, "RAG索引", f"⚠️ RAG索引跳过：{index_result.get('error', '未知错误')}", "thinking")
        except Exception as e:
            logger.warning(f"RAG索引失败: {e}")
    
    await update_task_progress(
        task_id, "requirement_acquire", "需求获取", 
        requirement_status="running", requirement_progress=10
    )
    await push_log(task_id, "需求获取", "✅ 需求内容获取完成", "complete")
    
    # ========== 1.2 需求分析 ==========
    await update_task_progress(
        task_id, "requirement_analysis", "需求分析", 
        requirement_status="running", requirement_progress=15
    )
    await push_log(task_id, "需求分析", "⏳ 正在分析需求文档...", "thinking")
    
    analysis_prompt = """
    你是一位专业的软件需求文档分析师。请仔细阅读并理解需求文档内容，然后进行整理和摘要。
    
    重点提取和归纳以下信息:
    1. 主要功能需求
    2. 非功能性需求
    3. 业务背景与目标
    4. 用户角色与关键使用场景
    5. 核心术语与概念定义
    6. 数据需求
    7. 依赖关系与约束
    8. 潜在歧义与待确认点
    
    请以结构化、层次清晰的 Markdown 格式输出你的分析摘要。
    """
    
    acquisition_agent = AssistantAgent(
        name='acquisition_agent',
        model_client=get_deepseek_client(),
        system_message=analysis_prompt,
        model_client_stream=False
    )
    
    result = await acquisition_agent.run(task=f"请分析以下需求文档内容:\n\n{combined_input}")
    analysis_content = result.messages[-1].content
    
    await push_log(task_id, "需求分析", "✅ 需求分析完成", "complete")
    
    # ========== 1.3 功能点提取 ==========
    await update_task_progress(
        task_id, "requirement_output", "功能点提取", 
        requirement_status="running", requirement_progress=25
    )
    await push_log(task_id, "功能点提取", "📝 开始提取功能点...", "thinking")
    
    output_prompt = """
请根据需求分析报告进行需求整理。
重要约束：
1. 数量控制：小型功能建议3-8个，中型建议8-12个，不要超过15个
2. 合并原则：相关的小功能合并为一个功能点，不要过度拆分
3. 核心优先：只提取核心功能点，边缘场景可合并到主功能中
4. 输出格式：输出必须是一个有效的JSON格式，不要包含任何解释或前导文本。仅输出JSON对象本身，包含requirements数组。

生成的JSON格式必须符合这个结构:
{
  "requirements": [
    {
      "name": "需求名称",
      "description": "明确的功能点描述",
      "category": "功能/性能/安全/接口/体验/改进/其它",
      "module": "所属的业务模块",
      "priority": "高/中/低",
      "acceptance_criteria": "明确的验收标准",
      "keywords": "提取当前需求的关键词，逗号分隔"
    }
  ]
}
"""
    
    output_agent = AssistantAgent(
        name='output_agent',
        model_client=get_qwen_client(),
        system_message=output_prompt,
        model_client_stream=False
    )
    
    result = await output_agent.run(task=f"根据以下需求分析报告，生成结构化需求列表：\n\n{analysis_content}")
    output_content = result.messages[-1].content
    
    # 解析JSON
    requirements = parse_json_response(output_content)
    
    # 解析失败时创建默认功能点
    if not requirements and output_content and len(output_content.strip()) > 50:
        requirements = _create_default_requirements(output_content, requirement_name)
    
    await push_log(task_id, "功能点提取", f"✅ 功能点提取完成，共 {len(requirements)} 个", "complete")

    # ========== 1.4 发送结构化功能点数据到前端 ==========

    # ========== 1.5 保存功能点 ==========
    await update_task_progress(
        task_id, "requirement_save", "功能点保存", 
        requirement_status="running", requirement_progress=35
    )
    await push_log(task_id, "功能点保存", "💾 正在保存功能点到数据库...", "thinking")
    
    saved_ids = []
    for req_data in requirements:
        try:
            req_name = req_data.get("name", "")
            requirement = await Requirement.create(
                project_id=project_id,
                version_id=version_id,
                requirement_name=requirement_name,
                name=req_name,
                description=req_data.get("description", ""),
                category=req_data.get("category", ""),
                module=req_data.get("module", ""),
                priority=req_data.get("priority", "中"),
                acceptance_criteria=req_data.get("acceptance_criteria", ""),
                keywords=req_data.get("keywords", ""),
                task_id=task_id,
            )
            saved_ids.append(requirement.id)
        except Exception as e:
            logger.error(f"保存功能点失败: {e}")
    
    # 更新任务记录
    task = await AITestTask.get(task_id=task_id)
    task.saved_requirement_ids = saved_ids
    task.total_requirements = len(requirements)
    task.saved_requirements = len(saved_ids)
    # 持久化文档分块数量
    if not task.result:
        task.result = {}
    task.result["doc_chunk_count"] = chunk_count
    await task.save()
    
    await push_log(task_id, "功能点保存", f"✅ 已保存 {len(saved_ids)} 个功能点到数据库", "complete", 
                   {"count": len(saved_ids), "saved_ids": saved_ids})
    
    # 需求分析阶段完成
    await update_task_progress(
        task_id, "requirement_complete", "需求分析完成", 
        requirement_status="completed", requirement_progress=40,
        saved_requirements=len(saved_ids)
    )
    await push_log(task_id, "System", "✅ 阶段1需求分析完成！", "complete",
                   {"total_requirements": len(saved_ids)})
    
    return saved_ids


def _create_default_requirements(content: str, requirement_name: str = "") -> List[Dict[str, Any]]:
    """创建默认功能点（当JSON解析失败时）"""
    requirements = []
    
    clean_content = re.sub(r'```[\s\S]*?```', '', content)
    clean_content = re.sub(r'#{1,6}\s+', '', clean_content)
    clean_content = re.sub(r'\*\*(.*?)\*\*', r'\1', clean_content)
    
    paragraphs = re.split(r'\n\s*\n', clean_content)
    for i, para in enumerate(paragraphs):
        para = para.strip()
        if not para or len(para) < 20:
            continue
        
        first_line = para.split('\n')[0].strip()
        name = first_line[:80] if len(first_line) > 80 else first_line
        if not name:
            name = f"功能点_{i+1}"
        
        requirements.append({
            "name": name,
            "description": para[:500],
            "category": "功能需求",
            "module": "",
            "priority": "中"
        })
    
    if len(requirements) > 20:
        requirements = requirements[:20]
    
    return requirements


# ============ 阶段2: 用例生成 ============

async def run_testcase_generation(task_id: str, project_id: Optional[int], version_id: Optional[int],
                                  requirement_ids: List[int]):
    """
    执行用例生成阶段
    """
    from app.agents.runtime import get_model_clients, get_deepseek_client
    from autogen_agentchat.agents import AssistantAgent
    
    # 更新阶段状态
    await update_task_progress(
        task_id, "testcase_prepare", "用例生成准备", 
        testcase_status="running", testcase_progress=0
    )
    await push_log(task_id, "System", "🚀 阶段2：用例生成开始", "thinking")
    
    # 获取模型客户端（使用异步版本）
    _, generate_client, review_client = await get_model_clients(None, None)
    
    # ========== 2.1 获取功能点 ==========
    await push_log(task_id, "用例生成", "📋 正在获取功能点...", "thinking")
    requirements = await Requirement.filter(id__in=requirement_ids).prefetch_related("project")
    await push_log(task_id, "用例生成", f"✅ 已获取 {len(requirements)} 个功能点", "response")
    
    # ========== 2.2 RAG预检索 ==========
    await update_task_progress(
        task_id, "testcase_rag", "RAG检索", 
        testcase_status="running", testcase_progress=10
    )
    await push_log(task_id, "RAG检索", "⏳ 正在检索相关文档...", "thinking")
    
    rag_cache: Dict[int, str] = {}
    try:
        from app.rag import get_index_manager
        index_manager = await get_index_manager()
        
        rag_semaphore = asyncio.Semaphore(2)
        
        async def _rag_search(req):
            async with rag_semaphore:
                try:
                    query_text = f"{req.name}\n{req.description or ''}"
                    results = await asyncio.wait_for(
                        index_manager.search_for_testcase_generation(
                            requirement=query_text,
                            project_id=project_id,
                            version_id=version_id,
                            task_id=task_id,
                            top_k=5,
                            score_threshold=0.30
                        ),
                        timeout=10.0
                    )
                    return req.id, results
                except Exception as e:
                    logger.warning(f"RAG检索失败: {e}")
                    return req.id, []
        
        rag_tasks = [_rag_search(req) for req in requirements]
        rag_results_list = await asyncio.wait_for(
            asyncio.gather(*rag_tasks, return_exceptions=True),
            timeout=60.0
        )
        
        for result in rag_results_list:
            if isinstance(result, Exception):
                continue
            req_id, rag_results = result
            if rag_results:
                context_parts = []
                for r in rag_results[:3]:
                    context_parts.append(f"【相关需求片段】\n{r.get('content', '')}")
                rag_cache[req_id] = "\n\n".join(context_parts)
        
        await push_log(task_id, "RAG检索", f"✅ RAG预检索完成：已缓存 {len(rag_cache)} 个功能点的上下文", "complete")
        
    except Exception as e:
        logger.warning(f"RAG预检索失败: {e}")
        await push_log(task_id, "RAG检索", f"⚠️ RAG检索跳过：{str(e)[:30]}", "thinking")
    
    # ========== 2.3 并行用例生成 ==========
    await update_task_progress(
        task_id, "testcase_generate", "用例生成", 
        testcase_status="running", testcase_progress=30
    )
    
    all_generated_cases: List[Dict[str, Any]] = []
    semaphore = asyncio.Semaphore(3)
    
    async def _generate_for_requirement(req_id: int, idx: int, total: int) -> List[Dict[str, Any]]:
        generated_cases: List[Dict[str, Any]] = []
        
        async with semaphore:
            requirement = await Requirement.get_or_none(id=req_id)
            if not requirement:
                return generated_cases
            
            # 静默执行，不打印开始处理日志
            # await push_log(task_id, "用例生成", f"📝 [{idx+1}/{total}] 开始处理: {requirement.name}", "thinking")
            
            try:
                rag_context = rag_cache.get(req_id, "")
                
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
                    model_client_stream=False
                )
                
                task_prompt = f"请根据以下需求生成测试用例：\n\n需求名称：{requirement.name}\n描述：{requirement.description or '无'}"
                
                result = await generate_agent.run(task=task_prompt)
                testcase_content = result.messages[-1].content
                
                # 解析JSON
                try:
                    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', testcase_content)
                    if json_match:
                        testcase_content = json_match.group(1)
                    
                    testcases_data = json.loads(testcase_content.strip())
                    if isinstance(testcases_data, dict):
                        testcases_data = testcases_data.get("testcases", [testcases_data])
                    
                    for tc_data in testcases_data:
                        tc_data["requirement_id"] = req_id
                        tc_data["requirement_name"] = requirement.name
                        generated_cases.append(tc_data)
                    
                    # 豆包风格：流式输出每个用例
                    await push_log(task_id, "TestCaseGenerateAgent", f"✓ {requirement.name}: 生成 {len(testcases_data)} 个用例", "stream")
                    
                except json.JSONDecodeError as e:
                    logger.error(f"JSON解析失败: {e}")
                    # 静默执行，不打印解析失败日志
                    # await push_log(task_id, "用例生成", f"⚠️ [{idx+1}/{total}] 测试用例格式解析失败", "thinking")
                    
            except Exception as e:
                logger.error(f"生成测试用例失败: {e}")
                # 静默执行，不打印失败日志
                # await push_log(task_id, "用例生成", f"❌ [{idx+1}/{total}] 生成失败: {str(e)}", "error")
        
        return generated_cases
    
    # 静默执行，不打印开始生成日志
    # await push_log(task_id, "用例生成", f"⏳ 并行生成测试用例中... (共 {len(requirements)} 个功能点)", "thinking")
    await push_log(task_id, "用例生成", "⏳ 正在并行生成测试用例...", "thinking")
    
    results = await asyncio.gather(*[
        _generate_for_requirement(req.id, idx, len(requirements))
        for idx, req in enumerate(requirements)
    ])
    
    for cases in results:
        all_generated_cases.extend(cases)
    
    # 静默执行，不打印完成日志（只保留最终汇总）
    # await push_log(task_id, "用例生成", f"✅ 并行生成完成，共 {len(all_generated_cases)} 个测试用例", "response")
    await push_log(task_id, "用例生成", f"✅ 已生成 {len(all_generated_cases)} 个测试用例", "complete")
    
    # ========== 2.4 发送第一版测试用例数据到前端 ==========

    # ========== 2.5 AI评审 ==========
    await update_task_progress(
        task_id, "testcase_review", "用例评审", 
        testcase_status="running", testcase_progress=70
    )
    await push_log(task_id, "用例评审", "⏳ AI评审中...", "thinking")
    
    review_agent = AssistantAgent(
        name='review_agent',
        model_client=review_client,
        system_message=await PromptLoader.get_prompt("testcase_batch_review"),
        model_client_stream=False
    )
    
    cases_text = json.dumps(all_generated_cases, ensure_ascii=False, indent=2)
    review_task = f"请评审以下{len(all_generated_cases)}个测试用例：\n{cases_text}"
    
    review_result = await review_agent.run(task=review_task)
    review_content = review_result.messages[-1].content
    
    # 解析评审结果
    review_conclusion = {"approved": True, "summary": "评审通过", "total_testcases": len(all_generated_cases)}
    try:
        review_json_match = re.search(r'\{[\s\S]*\}', review_content)
        if review_json_match:
            review_conclusion = json.loads(review_json_match.group(0))
    except Exception as e:
        logger.warning(f"解析评审结果失败: {e}")
    
    coverage_rate = review_conclusion.get('coverage_rate', '100%')
    if isinstance(coverage_rate, str):
        # 处理中文数字和特殊字符，如 "约85%"、"85%" 等
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

    # ========== 2.6 发送评审结论到前端 ==========
    # 豆包风格：只显示评审摘要，不发送JSON卡片
    # await push_log(task_id, "评审结论", f"[REVIEW_RESULT]{json.dumps(review_conclusion, ensure_ascii=False)}[/REVIEW_RESULT]", "response")

    # ========== 2.7 保存用例 ==========
    await update_task_progress(
        task_id, "testcase_save", "用例保存", 
        testcase_status="running", testcase_progress=90
    )
    await push_log(task_id, "用例保存", "💾 正在保存测试用例到数据库...", "thinking")
    
    saved_testcase_ids: List[int] = []
    
    for tc_data in all_generated_cases:
        try:
            steps_data = tc_data.pop("steps", [])
            
            test_case = await TestCase.create(
                project_id=tc_data.get("project_id", project_id),
                requirement_id=tc_data.get("requirement_id"),
                version_id=version_id,
                title=tc_data.get("title", ""),
                description=tc_data.get("desc", tc_data.get("description", "")),
                priority=tc_data.get("priority", "中"),
                test_type=tc_data.get("tags", "功能测试"),
                preconditions=tc_data.get("preconditions", ""),
                test_data=tc_data.get("test_data", ""),
                creator="AI",
                task_id=task_id,
            )
            
            for i, step_data in enumerate(steps_data, 1):
                await TestStep.create(
                    test_case_id=test_case.id,
                    step_number=i,
                    description=step_data.get("description", ""),
                    expected_result=step_data.get("expected_result", ""),
                )
            
            saved_testcase_ids.append(test_case.id)
            
        except Exception as e:
            logger.error(f"保存测试用例失败: {e}")
    
    # 更新任务记录
    task = await AITestTask.get(task_id=task_id)
    task.saved_testcase_ids = saved_testcase_ids
    task.total_testcases = len(all_generated_cases)
    task.saved_testcases = len(saved_testcase_ids)
    task.testcase_phase_status = "completed"
    task.testcase_phase_progress = 100
    task.status = "completed"
    task.progress = 100
    task.completed_at = datetime.now()
    task.result = {
        "review_conclusion": review_conclusion,
        "function_ids": requirement_ids,
        "function_count": len(requirement_ids),
    }
    await task.save()
    
    await push_log(task_id, "用例保存", f"✅ 已保存 {len(saved_testcase_ids)} 个测试用例到数据库", "complete",
                   {"count": len(saved_testcase_ids)})

    # ========== 2.8 发送最终测试用例数据到前端 ==========
    # 豆包风格：只显示完成摘要，不发送JSON卡片
    # await push_log(task_id, "最终用例", f"[FINAL_TC]{json.dumps(final_tc_data, ensure_ascii=False)}[/FINAL_TC]", "complete")

    # 整体完成
    await push_log(task_id, "System", "🎉 AI测试任务完成！", "complete", {
        "total_requirements": len(requirement_ids),
        "total_testcases": len(saved_testcase_ids),
    })
    
    return saved_testcase_ids


# ============ 统一工作流入口 ============

async def run_unified_ai_test_workflow(
    task_id: str,
    project_id: Optional[int],
    version_id: Optional[int],
    task_name: str,
    document_content: str,
    description: str,
):
    """
    统一AI测试工作流入口
    
    整合需求分析和用例生成，一个任务卡片展示完整流程
    """
    from app.api.websocket import push_to_websocket
    
    start_time = datetime.now()
    
    try:
        # 更新任务状态为运行中
        task = await AITestTask.get(task_id=task_id)
        task.status = "running"
        task.started_at = datetime.now()
        await task.save()
        
        # 推送启动消息
        await push_log(task_id, "System", "🚀 AI测试任务启动", "thinking")
        
        # ========== 阶段1: 需求分析 ==========
        requirement_ids = await run_requirement_analysis(
            task_id=task_id,
            project_id=project_id,
            version_id=version_id,
            requirement_name=task_name or "未命名需求",
            document_content=document_content,
            description=description,
        )
        
        # 检查是否被取消
        task = await AITestTask.get(task_id=task_id)
        if task.status == "cancelled":
            await push_log(task_id, "System", "⚠️ 任务已被取消", "warning")
            return
        
        if not requirement_ids:
            await push_log(task_id, "System", "⚠️ 未提取到功能点，跳过用例生成", "warning")
            await update_task_progress(task_id, "complete", "任务完成", 
                                     requirement_status="completed", requirement_progress=40)
            task = await AITestTask.get(task_id=task_id)
            task.status = "completed"
            task.progress = 40
            await task.save()
            return
        
        # ========== 阶段2: 用例生成 ==========
        await run_testcase_generation(
            task_id=task_id,
            project_id=project_id,
            version_id=version_id,
            requirement_ids=requirement_ids,
        )
        
        # 发送完成消息到WebSocket
        duration = (datetime.now() - start_time).total_seconds()
        await push_to_websocket(
            task_id,
            "System",
            "complete",
            "complete",
            {
                "total_requirements": len(requirement_ids),
                "total_testcases": len(requirement_ids),  # 近似值
                "duration": duration,
            }
        )
        
        logger.info(f"AI测试任务完成: task_id={task_id}, 功能点={len(requirement_ids)}, 耗时={duration:.1f}s")
        
    except Exception as e:
        logger.error(f"AI测试任务失败: {e}", exc_info=True)
        
        # 更新任务状态为失败
        task = await AITestTask.get_or_none(task_id=task_id)
        if task:
            task.status = "failed"
            task.error_message = str(e)
            task.completed_at = datetime.now()
            await task.save()
        
        await push_log(task_id, "System", f"❌ 任务失败: {str(e)}", "error")
        
        # 发送失败消息到WebSocket
        await push_to_websocket(task_id, "System", f"任务失败: {str(e)}", "error")
