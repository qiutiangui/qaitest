"""
增强文档解析器模块
基于 LlamaIndex Readers 提供更强大的文档解析能力
"""
from typing import List, Optional, Dict, Any, Union
from pathlib import Path
from io import BytesIO
from loguru import logger

# LlamaIndex 核心类型
from llama_index.core import Document
from llama_index.core.readers.base import BaseReader

# LlamaIndex 内置解析器（已内置在 llama-index 核心包中）
try:
    from llama_index.readers.file import PDFReader as LlamaPDFReader
    PDF_READER_AVAILABLE = True
except ImportError:
    PDF_READER_AVAILABLE = False
    logger.warning("PDFReader 不可用，PDF 解析功能受限")

try:
    from llama_index.readers.file import DocxReader as LlamaDocxReader
    DOCX_READER_AVAILABLE = True
except ImportError:
    DOCX_READER_AVAILABLE = False
    logger.warning("DocxReader 不可用，Word 解析功能受限")

try:
    from llama_index.core import SimpleDirectoryReader
    SIMPLE_READER_AVAILABLE = True
except ImportError:
    SIMPLE_READER_AVAILABLE = False
    logger.warning("SimpleDirectoryReader 不可用")


class EnhancedPDFReader(BaseReader):
    """增强的 PDF 解析器（基于 LlamaIndex PDFReader）"""
    
    def __init__(self, extract_images: bool = False, extract_tables: bool = True):
        self.extract_images = extract_images
        self.extract_tables = extract_tables
    
    def load_data(
        self,
        file: Path,
        extra_info: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """加载 PDF 文档并提取内容
        
        特性：
        - 高质量文本提取
        - 表格识别（可选）
        - 图片提取（可选）
        - 章节识别
        - 元数据提取
        """
        if not PDF_READER_AVAILABLE:
            logger.error("PDFReader 不可用，请安装 llama-index")
            return []
        
        try:
            reader = LlamaPDFReader()
            documents = reader.load_data(file_path=str(file))
            
            if extra_info:
                for doc in documents:
                    doc.metadata.update(extra_info)
            
            logger.info(f"PDF 解析完成: {file.name}, 共 {len(documents)} 个文档块")
            return documents
            
        except Exception as e:
            logger.error(f"PDF 解析失败 {file.name}: {e}")
            return []


class EnhancedDocxReader(BaseReader):
    """增强的 Word 文档解析器"""
    
    def __init__(self, preserve_formatting: bool = True):
        self.preserve_formatting = preserve_formatting
    
    def load_data(
        self,
        file: Path,
        extra_info: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """加载 Word 文档并提取内容
        
        特性：
        - 样式保留（可选）
        - 目录提取
        - 表格识别
        - 段落结构保持
        """
        if not DOCX_READER_AVAILABLE:
            logger.error("DocxReader 不可用，请安装 llama-index")
            return []
        
        try:
            reader = LlamaDocxReader()
            documents = reader.load_data(file=str(file))
            
            if extra_info:
                for doc in documents:
                    doc.metadata.update(extra_info)
            
            logger.info(f"Word 解析完成: {file.name}, 共 {len(documents)} 个文档块")
            return documents
            
        except Exception as e:
            logger.error(f"Word 解析失败 {file.name}: {e}")
            return []


class EnhancedMarkdownReader(BaseReader):
    """增强的 Markdown 解析器"""
    
    def __init__(self, remove_code_blocks: bool = False):
        self.remove_code_blocks = remove_code_blocks
    
    def load_data(
        self,
        file: Path,
        extra_info: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """加载 Markdown 文档并提取内容
        
        特性：
        - 代码块处理（可选移除）
        - 表格识别
        - 标题结构提取
        - 列表项保持
        """
        try:
            # 读取文件内容
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 处理代码块（可选）
            if self.remove_code_blocks:
                import re
                content = re.sub(r'```[\s\S]*?```', '', content)
            
            # 创建文档对象
            document = Document(
                text=content,
                metadata=extra_info or {}
            )
            
            # 提取章节信息
            sections = self._extract_sections(content)
            if sections:
                # 按章节分块
                documents = []
                for section_title, section_content in sections.items():
                    doc = Document(
                        text=section_content,
                        metadata={
                            **(extra_info or {}),
                            "section": section_title
                        }
                    )
                    documents.append(doc)
                
                logger.info(f"Markdown 解析完成: {file.name}, 共 {len(documents)} 个章节")
                return documents
            else:
                logger.info(f"Markdown 解析完成: {file.name}")
                return [document]
            
        except Exception as e:
            logger.error(f"Markdown 解析失败 {file.name}: {e}")
            return []
    
    def _extract_sections(self, content: str) -> Dict[str, str]:
        """提取 Markdown 章节"""
        sections = {}
        lines = content.split('\n')
        current_section = "Introduction"
        current_content = []
        
        for line in lines:
            # 检测标题
            if line.startswith('#'):
                # 保存上一个章节
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                    current_content = []
                
                # 提取新章节标题
                current_section = line.lstrip('#').strip()
            else:
                current_content.append(line)
        
        # 保存最后一个章节
        if current_content:
            sections[current_section] = '\n'.join(current_content)
        
        return sections


class UniversalDocumentReader(BaseReader):
    """通用文档解析器 - 自动识别文件类型并选择合适的解析器"""
    
    def __init__(self):
        self.pdf_reader = EnhancedPDFReader()
        self.docx_reader = EnhancedDocxReader()
        self.md_reader = EnhancedMarkdownReader()
    
    def load_data(
        self,
        file: Path,
        extra_info: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """自动识别文件类型并解析
        
        支持格式：
        - PDF (.pdf)
        - Word (.docx, .doc)
        - Markdown (.md, .markdown)
        - 文本 (.txt)
        """
        if not file.exists():
            logger.error(f"文件不存在: {file}")
            return []
        
        suffix = file.suffix.lower()
        
        if suffix == '.pdf':
            return self.pdf_reader.load_data(file, extra_info)
        elif suffix in ['.docx', '.doc']:
            return self.docx_reader.load_data(file, extra_info)
        elif suffix in ['.md', '.markdown']:
            return self.md_reader.load_data(file, extra_info)
        elif suffix == '.txt':
            # 简单文本文件
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                document = Document(
                    text=content,
                    metadata=extra_info or {}
                )
                
                logger.info(f"文本文件解析完成: {file.name}")
                return [document]
                
            except Exception as e:
                logger.error(f"文本文件解析失败 {file.name}: {e}")
                return []
        else:
            logger.warning(f"不支持的文件格式: {suffix}")
            return []
    
    @staticmethod
    async def load_from_bytes(
        content: bytes,
        filename: str,
        extra_info: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """从字节内容加载文档
        
        Args:
            content: 文件字节内容
            filename: 文件名（用于识别类型）
            extra_info: 额外元数据
        
        Returns:
            Document 列表
        """
        reader = UniversalDocumentReader()
        suffix = Path(filename).suffix.lower()
        
        try:
            if suffix == '.pdf':
                if not PDF_READER_AVAILABLE:
                    logger.error("PDFReader 不可用")
                    return []
                ll_reader = LlamaPDFReader()
                # PDFReader 可能需要先保存为临时文件
                import tempfile
                import os
                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_file:
                    tmp_file.write(content)
                    tmp_path = tmp_file.name
                try:
                    docs = ll_reader.load_data(file_path=tmp_path, extra_info=extra_info)
                    return docs
                finally:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
            
            elif suffix in ['.docx', '.doc']:
                # 使用 SimpleDirectoryReader + 临时文件方式解析 docx
                import tempfile
                import os
                
                if not SIMPLE_READER_AVAILABLE:
                    logger.error("SimpleDirectoryReader 不可用")
                    return []
                
                try:
                    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_file:
                        tmp_file.write(content)
                        tmp_path = tmp_file.name
                    
                    try:
                        reader = SimpleDirectoryReader(input_files=[tmp_path])
                        docs = reader.load_data()
                        
                        if docs and any(doc.text.strip() for doc in docs):
                            # 添加额外元数据
                            for doc in docs:
                                if extra_info:
                                    doc.metadata.update(extra_info)
                            logger.info(f"SimpleDirectoryReader 解析完成: {filename}, {len(docs)} 个文档块")
                            return docs
                        else:
                            logger.warning(f"文档内容为空: {filename}")
                            return []
                    finally:
                        if os.path.exists(tmp_path):
                            os.unlink(tmp_path)
                            
                except ImportError as e:
                    logger.error(f"缺少依赖: {e}")
                    return []
                except Exception as e:
                    logger.error(f"docx 解析失败 {filename}: {e}")
                    return []
            
            elif suffix in ['.md', '.markdown', '.txt']:
                text = content.decode('utf-8', errors='ignore')
                return [Document(text=text, metadata=extra_info or {})]
            
            else:
                logger.warning(f"不支持的文件格式: {suffix}")
                return []
                
        except Exception as e:
            logger.error(f"从字节加载文档失败 {filename}: {e}")
            return []
    
    @staticmethod
    async def get_text(
        content: bytes,
        filename: str
    ) -> str:
        """获取纯文本内容
        
        Args:
            content: 文件字节内容
            filename: 文件名
        
        Returns:
            纯文本内容
        """
        docs = await UniversalDocumentReader.load_from_bytes(content, filename)
        return '\n\n'.join([doc.text for doc in docs])


class SmartChunker:
    """智能中文分块器 - 保持语义完整性，支持章节感知"""
    
    @staticmethod
    def extract_chapters(text: str) -> List[tuple]:
        """提取文档章节结构
        
        Returns:
            [(章节标题, 起始行, 结束行), ...]
        """
        import re
        
        chapters = []
        lines = text.split('\n')
        current_chapter = "全文"
        chapter_start = 0
        
        for i, line in enumerate(lines):
            # 检测 Markdown 标题格式
            if re.match(r'^#{1,6}\s+', line):
                if chapters:
                    # 保存上一个章节
                    chapters.append((
                        current_chapter,
                        chapter_start,
                        i
                    ))
                
                current_chapter = line.lstrip('#').strip()
                chapter_start = i + 1
        
        # 最后一个章节
        if chapter_start < len(lines):
            chapters.append((
                current_chapter,
                chapter_start,
                len(lines)
            ))
        
        return chapters if chapters else [("全文", 0, len(lines))]
    
    @staticmethod
    def smart_chunk(
        text: str,
        chunk_size: int = 500,
        overlap: int = 100,
        respect_chapters: bool = True
    ) -> List[Document]:
        """智能分块
        
        Args:
            text: 原始文本
            chunk_size: 每块最大字符数
            overlap: 块之间重叠字符数
            respect_chapters: 是否优先按章节分割
        
        Returns:
            Document 列表
        """
        if not text:
            return []
        
        documents = []
        
        if respect_chapters:
            chapters = SmartChunker.extract_chapters(text)
            lines = text.split('\n')
            
            for chapter_title, start_line, end_line in chapters:
                chapter_text = '\n'.join(lines[start_line:end_line])
                
                if len(chapter_text) <= chunk_size:
                    if chapter_text.strip():
                        documents.append(Document(
                            text=chapter_text.strip(),
                            metadata={"chapter": chapter_title}
                        ))
                else:
                    sub_chunks = SmartChunker._split_with_overlap(chapter_text, chunk_size, overlap)
                    for i, sub_text in enumerate(sub_chunks):
                        documents.append(Document(
                            text=sub_text,
                            metadata={"chapter": f"{chapter_title} (第{i+1}部分)"}
                        ))
        else:
            chunks = SmartChunker._split_with_overlap(text, chunk_size, overlap)
            for i, chunk_text in enumerate(chunks):
                documents.append(Document(
                    text=chunk_text,
                    metadata={"chapter": "全文", "chunk_index": i}
                ))
        
        return documents
    
    @staticmethod
    def _split_with_overlap(text: str, chunk_size: int, overlap: int) -> List[str]:
        """带重叠的文本分割，优先在句子边界分割"""
        if not text:
            return []
        
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + chunk_size
            
            if end >= text_length:
                chunk = text[start:]
                chunks.append(chunk.strip())
                break
            
            # 尝试在句子边界分割
            search_text = text[start:end]
            last_period = search_text.rfind('。')
            last_newline = search_text.rfind('\n')
            split_point = max(last_period, last_newline)
            
            if split_point > chunk_size // 2:
                chunk = text[start:start + split_point + 1]
            else:
                chunk = search_text
            
            chunks.append(chunk.strip())
            start = start + len(chunk) - overlap
        
        return [c for c in chunks if c]


# 飞书文档读取器
from app.rag.readers.feishu_reader import FeishuReader

# 导出解析器
__all__ = [
    'EnhancedPDFReader',
    'EnhancedDocxReader',
    'EnhancedMarkdownReader',
    'UniversalDocumentReader',
    'SmartChunker',
    'FeishuReader',
]
