"""
LlamaIndex 嵌入模型适配器
支持 DashScope/Qwen 嵌入模型、Ollama 本地嵌入模型与 LlamaIndex 集成
"""
from typing import List, Optional
import asyncio
from loguru import logger

# LlamaIndex 核心类型
from llama_index.core.embeddings import BaseEmbedding

# OpenAI 兼容客户端
import httpx


class QwenEmbeddingModel(BaseEmbedding):
    """Qwen 嵌入模型适配器 - 通过 OpenAI 兼容接口调用"""
    
    def __init__(
        self,
        api_key: str,
        model_name: str = "text-embedding-v3",
        api_base: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
        embed_batch_size: int = 10,
        dimension: int = 1024
    ):
        super().__init__(
            embed_batch_size=embed_batch_size
        )
        self._api_key = api_key
        self._model_name = model_name
        self._api_base = api_base
        self._dimension = dimension
        self._provider = "dashscope"
        
        logger.info(f"初始化 Qwen 嵌入模型: {model_name}, 维度: {dimension}")
    
    @classmethod
    def class_name(cls) -> str:
        return "QwenEmbeddingModel"
    
    async def _aget_query_embedding(self, query: str) -> List[float]:
        """异步获取查询嵌入"""
        return await self._get_embedding(query)
    
    async def _aget_text_embedding(self, text: str) -> List[float]:
        """异步获取文本嵌入"""
        return await self._get_embedding(text)
    
    async def _aget_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """异步批量获取文本嵌入"""
        embeddings = []
        for text in texts:
            embedding = await self._get_embedding(text)
            embeddings.append(embedding)
        return embeddings
    
    def _get_query_embedding(self, query: str) -> List[float]:
        """同步获取查询嵌入"""
        try:
            loop = asyncio.get_running_loop()
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self._aget_query_embedding(query))
                return future.result()
        except RuntimeError:
            return asyncio.run(self._aget_query_embedding(query))
    
    def _get_text_embedding(self, text: str) -> List[float]:
        """同步获取文本嵌入"""
        try:
            loop = asyncio.get_running_loop()
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self._aget_text_embedding(text))
                return future.result()
        except RuntimeError:
            return asyncio.run(self._aget_text_embedding(text))
    
    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """同步批量获取文本嵌入"""
        try:
            loop = asyncio.get_running_loop()
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self._aget_text_embeddings(texts))
                return future.result()
        except RuntimeError:
            return asyncio.run(self._aget_text_embeddings(texts))
    
    async def _get_embedding(self, text: str) -> List[float]:
        """调用 API 获取嵌入向量"""
        
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }
        
        # 根据 provider 选择不同的 API 格式
        if self._provider == "ollama":
            # Ollama API 格式
            url = f"{self._api_base}/api/embeddings"
            data = {
                "model": self._model_name,
                "prompt": text,
            }
        else:
            # OpenAI/DashScope API 格式
            url = f"{self._api_base}/embeddings"
            data = {
                "model": self._model_name,
                "input": text,
                "encoding_format": "float"
            }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, headers=headers, json=data)
                response.raise_for_status()
                
                result = response.json()
                
                # 解析不同格式的响应
                if self._provider == "ollama":
                    embedding = result["embedding"]
                else:
                    embedding = result["data"][0]["embedding"]
                
                return embedding
                
        except Exception as e:
            logger.error(f"获取嵌入向量失败: {e}")
            raise
    
    @property
    def dimension(self) -> int:
        """返回嵌入向量维度"""
        return self._dimension


