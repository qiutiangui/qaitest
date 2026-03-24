"""
飞书文档读取器
支持从飞书云文档和知识库获取内容并转换为 LlamaIndex Document
"""
from typing import List, Optional, Dict, Any
from loguru import logger
import httpx
import re

from llama_index.core import Document


class FeishuReader:
    """飞书云文档/知识库读取器"""

    def __init__(
        self,
        app_id: str,
        app_secret: str,
        timeout: int = 60
    ):
        self._app_id = app_id
        self._app_secret = app_secret
        self._timeout = timeout
        self._tenant_access_token: Optional[str] = None

    @property
    def base_url(self) -> str:
        return "https://open.feishu.cn/open-apis"

    async def _get_access_token(self) -> str:
        """获取 tenant_access_token"""
        if self._tenant_access_token:
            return self._tenant_access_token

        url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
        data = {"app_id": self._app_id, "app_secret": self._app_secret}

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(url, json=data)
            response.raise_for_status()

            result = response.json()
            if result.get("code") != 0:
                raise ValueError(f"获取飞书 access_token 失败: {result}")

            self._tenant_access_token = result["tenant_access_token"]
            return self._tenant_access_token

    def _get_headers(self, token: str) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    async def _fetch_document(self, doc_id: str) -> Dict[str, Any]:
        """获取文档元信息"""
        token = await self._get_access_token()
        url = f"{self.base_url}/docx/v1/documents/{doc_id}"

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(url, headers=self._get_headers(token))
            response.raise_for_status()
            return response.json()

    async def _fetch_blocks(self, doc_id: str) -> List[Dict[str, Any]]:
        """获取文档所有块内容（包含子块）"""
        token = await self._get_access_token()
        all_blocks = []
        page_token = None

        while True:
            url = f"{self.base_url}/docx/v1/documents/{doc_id}/blocks"
            params = {"page_size": 500}
            if page_token:
                params["page_token"] = page_token

            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(
                    url,
                    headers=self._get_headers(token),
                    params=params
                )
                response.raise_for_status()

                result = response.json()
                if result.get("code") != 0:
                    raise ValueError(f"获取飞书文档块失败: {result}")

                items = result.get("data", {}).get("items", [])
                all_blocks.extend(items)

                has_more = result.get("data", {}).get("has_more", False)
                if not has_more:
                    break

                page_token = result.get("data", {}).get("page_token")

        return all_blocks

    def _extract_text_from_block(self, block: Dict[str, Any]) -> Optional[str]:
        """从块中提取文本"""
        block_type = block.get("block_type", 0)
        block_id = block.get("block_id", "")

        # 只处理文本相关类型
        text_types = {
            2,   # 文本
            3,   # 文本
            4,   # 文本
            5,   # 标题1
            6,   # 标题2
            7,   # 标题3
            8,   # 标题4
            9,   # 标题5
            10,  # 标题6
            12,  # 代码块
            13,  # 有序列表
            14,  # 无序列表
            17,  # 引用
            18,  # 分割线
            19,  # 代码块
            20,  # 代码块
            21,  # 代码块
        }

        if block_type not in text_types:
            return None

        texts_parts = []

        # 方式1：从 text 字段获取
        if "text" in block:
            elements = block["text"].get("elements", [])
            for elem in elements:
                if "text_run" in elem:
                    texts_parts.append(elem["text_run"].get("content", ""))

        # 方式2：如果没有 text 字段，尝试用 block_id 作为 key
        if not texts_parts and block_id in block:
            data = block.get(block_id, {})
            if isinstance(data, dict) and "elements" in data:
                for elem in data.get("elements", []):
                    if "text_run" in elem:
                        texts_parts.append(elem["text_run"].get("content", ""))

        # 方式3：尝试其他可能的字段
        if not texts_parts:
            for key in ["heading1", "heading2", "heading3", "heading4", "heading5", "heading6",
                        "code", "ordered", "bullet", "quote"]:
                if key in block:
                    data = block[key]
                    if isinstance(data, dict) and "elements" in data:
                        for elem in data.get("elements", []):
                            if "text_run" in elem:
                                texts_parts.append(elem["text_run"].get("content", ""))

        return "".join(texts_parts) if texts_parts else None

    def _parse_blocks(self, blocks: List[Dict[str, Any]]) -> str:
        """解析飞书块为纯文本"""
        texts = []

        for block in blocks:
            block_type = block.get("block_type", 0)
            text = self._extract_text_from_block(block)

            if text is None:
                continue

            # 根据块类型添加格式
            if block_type == 5:  # 标题1
                texts.append(f"# {text}")
            elif block_type == 6:  # 标题2
                texts.append(f"## {text}")
            elif block_type == 7:  # 标题3
                texts.append(f"### {text}")
            elif block_type in [8, 9, 10]:  # 标题4-6
                texts.append(f"#### {text}")
            elif block_type in [13]:  # 有序列表
                texts.append(f"1. {text}")
            elif block_type in [14]:  # 无序列表
                texts.append(f"- {text}")
            elif block_type in [12, 19, 20, 21]:  # 代码块
                lang = block.get(block.get("block_id", ""), {}).get("language", 0)
                texts.append(f"```{lang}\n{text}\n```")
            elif block_type == 17:  # 引用
                texts.append(f"> {text}")
            elif block_type == 18:  # 分割线
                texts.append("---")
            else:
                texts.append(text)

        return "\n\n".join(texts)

    async def load_data(
        self,
        doc_id: str,
        extra_info: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """加载飞书文档"""
        try:
            # 获取文档信息
            doc_info = await self._fetch_document(doc_id)
            doc_data = doc_info.get("data", {}).get("document", {})
            title = doc_data.get("title", "Untitled")

            logger.info(f"获取飞书文档: {title}")

            # 获取文档内容
            blocks = await self._fetch_blocks(doc_id)
            logger.info(f"获取到 {len(blocks)} 个块")

            # 解析为纯文本
            content = self._parse_blocks(blocks)

            if not content.strip():
                logger.warning(f"飞书文档 {doc_id} 内容为空")
                return []

            # 构建元数据
            metadata = {
                "source": "feishu",
                "doc_id": doc_id,
                "title": title,
                **(extra_info or {})
            }

            document = Document(text=content, metadata=metadata)
            logger.info(f"飞书文档解析完成: {title}, 长度: {len(content)}")

            return [document]

        except Exception as e:
            logger.error(f"加载飞书文档失败 {doc_id}: {e}")
            raise

    async def load_data_from_url(self, url: str, extra_info: Optional[Dict[str, Any]] = None) -> List[Document]:
        """
        从飞书文档 URL 加载

        支持格式:
        - https://xxx.feishu.cn/docx/xxxxx
        - https://xxx.feishu.cn/docs/xxxxx (旧版)
        - https://xxx.feishu.cn/wiki/xxxxx (知识库)
        - https://my.feishu.cn/wiki/xxxxx (知识库)
        """
        # 从 URL 提取文档 ID
        patterns = [
            r'/docx/([a-zA-Z0-9]+)',
            r'/docs/([a-zA-Z0-9]+)',
            r'/wiki/([a-zA-Z0-9]+)',  # 知识库文档
        ]

        doc_id = None
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                doc_id = match.group(1)
                break

        if not doc_id:
            raise ValueError(f"无法从 URL 中提取文档 ID: {url}")

        return await self.load_data(doc_id, extra_info)


# 导出
__all__ = ['FeishuReader']
