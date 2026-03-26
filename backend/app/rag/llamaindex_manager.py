"""
LlamaIndex 索引管理器 - 基于 LlamaIndex 0.14.18 的 RAG 实现
保持与现有 IndexManager 相同的接口，提供更强大的文档解析和检索能力
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
from loguru import logger

# LlamaIndex 核心
from llama_index.core import VectorStoreIndex, Document, Settings as LlamaSettings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.storage.storage_context import StorageContext
from llama_index.core.vector_stores.types import VectorStoreQuery, MetadataFilters, MetadataFilter

# LlamaIndex 嵌入模型（使用 OpenAI 兼容接口）
from llama_index.embeddings.openai import OpenAIEmbedding

from app.config import settings
from app.rag.llama_embeddings import QwenEmbeddingModel, MockEmbeddingModel

# 延迟导入 Milvus，避免启动时的版本兼容问题
# from llama_index.vector_stores.milvus import MilvusVectorStore


class LlamaIndexIndexManager:
    """基于 LlamaIndex 0.14.18 的索引管理器"""
    
    def __init__(self):
        self._initialized = False
        self._indices: Dict[str, VectorStoreIndex] = {}  # 缓存索引
        self._vector_stores: Dict[str, MilvusVectorStore] = {}  # 缓存向量存储
        self._embedding_model = None
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """初始化索引管理器"""
        if self._initialized:
            return

        async with self._lock:
            if self._initialized:
                return

            try:
                # 配置 LlamaIndex 全局设置（异步）
                await self._setup_llamaindex_settings()

                logger.info("LlamaIndex 索引管理器初始化完成")
                self._initialized = True

            except Exception as e:
                logger.error(f"LlamaIndex 初始化失败: {e}")
                raise
    
    async def _setup_llamaindex_settings(self) -> None:
        """配置 LlamaIndex 全局设置 - 从数据库读取嵌入模型配置"""
        from app.rag.llama_embeddings import OllamaEmbeddingModel
        
        # 尝试从数据库获取嵌入模型配置
        try:
            from app.services.embedding_model_service import EmbeddingModelService
            
            config = await EmbeddingModelService.get_default_config()
            if config:
                logger.info(f"从数据库获取到嵌入模型配置: name={config.name}, provider={config.provider}, api_key={'已设置' if config.api_key else '未设置'}, model={config.model_name}")
                # 根据 provider 选择正确的嵌入模型类
                if config.provider == "ollama":
                    self._embedding_model = OllamaEmbeddingModel(
                        model_name=config.model_name,
                        api_base=config.api_base,
                        embed_batch_size=settings.llamaindex_embed_batch_size,
                        dimension=config.dimension
                    )
                elif config.api_key:
                    # DashScope / OpenAI 等需要 API Key
                    self._embedding_model = QwenEmbeddingModel(
                        api_key=config.api_key,
                        model_name=config.model_name,
                        api_base=config.api_base,
                        embed_batch_size=settings.llamaindex_embed_batch_size,
                        dimension=config.dimension
                    )
                else:
                    # 有配置但没有 API Key，跳过，使用其他方式
                    raise ValueError(f"Provider {config.provider} requires API key")
                
                logger.info(f"使用数据库配置的嵌入模型: {config.display_name} ({config.model_name}, provider={config.provider}, dimension={config.dimension})")
                self._initialized = True
                return
        except Exception as e:
            logger.warning(f"从数据库获取嵌入模型配置失败: {e}")

        # 回退到环境变量配置（向后兼容）
        if settings.dashscope_api_key:
            self._embedding_model = QwenEmbeddingModel(
                api_key=settings.dashscope_api_key,
                model_name="text-embedding-v3",
                api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
                embed_batch_size=settings.llamaindex_embed_batch_size,
                dimension=1024
            )
            logger.info("使用环境变量配置的嵌入模型 (text-embedding-v3, dimension=1024)")
        else:
            # 使用模拟嵌入模型（仅用于测试）
            logger.warning("未配置嵌入模型，使用模拟嵌入模型")
            self._embedding_model = MockEmbeddingModel(dimension=1024)

        # 配置全局分块器
        self._text_splitter = SentenceSplitter(
            chunk_size=settings.llamaindex_chunk_size,
            chunk_overlap=settings.llamaindex_chunk_overlap
        )
    
    def _get_collection_name(
        self, 
        project_id: Optional[int], 
        version_id: Optional[int] = None,
        task_id: Optional[str] = None
    ) -> str:
        """
        获取集合名称
        
        优先级：
        1. project_id + version_id: project_{project_id}_v{version_id}
        2. project_id: project_{project_id}
        3. task_id: task_{task_id}
        4. 默认: global
        """
        if project_id and project_id > 0:
            if version_id:
                return f"project_{project_id}_v{version_id}"
            return f"project_{project_id}"
        elif task_id:
            return f"task_{task_id}"
        else:
            return "global"
    
    async def _get_or_create_vector_store(
        self,
        collection_name: str
    ):
        """获取或创建向量存储"""
        # 延迟导入 Milvus，避免启动时的版本兼容问题
        from llama_index.vector_stores.milvus import MilvusVectorStore
        
        if collection_name in self._vector_stores:
            return self._vector_stores[collection_name]
        
        # 创建 Milvus 向量存储（增加超时配置）
        vector_store = MilvusVectorStore(
            uri=f"http://{settings.milvus_host}:{settings.milvus_port}",
            collection_name=collection_name,
            dim=1024,  # Qwen text-embedding-v3 的维度
            overwrite=False,  # 重新创建集合以使用正确的 schema
            enable_dynamic_field=True,  # 启用动态字段
            # 增加超时和重试配置（Milvus 2.4+ 支持）
            timeout=30,  # 增加超时到30秒
        )
        
        self._vector_stores[collection_name] = vector_store
        logger.info(f"创建向量存储: {collection_name}")
        
        return vector_store
    
    async def _get_or_create_index(
        self,
        collection_name: str
    ) -> VectorStoreIndex:
        """获取或创建索引"""
        if collection_name in self._indices:
            return self._indices[collection_name]
        
        # 获取向量存储
        vector_store = await self._get_or_create_vector_store(collection_name)
        
        # 创建存储上下文
        storage_context = StorageContext.from_defaults(
            vector_store=vector_store
        )
        
        # 创建或加载索引
        index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
            storage_context=storage_context,
            embed_model=self._embedding_model
        )
        
        self._indices[collection_name] = index
        logger.info(f"创建索引: {collection_name}")
        
        return index
    
    async def index_requirement_document(
        self,
        project_id: Optional[int],
        content: str,
        filename: str,
        version_id: Optional[int] = None,
        requirement_name: Optional[str] = None,
        task_id: Optional[str] = None,  # 新增：任务ID作为备用标识
        chunk_size: int = 500,
        overlap: int = 100
    ) -> Dict[str, Any]:
        """
        索引需求文档（支持无项目情况）
        
        Args:
            project_id: 项目ID（可选，如果为None则使用task_id）
            content: 文档内容
            filename: 文件名
            version_id: 版本ID
            requirement_name: 需求名称
            chunk_size: 分块大小
            overlap: 重叠大小
        
        Returns:
            索引结果
        """
        if not self._initialized:
            await self.initialize()
        
        if not content or not content.strip():
            return {
                "success": False,
                "error": "文档内容为空",
                "indexed": 0
            }
        
        collection_name = self._get_collection_name(project_id, version_id, task_id)
        
        try:
            # 创建文档对象
            document = Document(
                text=content,
                metadata={
                    "project_id": project_id,
                    "version_id": version_id,
                    "requirement_name": requirement_name,
                    "source": "requirement_document",
                    "filename": filename,
                    "created_at": datetime.now().isoformat()
                }
            )
            
            # 使用自定义分块器
            # 如果内容太短，使用更小的 chunk_size 确保至少产生 1 个切片
            effective_chunk_size = min(chunk_size, max(50, len(content) // 2 + 1))
            text_splitter = SentenceSplitter(
                chunk_size=effective_chunk_size,
                chunk_overlap=overlap
            )
            
            logger.info(f"[RAG索引] 开始分块, 原始内容长度={len(content)}, 有效chunk_size={effective_chunk_size}, overlap={overlap}")
            
            # 获取或创建索引
            index = await self._get_or_create_index(collection_name)
            
            # 分块并添加节点
            nodes = text_splitter.get_nodes_from_documents([document])
            
            # 如果分块结果为空（内容太短），创建一个包含全部内容的节点
            if not nodes:
                logger.warning(f"[RAG索引] 分块结果为空，为内容创建单个节点")
                from llama_index.core.schema import TextNode
                node = TextNode(
                    text=content,
                    metadata=document.metadata
                )
                nodes = [node]
            
            logger.info(f"[RAG索引] 分块完成, 生成 {len(nodes)} 个节点")
            
            # 为每个节点添加额外元数据
            for i, node in enumerate(nodes):
                node.metadata["chunk_index"] = i
                node.metadata["chapter"] = self._extract_chapter(node.text)
            
            # 添加到索引
            index.insert_nodes(nodes)
            
            logger.info(f"[RAG索引] 已索引 {len(nodes)} 个文档块到集合 {collection_name}")
            
            return {
                "success": True,
                "indexed": len(nodes),
                "collection": collection_name,
                "chunks": len(nodes),
                "filename": filename
            }
            
        except Exception as e:
            logger.error(f"索引需求文档失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "indexed": 0
            }
    
    def _extract_chapter(self, text: str) -> str:
        """从文本中提取章节信息"""
        lines = text.strip().split("\n")
        for line in lines[:5]:  # 检查前5行
            line = line.strip()
            # 匹配章节标题（如 "## 1. 简介", "# 第一章", "1.1 概述" 等）
            if line.startswith("#") or (line and line[0].isdigit() and "." in line[:5]):
                return line[:50]  # 返回前50个字符
        return ""
    
    async def search_for_testcase_generation(
        self,
        requirement: str,
        project_id: Optional[int],
        version_id: Optional[int] = None,
        task_id: Optional[str] = None,  # 新增：任务ID作为备用标识
        top_k: int = 5,
        score_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        为测试用例生成检索相关内容（支持无项目情况）
        
        Args:
            requirement: 功能点描述
            project_id: 项目ID（可选）
            version_id: 版本ID（可选，用于版本隔离）
            task_id: 任务ID（当project_id为None时使用）
            top_k: 返回数量
            score_threshold: 相似度阈值
        
        Returns:
            相关需求片段列表
        """
        if not self._initialized:
            await self.initialize()
        
        collection_name = self._get_collection_name(project_id, version_id, task_id)
        
        try:
            # 获取索引
            index = await self._get_or_create_index(collection_name)
            
            # 构建元数据过滤器
            filters = MetadataFilters(
                filters=[
                    MetadataFilter(key="source", value="requirement_document")
                ]
            )
            
            if version_id is not None:
                filters.filters.append(
                    MetadataFilter(key="version_id", value=version_id)
                )
            
            # 创建检索器
            retriever = index.as_retriever(
                similarity_top_k=top_k,
                filters=filters
            )
            
            # 执行检索
            nodes = retriever.retrieve(requirement)
            
            # 过滤低分结果
            results = []
            for node in nodes:
                score = node.score if node.score is not None else 0.0
                
                if score >= score_threshold:
                    results.append({
                        "content": node.node.text,
                        "chapter": node.node.metadata.get("chapter", ""),
                        "filename": node.node.metadata.get("filename", ""),
                        "score": score
                    })
            
            logger.info(f"检索到 {len(results)} 条相关内容 (threshold={score_threshold})")
            
            return results
            
        except Exception as e:
            logger.error(f"检索失败: {e}")
            return []
    
    async def delete_by_requirement(
        self,
        project_id: int,
        requirement_name: str,
        version_id: Optional[int] = None
    ) -> int:
        """
        按需求名称删除向量数据
        
        Args:
            project_id: 项目ID
            requirement_name: 需求名称
            version_id: 版本ID（可选，用于精确匹配）
        
        Returns:
            删除的记录数
        """
        if not self._initialized:
            await self.initialize()
        
        collection_name = self._get_collection_name(project_id, version_id)
        
        try:
            # 注意：LlamaIndex 的 MilvusVectorStore 不支持直接按元数据删除
            # 需要使用底层的 Milvus 客户端
            from pymilvus import MilvusClient
            
            client = MilvusClient(
                uri=f"http://{settings.milvus_host}:{settings.milvus_port}"
            )
            
            # 检查集合是否存在
            collections = client.list_collections()
            if collection_name not in collections:
                logger.warning(f"集合 {collection_name} 不存在")
                return 0
            
            # 构建过滤表达式
            filter_expr = f'requirement_name == "{requirement_name}"'
            if version_id is not None:
                filter_expr += f' and version_id == {version_id}'
            
            # 查询符合条件的记录
            results = client.query(
                collection_name=collection_name,
                filter=filter_expr,
                output_fields=["id"]
            )
            
            if not results:
                return 0
            
            # 删除记录
            ids_to_delete = [r.get("id") for r in results if r.get("id")]
            
            if ids_to_delete:
                client.delete(
                    collection_name=collection_name,
                    ids=ids_to_delete
                )
                logger.info(f"已删除 {len(ids_to_delete)} 条需求向量数据")
            
            return len(ids_to_delete)
            
        except Exception as e:
            logger.error(f"按需求删除向量数据失败: {e}")
            return 0
    
    async def delete_project_index(self, project_id: int) -> bool:
        """删除项目的向量索引"""
        collection_name = self._get_collection_name(project_id)
        
        if not self._initialized:
            await self.initialize()
        
        try:
            from pymilvus import MilvusClient
            
            client = MilvusClient(
                uri=f"http://{settings.milvus_host}:{settings.milvus_port}",
                timeout=30,  # 增加超时到30秒
            )
            
            # 删除集合
            client.drop_collection(collection_name)
            
            # 清理缓存
            self._indices.pop(collection_name, None)
            self._vector_stores.pop(collection_name, None)
            
            logger.info(f"已删除项目向量索引: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"删除项目索引失败: {e}")
            return False
    
    async def get_project_index_stats(self, project_id: int) -> Dict[str, Any]:
        """获取项目索引统计信息"""
        collection_name = self._get_collection_name(project_id)
        
        if not self._initialized:
            await self.initialize()
        
        try:
            from pymilvus import MilvusClient
            
            client = MilvusClient(
                uri=f"http://{settings.milvus_host}:{settings.milvus_port}"
            )
            
            # 检查集合是否存在
            collections = client.list_collections()
            if collection_name not in collections:
                return {"exists": False, "count": 0}
            
            # 获取统计信息
            stats = client.get_collection_stats(collection_name)
            
            return {
                "exists": True,
                "collection": collection_name,
                "count": stats.get("row_count", 0)
            }
            
        except Exception as e:
            logger.error(f"获取索引统计失败: {e}")
            return {"exists": False, "count": 0, "error": str(e)}


# 全局单例
_llamaindex_manager: Optional[LlamaIndexIndexManager] = None
_manager_lock = asyncio.Lock()


async def get_index_manager() -> LlamaIndexIndexManager:
    """获取全局索引管理器实例（保持接口不变）"""
    global _llamaindex_manager
    
    if _llamaindex_manager is None:
        async with _manager_lock:
            if _llamaindex_manager is None:
                _llamaindex_manager = LlamaIndexIndexManager()
                await _llamaindex_manager.initialize()
    
    return _llamaindex_manager