class OllamaEmbeddingModel(BaseEmbedding):
    """Ollama 本地嵌入模型适配器"""
    
    def __init__(
        self,
        model_name: str = "nomic-embed-text",
        api_base: str = "http://localhost:11434",
        embed_batch_size: int = 10,
        dimension: int = 768
    ):
        super().__init__(
            embed_batch_size=embed_batch_size
        )
        self._model_name = model_name
        self._api_base = api_base
        self._dimension = dimension
        
        logger.info(f"初始化 Ollama 嵌入模型: {model_name}, 维度: {dimension}")
    
    @classmethod
    def class_name(cls) -> str:
        return "OllamaEmbeddingModel"
    
    async def _aget_query_embedding(self, query: str) -> List[float]:
        """异步获取查询嵌入"""
        return await self._get_embedding(query)
    
    async def _aget_text_embedding(self, text: str) -> List[float]:
        """异步获取文本嵌入"""
        return await self._get_embedding(text)
    
    async def _aget_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """异步批量获取文本嵌入"""
        embeddings = []
        for text in texts:
            embedding = await self._get_embedding(text)
            embeddings.append(embedding)
        return embeddings
    
    def _get_query_embedding(self, query: str) -> List[float]:
        try:
            loop = asyncio.get_running_loop()
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self._aget_query_embedding(query))
                return future.result()
        except RuntimeError:
            return asyncio.run(self._aget_query_embedding(query))
    
    def _get_text_embedding(self, text: str) -> List[float]:
        try:
            loop = asyncio.get_running_loop()
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self._aget_text_embedding(text))
                return future.result()
        except RuntimeError:
            return asyncio.run(self._aget_text_embedding(text))
    
    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        try:
            loop = asyncio.get_running_loop()
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self._aget_text_embeddings(texts))
                return future.result()
        except RuntimeError:
            return asyncio.run(self._aget_text_embeddings(texts))
    
    async def _get_embedding(self, text: str) -> List[float]:
        """调用 Ollama API 获取嵌入向量"""
        url = f"{self._api_base}/api/embeddings"
        
        data = {
            "model": self._model_name,
            "prompt": text,
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=data)
                response.raise_for_status()
                
                result = response.json()
                return result["embedding"]
                
        except Exception as e:
            logger.error(f"获取 Ollama 嵌入向量失败: {e}")
            raise
    
    @property
    def dimension(self) -> int:
        return self._dimension


class MockEmbeddingModel(BaseEmbedding):
    """模拟嵌入模型 - 用于测试（不需要真实 API 调用）"""
    
    def __init__(self, dimension: int = 1024):
        super().__init__()
        self._dimension = dimension
        logger.warning("使用模拟嵌入模型（仅用于测试）")
    
    @classmethod
    def class_name(cls) -> str:
        return "MockEmbeddingModel"
    
    def _get_query_embedding(self, query: str) -> List[float]:
        """同步获取查询嵌入"""
        return self._generate_mock_embedding(query)
    
    def _get_text_embedding(self, text: str) -> List[float]:
        """同步获取文本嵌入"""
        return self._generate_mock_embedding(text)
    
    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """同步批量获取文本嵌入"""
        return [self._generate_mock_embedding(text) for text in texts]
    
    async def _aget_query_embedding(self, query: str) -> List[float]:
        """异步获取查询嵌入"""
        return self._generate_mock_embedding(query)
    
    async def _aget_text_embedding(self, text: str) -> List[float]:
        """异步获取文本嵌入"""
        return self._generate_mock_embedding(text)
    
    async def _aget_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """异步批量获取文本嵌入"""
        return [self._generate_mock_embedding(text) for text in texts]
    
    def _generate_mock_embedding(self, text: str) -> List[float]:
        """生成模拟嵌入向量"""
        import hashlib
        import random
        
        # 使用哈希生成伪随机向量（仅用于测试）
        hash_obj = hashlib.md5(text.encode())
        hash_int = int(hash_obj.hexdigest(), 16)
        
        random.seed(hash_int)
        return [random.gauss(0, 1) for _ in range(self._dimension)]
    
    @property
    def dimension(self) -> int:
        return self._dimension


# 导出
__all__ = ['QwenEmbeddingModel', 'OllamaEmbeddingModel', 'MockEmbeddingModel']
