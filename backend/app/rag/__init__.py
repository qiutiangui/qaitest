"""
RAG 模块 - 基于 LlamaIndex 0.14.18

提供向量检索、文档索引等功能
"""
from app.rag.llamaindex_manager import get_index_manager, LlamaIndexIndexManager

__all__ = ['get_index_manager', 'LlamaIndexIndexManager']
