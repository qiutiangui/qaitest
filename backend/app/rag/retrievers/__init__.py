"""
高级检索器模块
提供混合检索、重排序等高级检索策略
"""
from typing import List, Dict, Any, Optional
from loguru import logger

# LlamaIndex 核心类型
from llama_index.core import VectorStoreIndex, QueryBundle
from llama_index.core.retrievers import BaseRetriever, VectorIndexRetriever
from llama_index.core.schema import NodeWithScore, QueryBundle

# BM25 检索器（可选）
try:
    from llama_index.retrievers.bm25 import BM25Retriever
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False
    logger.warning("BM25Retriever 不可用，混合检索功能受限")


class HybridRetriever(BaseRetriever):
    """混合检索器：向量检索 + BM25 关键词检索"""
    
    def __init__(
        self,
        vector_retriever: VectorIndexRetriever,
        bm25_retriever: Optional[Any] = None,
        mode: str = "reciprocal_rerank",
        top_k: int = 10
    ):
        """
        Args:
            vector_retriever: 向量检索器
            bm25_retriever: BM25 检索器（可选）
            mode: 融合模式 (reciprocal_rerank, simple, dot_product)
            top_k: 返回结果数量
        """
        self._vector_retriever = vector_retriever
        self._bm25_retriever = bm25_retriever
        self._mode = mode
        self._top_k = top_k
    
    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        """执行混合检索并合并结果"""
        # 向量检索
        vector_nodes = self._vector_retriever.retrieve(query_bundle)
        
        # BM25 检索（如果可用）
        bm25_nodes = []
        if self._bm25_retriever and BM25_AVAILABLE:
            try:
                bm25_nodes = self._bm25_retriever.retrieve(query_bundle)
            except Exception as e:
                logger.warning(f"BM25 检索失败: {e}")
        
        # 合并结果
        if not bm25_nodes:
            return vector_nodes[:self._top_k]
        
        # 根据 mode 融合结果
        if self._mode == "reciprocal_rerank":
            return self._reciprocal_rerank(vector_nodes, bm25_nodes)
        elif self._mode == "simple":
            return self._simple_fusion(vector_nodes, bm25_nodes)
        else:
            return self._simple_fusion(vector_nodes, bm25_nodes)
    
    def _reciprocal_rerank(
        self,
        vector_nodes: List[NodeWithScore],
        bm25_nodes: List[NodeWithScore],
        k: int = 60
    ) -> List[NodeWithScore]:
        """倒数重排序融合
        
        参考: Reciprocal Rank Fusion (RRF)
        """
        # 构建分数字典
        scores_dict: Dict[str, float] = {}
        nodes_dict: Dict[str, NodeWithScore] = {}
        
        # 向量检索结果
        for i, node in enumerate(vector_nodes):
            node_id = node.node.node_id
            scores_dict[node_id] = 1.0 / (i + k)
            nodes_dict[node_id] = node
        
        # BM25 检索结果
        for i, node in enumerate(bm25_nodes):
            node_id = node.node.node_id
            if node_id in scores_dict:
                scores_dict[node_id] += 1.0 / (i + k)
            else:
                scores_dict[node_id] = 1.0 / (i + k)
                nodes_dict[node_id] = node
        
        # 按分数排序
        sorted_ids = sorted(scores_dict.items(), key=lambda x: x[1], reverse=True)
        
        # 构建结果列表
        results = []
        for node_id, score in sorted_ids[:self._top_k]:
            node_with_score = nodes_dict[node_id]
            # 更新分数
            node_with_score.score = score
            results.append(node_with_score)
        
        return results
    
    def _simple_fusion(
        self,
        vector_nodes: List[NodeWithScore],
        bm25_nodes: List[NodeWithScore]
    ) -> List[NodeWithScore]:
        """简单融合：去重后返回"""
        seen_ids = set()
        results = []
        
        # 添加向量检索结果
        for node in vector_nodes:
            if node.node.node_id not in seen_ids:
                seen_ids.add(node.node.node_id)
                results.append(node)
        
        # 添加 BM25 检索结果
        for node in bm25_nodes:
            if node.node.node_id not in seen_ids:
                seen_ids.add(node.node.node_id)
                results.append(node)
        
        return results[:self._top_k]


class QueryEnhancer:
    """查询增强器：使用多种策略改进查询"""
    
    @staticmethod
    def expand_query(query: str, keywords: List[str] = None) -> str:
        """查询扩展
        
        Args:
            query: 原始查询
            keywords: 关键词列表（可选）
        
        Returns:
            扩展后的查询
        """
        if not keywords:
            return query
        
        # 添加关键词到查询
        expanded = f"{query} {' '.join(keywords)}"
        return expanded.strip()
    
    @staticmethod
    def extract_keywords(query: str) -> List[str]:
        """从查询中提取关键词
        
        Args:
            query: 查询文本
        
        Returns:
            关键词列表
        """
        # 简单的关键词提取：移除停用词、标点等
        import re
        
        # 移除标点
        query = re.sub(r'[^\w\s]', ' ', query)
        
        # 分词
        words = query.split()
        
        # 移除短词和数字
        keywords = [w for w in words if len(w) > 2 and not w.isdigit()]
        
        return keywords


class RetrievalResultProcessor:
    """检索结果处理器"""
    
    @staticmethod
    def filter_by_score(
        nodes: List[NodeWithScore],
        min_score: float = 0.7
    ) -> List[NodeWithScore]:
        """按分数过滤结果"""
        return [node for node in nodes if node.score and node.score >= min_score]
    
    @staticmethod
    def deduplicate(nodes: List[NodeWithScore]) -> List[NodeWithScore]:
        """去重"""
        seen_ids = set()
        results = []
        
        for node in nodes:
            if node.node.node_id not in seen_ids:
                seen_ids.add(node.node.node_id)
                results.append(node)
        
        return results
    
    @staticmethod
    def format_results(
        nodes: List[NodeWithScore],
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """格式化检索结果
        
        Args:
            nodes: 检索结果节点
            include_metadata: 是否包含元数据
        
        Returns:
            格式化后的结果列表
        """
        results = []
        
        for node in nodes:
            result = {
                "content": node.node.text,
                "score": node.score if node.score else 0.0
            }
            
            if include_metadata:
                result["metadata"] = node.node.metadata
            
            results.append(result)
        
        return results


# 导出检索器
__all__ = [
    'HybridRetriever',
    'QueryEnhancer',
    'RetrievalResultProcessor'
]
