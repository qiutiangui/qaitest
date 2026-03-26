"""
功能点管理API
"""
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form, Body
from typing import Optional, List
import uuid
import asyncio
from datetime import datetime
from loguru import logger

from app.models import Requirement, AITestTask
from app.schemas.requirement import (
    RequirementCreate,
    RequirementUpdate,
    RequirementResponse,
    RequirementListResponse,
    RequirementGroupResponse,
)
from app.schemas.model_config import ModelConfigRequest
from app.rag.readers import UniversalDocumentReader

router = APIRouter()


@router.get("", response_model=RequirementListResponse)
async def list_requirements(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    project_id: Optional[int] = Query(None, description="项目ID"),
    version_id: Optional[int] = Query(None, description="版本ID"),
    category: Optional[str] = Query(None, description="类别筛选"),
    priority: Optional[str] = Query(None, description="优先级筛选"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    sort_by: Optional[str] = Query("created_at", description="排序字段(created_at/updated_at/priority)"),
    order: Optional[str] = Query("desc", description="排序方向(asc/desc)"),
):
    """获取功能点列表"""
    query = Requirement.all()
    
    if project_id:
        query = query.filter(project_id=project_id)
    if version_id:
        query = query.filter(version_id=version_id)
    if category:
        query = query.filter(category=category)
    if priority:
        query = query.filter(priority=priority)
    if keyword:
        query = query.filter(name__contains=keyword)
    
    # 排序
    order_prefix = "-" if order == "desc" else ""
    sort_field = f"{order_prefix}{sort_by}"
    query = query.order_by(sort_field)
    
    total = await query.count()
    items = await query.offset((page - 1) * page_size).limit(page_size)
    
    return RequirementListResponse(
        total=total,
        items=[RequirementResponse.model_validate(item) for item in items],
    )


@router.post("", response_model=RequirementResponse)
async def create_requirement(data: RequirementCreate):
    """创建功能点"""
    requirement = await Requirement.create(**data.model_dump())
    return RequirementResponse.model_validate(requirement)


@router.get("/groups")
async def get_requirement_groups(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    project_id: Optional[int] = Query(None, description="项目ID"),
):
    """
    按需求名称分组获取功能点列表
    
    返回每个需求名称作为一个分组的统计信息
    """
    # 构建基础查询
    query = Requirement.all()
    if project_id:
        query = query.filter(project_id=project_id)
    
    # 获取所有符合条件的功能点
    requirements = await query.order_by("-created_at")
    
    # 按 requirement_name 分组
    groups_dict = {}
    for req in requirements:
        key = req.requirement_name or "未命名需求"
        if key not in groups_dict:
            groups_dict[key] = {
                "requirement_name": req.requirement_name,
                "project_id": req.project_id,
                "version_id": req.version_id,
                "count": 0,
                "created_at": req.created_at,
            }
        groups_dict[key]["count"] += 1
    
    # 转换为列表并分页
    groups = list(groups_dict.values())
    total = len(groups)
    
    # 分页处理
    start = (page - 1) * page_size
    end = start + page_size
    paginated_groups = groups[start:end]
    
    return {
        "total": total,
        "items": paginated_groups,
    }


@router.post("/by-ids")
async def get_requirements_by_ids(ids: list[int]):
    """根据ID列表获取功能点"""
    requirements = await Requirement.filter(id__in=ids)
    return [RequirementResponse.model_validate(req) for req in requirements]


@router.get("/{requirement_id}", response_model=RequirementResponse)
async def get_requirement(requirement_id: int):
    """获取功能点详情"""
    requirement = await Requirement.get_or_none(id=requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="功能点不存在")
    return RequirementResponse.model_validate(requirement)


@router.put("/{requirement_id}", response_model=RequirementResponse)
async def update_requirement(requirement_id: int, data: RequirementUpdate):
    """更新功能点"""
    requirement = await Requirement.get_or_none(id=requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="功能点不存在")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(requirement, key, value)
    
    await requirement.save()
    return RequirementResponse.model_validate(requirement)


@router.delete("/{requirement_id}")
async def delete_requirement(
    requirement_id: int,
    delete_testcases: bool = Query(False, description="是否同步删除关联的测试用例")
):
    """删除功能点"""
    from app.models.testcase import TestCase
    
    requirement = await Requirement.get_or_none(id=requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="功能点不存在")
    
    deleted_testcase_count = 0
    
    # 如果需要同步删除测试用例
    if delete_testcases:
        deleted_testcase_count = await TestCase.filter(requirement_id=requirement_id).delete()
    
    # 删除功能点
    await requirement.delete()
    
    return {
        "message": "删除成功",
        "deleted_testcase_count": deleted_testcase_count
    }


@router.post("/batch-delete")
async def batch_delete_requirements(
    ids: list[int] = Body(...),
    delete_testcases: bool = Body(False, description="是否同步删除关联的测试用例")
):
    """批量删除功能点"""
    from app.models.testcase import TestCase
    
    if not ids:
        raise HTTPException(status_code=400, detail="请选择要删除的功能点")
    
    # 获取要删除的功能点
    requirements = await Requirement.filter(id__in=ids)
    
    if not requirements:
        raise HTTPException(status_code=404, detail="未找到要删除的功能点")
    
    deleted_testcase_count = 0
    
    # 如果需要同步删除测试用例
    if delete_testcases:
        deleted_testcase_count = await TestCase.filter(requirement_id__in=ids).delete()
    
    # 执行批量删除
    deleted_count = await Requirement.filter(id__in=ids).delete()
    
    return {
        "message": f"成功删除 {deleted_count} 个功能点",
        "deleted_count": deleted_count,
        "deleted_testcase_count": deleted_testcase_count
    }


@router.post("/by-name/delete")
async def delete_requirements_by_name(
    project_id: int = Form(...),
    requirement_name: str = Form(...),
    version_id: Optional[int] = Form(None)
):
    """按需求名称删除功能点及其向量数据"""
    from app.rag import get_index_manager
    
    # 查询该需求名称下的所有功能点
    query = Requirement.filter(project_id=project_id, requirement_name=requirement_name)
    if version_id:
        query = query.filter(version_id=version_id)
    
    requirements = await query
    requirement_count = len(requirements)
    
    if requirement_count == 0:
        raise HTTPException(status_code=404, detail="未找到对应的功能点")
    
    # 删除功能点
    deleted_count = await query.delete()
    
    # 删除对应的向量数据
    deleted_vector_count = 0
    try:
        index_manager = await get_index_manager()
        deleted_vector_count = await index_manager.delete_by_requirement(
            project_id=project_id,
            requirement_name=requirement_name,
            version_id=version_id
        )
    except Exception as e:
        logger.warning(f"删除向量数据失败: {e}")
    
    return {
        "message": f"成功删除需求「{requirement_name}」",
        "deleted_function_count": deleted_count,
        "deleted_vector_count": deleted_vector_count
    }


@router.post("/analyze")
async def analyze_requirements(
    project_id: Optional[int] = Form(None, description="项目ID（可选）"),
    version_id: Optional[int] = Form(None, description="版本ID（可选）"),
    requirement_name: Optional[str] = Form(None, description="需求名称"),
    description: str = Form("", description="需求描述"),
    file: Optional[UploadFile] = File(None, description="需求文档文件"),
    llm_config_json: Optional[str] = Form(None, alias="llm_config", description="模型配置JSON字符串"),
):
    """
    分析需求文档并提取功能点

    Args:
        project_id: 项目ID（可选）
        version_id: 版本ID（可选）
        requirement_name: 需求名称（上传文档模式必填）
        description: 需求描述
        file: 需求文档文件（支持txt/md/pdf/docx格式）

    Returns:
        task_id: 任务ID，用于WebSocket连接
    """
    # 记录接收到的参数
    logger.info(f"收到需求分析请求: project_id={project_id}, requirement_name={requirement_name}, version_id={version_id}")

    # 文档上传模式下，需求名称必填
    if file and not requirement_name:
        raise HTTPException(status_code=400, detail="文档上传模式下需求名称必填")

    # project_id 可以是 None，不需要设置默认值
    logger.info(f"project_id={project_id}, 将{'进行' if project_id else '不进行'} RAG索引")

    # 如果 requirement_name 为空且没有文件，使用默认值（兼容手动输入模式）
    if not requirement_name and not file:
        if project_id:
            requirement_name = f"项目{project_id}_默认需求"
        else:
            requirement_name = f"默认需求_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        logger.warning(f"requirement_name 为空，使用默认值: {requirement_name}")

    # 解析 llm_config JSON 字符串
    llm_config = None
    if llm_config_json:
        try:
            import json
            config_dict = json.loads(llm_config_json)
            llm_config = ModelConfigRequest.model_validate(config_dict)
            logger.info(f"解析到 llm_config: {llm_config}")
        except Exception as e:
            logger.error(f"解析 llm_config 失败: {e}")

    # 生成任务ID
    task_id = str(uuid.uuid4())

    # 创建任务记录（使用统一的 AITestTask）
    async_task = await AITestTask.create(
        task_id=task_id,
        project_id=project_id,
        version_id=version_id,
        task_name=requirement_name,
        status="pending",
        progress=0,
        input_source="file" if file else "description",
    )

    # 读取文件内容
    document_content = ""
    if file:
        try:
            content = await file.read()
            document_content = await UniversalDocumentReader.get_text(
                content,
                file.filename or "document.txt"
            )
        except Exception as e:
            logger.error(f"文件读取失败: {e}")
            raise HTTPException(status_code=400, detail=f"文件读取失败: {str(e)}")

    # 后台启动分析任务
    async def run_analysis():
        import asyncio  # 在嵌套函数内导入，避免作用域问题
        # 使用 Runtime 模式
        from app.agents.requirement_agents import run_requirement_analysis_with_runtime
        from app.api.websocket import push_to_websocket
        
        # 更新任务状态为运行中（使用 update_requirement_progress）
        task = await AITestTask.get(task_id=task_id)
        await task.update_requirement_progress(status="running", progress=10)
        
        try:
            logger.info(f"开始执行需求分析任务: {task_id}")
            saved_ids = await run_requirement_analysis_with_runtime(
                task_id=task_id,
                project_id=project_id,
                requirement_name=requirement_name,
                document_content=document_content,
                description=description,
                version_id=version_id,
                llm_config=llm_config,
            )
            
            # 更新任务状态为完成（使用 update_requirement_progress）
            await task.update_requirement_progress(
                status="completed",
                progress=100,
                saved_count=len(saved_ids),
                saved_ids=saved_ids
            )
            await task.mark_complete(result={
                "project_id": project_id,
                "version_id": version_id,
                "requirement_name": requirement_name
            })
            logger.info(f"需求分析任务完成: {task_id}, 保存了 {len(saved_ids)} 个功能点")
            
            # 发送WebSocket完成消息
            await push_to_websocket(
                task_id,
                "RequirementOutputAgent",
                f"✅ 需求分析完成！成功提取 {len(saved_ids)} 个功能点",
                "complete",
                extra_data={"saved_ids": saved_ids, "count": len(saved_ids)}
            )
            
        except Exception as e:
            logger.error(f"需求分析失败: {e}", exc_info=True)
            # 更新任务状态为失败（使用 mark_failed）
            await task.mark_failed(error_message=str(e))
            
            # 发送WebSocket错误消息
            await push_to_websocket(task_id, "System", f"❌ 需求分析失败: {str(e)}", "error")
    
    # 启动后台任务
    asyncio.create_task(run_analysis())
    
    return {
        "task_id": task_id,
        "message": "需求分析任务已启动",
    }


@router.post("/analyze-multiple")
async def analyze_multiple_requirements(
    files: List[UploadFile] = File(..., description="多个需求文档文件"),
    project_id: Optional[int] = Form(None, description="项目ID（可选）"),
    version_id: Optional[int] = Form(None, description="版本ID（可选）"),
    requirement_name: str = Form(..., description="需求名称"),
    llm_config_json: Optional[str] = Form(None, alias="llm_config", description="模型配置JSON字符串"),
):
    """
    并行分析多个需求文档并提取功能点

    Args:
        files: 多个需求文档文件列表（支持txt/md/pdf/docx格式）
        project_id: 项目ID（可选）
        version_id: 版本ID（可选）
        requirement_name: 需求名称

    Returns:
        task_id: 任务ID，用于WebSocket连接
        total_files: 文件总数
    """
    # 解析 llm_config JSON 字符串
    llm_config = None
    if llm_config_json:
        try:
            import json
            config_dict = json.loads(llm_config_json)
            llm_config = ModelConfigRequest.model_validate(config_dict)
            logger.info(f"解析到 llm_config: {llm_config}")
        except Exception as e:
            logger.error(f"解析 llm_config 失败: {e}")

    # 记录接收到的参数
    logger.info(f"收到多文档需求分析请求: project_id={project_id}, requirement_name={requirement_name}, files_count={len(files)}, llm_config={llm_config}")

    if len(files) == 0:
        raise HTTPException(status_code=400, detail="请至少上传一个文档")

    if len(files) > 10:
        raise HTTPException(status_code=400, detail="最多支持同时处理10个文档")

    # 生成任务ID
    task_id = str(uuid.uuid4())

    # 重要：先在当前请求线程中读取所有文件内容
    # 因为 UploadFile 在请求结束后会被关闭，必须在后台任务启动前读取
    file_data_list = []
    for idx, file in enumerate(files):
        try:
            content = await file.read()
            document_content = await UniversalDocumentReader.get_text(
                content,
                file.filename or f"document_{idx}.txt"
            )
            file_data_list.append({
                "filename": file.filename,
                "content": document_content,
                "index": idx
            })
            logger.info(f"成功读取文件: {file.filename}, 内容长度: {len(document_content)}")
        except Exception as e:
            logger.error(f"读取文件失败: {file.filename}, 错误: {e}")
            file_data_list.append({
                "filename": file.filename,
                "content": "",
                "index": idx,
                "error": str(e)
            })

    # 创建任务记录（使用统一的 AITestTask）
    async_task = await AITestTask.create(
        task_id=task_id,
        project_id=project_id,
        version_id=version_id,
        task_name=requirement_name,
        status="pending",
        progress=0,
        input_source="file",
    )

    # 后台启动并行分析任务
    async def run_parallel_analysis(file_data_list: list, llm_config: Optional[ModelConfigRequest] = None):
        """并行处理多个文档的需求分析"""
        import asyncio  # 在嵌套函数内导入，避免作用域问题
        # 使用 Runtime 模式
        from app.agents.requirement_agents import run_requirement_analysis_with_runtime
        from app.api.websocket import push_to_websocket

        # 更新任务状态为运行中（使用 update_requirement_progress）
        task = await AITestTask.get(task_id=task_id)
        await task.update_requirement_progress(status="running", progress=5)

        # 推送启动消息
        await push_to_websocket(task_id, "System", f"🚀 开始并行分析 {len(file_data_list)} 个文档", "thinking")

        # 定义处理单个文档的函数
        async def process_single_document(file_data: dict) -> List[int]:
            """处理单个文档的需求分析"""
            import asyncio  # 确保嵌套函数内可访问
            doc_index = file_data["index"]
            filename = file_data["filename"]
            document_content = file_data["content"]

            # 检查内容是否为空
            if not document_content or not document_content.strip():
                logger.warning(f"文档内容为空: {filename}")
                await push_to_websocket(
                    task_id,
                    "System",
                    f"⚠️ [{doc_index+1}] 文档内容为空: {filename}",
                    "error"
                )
                return []

            try:
                # 推送开始处理消息
                await push_to_websocket(
                    task_id,
                    "System",
                    f"📄 [{doc_index+1}/{len(file_data_list)}] 开始处理文档: {filename}",
                    "thinking"
                )

                # 运行需求分析（使用 Runtime 模式）
                saved_ids = await run_requirement_analysis_with_runtime(
                    task_id=task_id,
                    project_id=project_id,
                    requirement_name=requirement_name,
                    document_content=document_content,
                    description="",  # 批量上传模式下不使用description
                    version_id=version_id,
                    llm_config=llm_config,
                )

                # 推送完成消息
                await push_to_websocket(
                    task_id,
                    "RequirementOutputAgent",
                    f"✅ [{doc_index+1}/{len(file_data_list)}] 文档处理完成: {filename}，提取了 {len(saved_ids)} 个功能点",
                    "complete",
                    extra_data={"saved_ids": saved_ids, "count": len(saved_ids)}
                )

                return saved_ids

            except Exception as e:
                logger.error(f"处理文档失败: {filename}, 错误: {e}")
                await push_to_websocket(
                    task_id,
                    "System",
                    f"❌ [{doc_index+1}/{len(file_data_list)}] 文档处理失败: {filename}，错误: {str(e)}",
                    "error"
                )
                return []

        try:
            # 过滤掉读取失败的文件
            valid_file_data_list = [fd for fd in file_data_list if not fd.get("error")]
            failed_files = [fd for fd in file_data_list if fd.get("error")]

            # 报告失败的文件
            for fd in failed_files:
                await push_to_websocket(
                    task_id,
                    "System",
                    f"⚠️ 文件读取失败: {fd['filename']}，错误: {fd.get('error')}",
                    "error"
                )

            if not valid_file_data_list:
                raise Exception("所有文件读取失败")

            # 并行处理所有文档
            await push_to_websocket(task_id, "System", "⚡ 启动并行处理...", "thinking")

            results = await asyncio.gather(*[
                process_single_document(file_data)
                for file_data in valid_file_data_list
            ])

            # 合并所有功能点ID
            all_saved_ids = []
            for saved_ids in results:
                all_saved_ids.extend(saved_ids)

            # 更新任务状态为完成（使用 update_requirement_progress）
            await task.update_requirement_progress(
                status="completed",
                progress=100,
                saved_count=len(all_saved_ids),
                saved_ids=all_saved_ids
            )
            await task.mark_complete(result={
                "project_id": project_id,
                "version_id": version_id,
                "requirement_name": requirement_name,
                "total_files": len(file_data_list),
                "total_requirements": len(all_saved_ids),
            })

            # 推送最终完成消息
            await push_to_websocket(
                task_id,
                "System",
                f"🎉 所有文档处理完成！共提取 {len(all_saved_ids)} 个功能点",
                "complete",
                extra_data={"saved_ids": all_saved_ids}
            )

            logger.info(f"多文档需求分析完成: {task_id}, 处理了 {len(file_data_list)} 个文档，保存了 {len(all_saved_ids)} 个功能点")

        except Exception as e:
            logger.error(f"多文档需求分析失败: {e}", exc_info=True)
            # 更新任务状态为失败（使用 mark_failed）
            await task.mark_failed(error_message=str(e))

            # 推送错误消息
            await push_to_websocket(task_id, "System", f"❌ 多文档分析失败: {str(e)}", "error")

    # 启动后台任务，传入已读取的文件数据
    asyncio.create_task(run_parallel_analysis(file_data_list, llm_config))

    return {
        "task_id": task_id,
        "total_files": len(file_data_list),
        "message": f"已启动 {len(file_data_list)} 个文档的并行分析任务",
    }


@router.get("/stats/project/{project_id}")
async def get_requirement_stats(project_id: int):
    """获取项目的功能点统计信息"""
    total = await Requirement.filter(project_id=project_id).count()
    
    # 按类别统计
    categories = {}
    requirements = await Requirement.filter(project_id=project_id)
    for req in requirements:
        category = req.category or "未分类"
        categories[category] = categories.get(category, 0) + 1
    
    # 按优先级统计
    priorities = {}
    for req in requirements:
        priority = req.priority or "中"
        priorities[priority] = priorities.get(priority, 0) + 1
    
    return {
        "project_id": project_id,
        "total": total,
        "by_category": categories,
        "by_priority": priorities,
    }


@router.get("/export/{task_id}")
async def export_requirements(
    task_id: str,
    format: str = Query("excel", description="导出格式: excel")
):
    """根据任务ID导出功能点"""
    requirements = await Requirement.filter(task_id=task_id)

    # 返回Excel数据结构，前端处理导出
    data = []
    for i, req in enumerate(requirements, 1):
        row = {
            "序号": i,
            "功能点名称": req.name,
            "描述": req.description or "",
            "类别": req.category or "",
            "优先级": req.priority or "",
            "状态": req.status or "",
            "创建时间": req.created_at.strftime("%Y-%m-%d %H:%M:%S") if req.created_at else "",
        }
        data.append(row)

    return {"data": data, "format": "excel"}
