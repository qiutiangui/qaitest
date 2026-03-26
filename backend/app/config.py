"""
应用配置模块
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # 忽略未知的环境变量
    )
    
    # 数据库配置
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "qaitest"
    
    # DeepSeek API配置 - 【已废弃】请通过界面配置模型，此配置仅用于向后兼容
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"

    # DashScope/Qwen API配置 - 【已废弃】请通过界面配置模型，此配置仅用于向后兼容
    dashscope_api_key: str = ""
    qwen_model: str = "qwen-plus"

    # Moonshot/Kimi API配置 - 【已废弃】请通过界面配置模型，此配置仅用于向后兼容
    moonshot_api_key: str = ""
    moonshot_base_url: str = "https://api.moonshot.cn/v1"
    moonshot_model: str = "moonshot-v1-32k"
    
    # Milvus配置
    milvus_host: str = "localhost"
    milvus_port: int = 19530
    milvus_collection: str = "qaitest_knowledge"
    
    # LlamaIndex RAG配置
    llamaindex_chunk_size: int = 500
    llamaindex_chunk_overlap: int = 100
    llamaindex_enable_reranker: bool = False
    llamaindex_reranker_model: str = "BAAI/bge-reranker-base"
    llamaindex_embed_batch_size: int = 10

    # 应用配置
    app_env: str = "development"
    app_debug: bool = True
    app_port: int = 8000
    
    @property
    def database_url(self) -> str:
        """获取数据库连接URL"""
        return f"mysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    @property
    def tortoise_orm_config(self) -> dict:
        """获取Tortoise ORM配置"""
        return {
            "connections": {
                "default": {
                    "engine": "tortoise.backends.mysql",
                    "credentials": {
                        "host": self.db_host,
                        "port": self.db_port,
                        "user": self.db_user,
                        "password": self.db_password,
                        "database": self.db_name,
                        "charset": "utf8mb4",
                        "connect_timeout": 60,        # 连接超时 60秒
                        "minsize": 1,
                        "maxsize": 10,
                    }
                }
            },
            "apps": {
                "models": {
                    "models": [
                        "app.models",
                        "aerich.models",
                    ],
                    "default_connection": "default",
                }
            },
            "use_tz": False,
            "timezone": "Asia/Shanghai",
        }


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


settings = get_settings()
