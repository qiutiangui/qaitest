"""
数据库初始化脚本
一键创建所有数据表
"""
import asyncio
from tortoise import Tortoise
from app.config import settings


async def init_database():
    await Tortoise.init(config=settings.tortoise_orm_config)
    await Tortoise.generate_schemas()
    print("✅ 数据库表创建完成")


if __name__ == "__main__":
    asyncio.run(init_database())
