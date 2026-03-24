"""
Milvus Lite 服务器管理

提供轻量级Milvus服务器的启动和停止功能
"""
from loguru import logger
from typing import Optional
from pathlib import Path
import time
import shutil
import threading


class MilvusLiteServer:
    """Milvus Lite服务器管理器"""

    def __init__(self):
        self._server = None
        self._is_running = False
        self._start_thread: Optional[threading.Thread] = None

    def _cleanup_old_logs(self, max_age_days: int = 7):
        """清理过期日志文件"""
        try:
            logs_dir = Path.home() / ".milvus.io" / "milvus-server" / "2.3.9" / "logs"
            if not logs_dir.exists():
                return
            
            now = time.time()
            cleaned = 0
            total_size = 0
            
            for log_file in logs_dir.glob("standalone-*.log"):
                # 跳过当前使用的日志（最新的）
                if log_file.stat().st_mtime > now - 86400:  # 最近24小时内
                    continue
                age_days = (now - log_file.stat().st_mtime) / 86400
                if age_days > max_age_days:
                    size = log_file.stat().st_size
                    log_file.unlink()
                    cleaned += 1
                    total_size += size
            
            if cleaned > 0:
                logger.info(f"🧹 已清理 {cleaned} 个过期日志文件，释放 {total_size / 1024:.1f} KB")
                
        except Exception as e:
            logger.warning(f"⚠️ 清理日志失败: {e}")
    
    def _start_in_thread(self, port: int):
        """在后台线程中启动 Milvus Lite（避免阻塞主事件循环）"""
        try:
            from milvus import default_server
            default_server.listen_port = port
            default_server.config.set("cache_size", "1GB")
            default_server.start()
            self._server = default_server
            self._is_running = True
            logger.info(f"✅ Milvus Lite服务器已启动: localhost:{port}")
        except ImportError:
            logger.warning("⚠️ Milvus Lite未安装，请运行: pip install milvus")
        except Exception as e:
            logger.error(f"❌ 启动Milvus Lite失败: {e}")

    def start(self, port: int = 19530, cleanup_logs: bool = True) -> bool:
        """
        启动Milvus Lite服务器（后台线程执行，不阻塞）

        Args:
            port: 服务端口，默认19530

        Returns:
            是否成功启动后台线程（不代表Milvus就绪）
        """
        if self._is_running:
            logger.info(f"Milvus Lite已在运行: localhost:{port}")
            return True

        if cleanup_logs:
            self._cleanup_old_logs()

        self._start_thread = threading.Thread(
            target=self._start_in_thread,
            args=(port,),
            daemon=True,
            name="milvus-lite-starter"
        )
        self._start_thread.start()
        logger.info(f"🚀 Milvus Lite启动线程已启动: localhost:{port}")
        return True
    
    def stop(self) -> bool:
        """
        停止Milvus Lite服务器
        
        Returns:
            是否停止成功
        """
        try:
            if self._server and self._is_running:
                from milvus import default_server
                default_server.stop()
                self._is_running = False
                logger.info("🛑 Milvus Lite服务器已停止")
            return True
        except Exception as e:
            logger.error(f"❌ 停止Milvus Lite失败: {e}")
            return False
    
    @property
    def is_running(self) -> bool:
        """服务器是否正在运行"""
        return self._is_running
    
    def health_check(self, timeout: int = 5) -> bool:
        """
        检查 Milvus 是否可连接
        
        Args:
            timeout: 连接超时时间（秒）
            
        Returns:
            是否可连接
        """
        try:
            from pymilvus import connections
            connections.connect(
                alias="health_check",
                host=self.host,
                port=self.port,
                timeout=timeout
            )
            connections.disconnect("health_check")
            return True
        except Exception:
            return False
    
    @property
    def host(self) -> str:
        """服务器主机"""
        return "localhost"
    
    @property
    def port(self) -> int:
        """服务器端口"""
        if self._server:
            return self._server.listen_port
        return 19530


# 全局单例
_milvus_server: Optional[MilvusLiteServer] = None


def get_milvus_server() -> MilvusLiteServer:
    """获取Milvus服务器单例"""
    global _milvus_server
    if _milvus_server is None:
        _milvus_server = MilvusLiteServer()
    return _milvus_server


def start_milvus_lite(port: int = 19530) -> bool:
    """
    启动Milvus Lite服务器（便捷函数）
    
    Args:
        port: 服务端口
        
    Returns:
        是否启动成功
    """
    return get_milvus_server().start(port)


def stop_milvus_lite() -> bool:
    """
    停止Milvus Lite服务器（便捷函数）
    
    Returns:
        是否停止成功
    """
    return get_milvus_server().stop()
