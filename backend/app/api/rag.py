"""
RAG索引管理API
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from typing import Optional, List
from loguru import logger

router = APIRouter()


@router.get("/stats/{project_id}")
async def get_index_stats(project_id: int):
    """
    获取项目的向量索引状态
    
    Args:
        project_id: 项目ID
    
    Returns:
        索引统计信息
    """
    from app.rag import get_index_manager
    
    try:
        index_manager = await get_index_manager()
        stats = await index_manager.get_project_index_stats(project_id)
        
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        logger.error(f"获取索引状态失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": {"exists": False, "count": 0}
        }


@router.get("/files/{project_id}")
async def get_indexed_files(project_id: int):
    """
    获取已索引的文件列表
    
    Args:
        project_id: 项目ID
    
    Returns:
        已索引文件列表
    """
    from app.rag import get_index_manager
    
    try:
        index_manager = await get_index_manager()
        files = await index_manager.get_indexed_files(project_id)
        
        return {
            "success": True,
            "count": len(files),
            "data": files
        }
    except Exception as e:
        logger.error(f"获取已索引文件列表失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "count": 0,
            "data": []
        }


@router.post("/index")
async def index_document(
    project_id: int = Form(..., description="项目ID"),
    version_id: Optional[int] = Form(None, description="版本ID"),
    file: Optional[UploadFile] = File(None, description="需求文档文件"),
    content: Optional[str] = Form(None, description="需求文档文本内容"),
    filename: Optional[str] = Form(None, description="文档名称"),
):
    """
    手动索引需求文档
    
    支持两种方式：
    1. 上传文件：支持 txt/md/pdf/docx 格式
    2. 直接提供文本内容
    """
    from app.rag import get_index_manager
    from app.rag.readers import UniversalDocumentReader
    
    try:
        # 获取文档内容
        document_content = ""
        doc_filename = filename or "manual_input.md"
        
        if file:
            # 从文件读取
            file_content = await file.read()
            document_content = await UniversalDocumentReader.get_text(
                file_content, 
                file.filename or "document.txt"
            )
            doc_filename = file.filename or "uploaded_document"
        elif content:
            document_content = content
        else:
            raise HTTPException(status_code=400, detail="请提供文件或文本内容")
        
        if not document_content or not document_content.strip():
            raise HTTPException(status_code=400, detail="文档内容为空")
        
        # 索引文档
        index_manager = await get_index_manager()
        result = await index_manager.index_requirement_document(
            project_id=project_id,
            content=document_content,
            filename=doc_filename,
            version_id=version_id,
            chunk_size=500,
            overlap=100
        )
        
        if result.get("success"):
            return {
                "success": True,
                "message": f"成功索引 {result.get('indexed', 0)} 个文本块",
                "data": result
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "索引失败"),
                "data": result
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"索引文档失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/update")
async def update_index(
    project_id: int = Form(..., description="项目ID"),
    version_id: Optional[int] = Form(None, description="版本ID"),
    file: Optional[UploadFile] = File(None, description="更新后的需求文档文件"),
    content: Optional[str] = Form(None, description="更新后的文档内容"),
    filename: Optional[str] = Form(None, description="文档名称"),
):
    """
    增量更新索引
    
    删除旧索引后，索引新内容，    """
    from app.rag import get_index_manager
    from app.rag.readers import UniversalDocumentReader
    
    try:
        # 获取文档内容
        document_content = ""
        doc_filename = filename or "updated_document.md"
        
        if file:
            file_content = await file.read()
            document_content = await UniversalDocumentReader.get_text(
                file_content,
                file.filename or "document.txt"
            )
            doc_filename = file.filename or "uploaded_document"
        elif content:
            document_content = content
        else:
            raise HTTPException(status_code=400, detail="请提供文件或文本内容")
        
        if not document_content or not document_content.strip():
            raise HTTPException(status_code=400, detail="文档内容为空")
        
        # 增量更新
        index_manager = await get_index_manager()
        result = await index_manager.incremental_update(
            project_id=project_id,
            content=document_content,
            filename=doc_filename,
            version_id=version_id
        )
        
        if result.get("success"):
            return {
                "success": True,
                "message": result.get("message", "更新完成"),
                "data": result
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "更新失败"),
                "data": result
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"增量更新失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.delete("/index/{project_id}")
async def delete_index(project_id: int):
    """
    删除项目的向量索引
    
    Args:
        project_id: 项目ID
    
    Returns:
        删除结果
    """
    from app.rag import get_index_manager
    
    try:
        index_manager = await get_index_manager()
        success = await index_manager.delete_project_index(project_id)
        
        if success:
            return {
                "success": True,
                "message": f"已删除项目 {project_id} 的向量索引"
            }
        else:
            return {
                "success": False,
                "error": "删除失败，可能索引不存在或向量数据库未连接"
            }
            
    except Exception as e:
        logger.error(f"删除索引失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.delete("/index/version/{project_id}/{version_id}")
async def delete_index_by_version(project_id: int, version_id: int):
    """
    按版本ID删除向量数据
    
    Args:
        project_id: 项目ID
        version_id: 版本ID
    
    Returns:
        删除结果
    """
    from app.rag import get_index_manager
    
    try:
        index_manager = await get_index_manager()
        deleted_count = await index_manager.delete_by_version(project_id, version_id)
        
        return {
            "success": True,
            "message": f"已删除 {deleted_count} 条版本向量数据",
            "deleted_count": deleted_count
        }
            
    except Exception as e:
        logger.error(f"按版本删除向量数据失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "deleted_count": 0
        }


class DeleteByRequirementRequest:
    """按需求删除请求体"""
    def __init__(
        self,
        project_id: int,
        requirement_name: str,
        version_id: Optional[int] = None
    ):
        self.project_id = project_id
        self.requirement_name = requirement_name
        self.version_id = version_id


@router.delete("/index/requirement")
async def delete_index_by_requirement(
    project_id: int,
    requirement_name: str,
    version_id: Optional[int] = None
):
    """
    按需求名称删除向量数据
    
    Args:
        project_id: 项目ID
        requirement_name: 需求名称
        version_id: 版本ID（可选）
    
    Returns:
        删除结果
    """
    from app.rag import get_index_manager
    
    try:
        index_manager = await get_index_manager()
        deleted_count = await index_manager.delete_by_requirement(
            project_id=project_id,
            requirement_name=requirement_name,
            version_id=version_id
        )
        
        return {
            "success": True,
            "message": f"已删除 {deleted_count} 条需求向量数据",
            "deleted_count": deleted_count
        }
            
    except Exception as e:
        logger.error(f"按需求删除向量数据失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "deleted_count": 0
        }


@router.post("/search")
async def search_similar(
    project_id: int = Form(..., description="项目ID"),
    query: str = Form(..., description="查询文本"),
    version_id: Optional[int] = Form(None, description="版本ID，用于版本隔离"),
    top_k: int = Form(5, description="返回数量"),
    score_threshold: float = Form(0.7, description="相似度阈值")
):
    """
    搜索相似的需求文档片段
    
    Args:
        project_id: 项目ID
        query: 查询文本
        version_id: 版本ID（可选，用于版本隔离查询）
        top_k: 返回数量
        score_threshold: 相似度阈值
    
    Returns:
        相似文档片段列表
    """
    from app.rag import get_index_manager
    
    try:
        index_manager = await get_index_manager()
        results = await index_manager.search_for_testcase_generation(
            requirement=query,
            project_id=project_id,
            version_id=version_id,
            top_k=top_k,
            score_threshold=score_threshold
        )
        
        return {
            "success": True,
            "count": len(results),
            "data": results
        }
        
    except Exception as e:
        logger.error(f"搜索失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "count": 0,
            "data": []
        }
