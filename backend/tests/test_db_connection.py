"""
数据库连接测试脚本
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tortoise import Tortoise
from app.config import settings
from loguru import logger


async def test_database_connection():
    """测试数据库连接"""
    print("=" * 60)
    print("数据库连接测试")
    print("=" * 60)

    print(f"\n📋 数据库配置:")
    print(f"  主机: {settings.db_host}")
    print(f"  端口: {settings.db_port}")
    print(f"  用户: {settings.db_user}")
    print(f"  数据库: {settings.db_name}")
    print(f"  连接URL: mysql://{settings.db_user}:***@{settings.db_host}:{settings.db_port}/{settings.db_name}")

    try:
        print(f"\n🔄 正在连接数据库...")
        await Tortoise.init(config=settings.tortoise_orm_config)

        conn = Tortoise.get_connection("default")
        result = await conn.execute_query("SELECT 1 as test")

        print(f"✅ 数据库连接成功!")
        print(f"   测试查询结果: {result}")

        version_result = await conn.execute_query("SELECT VERSION() as version")
        if version_result and len(version_result[1]) > 0:
            db_version = version_result[1][0]['version']
            print(f"   MySQL版本: {db_version}")

        tables_result = await conn.execute_query(
            "SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = %s",
            [settings.db_name]
        )
        table_count = len(tables_result[1]) if tables_result else 0
        print(f"   现有表数量: {table_count}")

        if table_count > 0:
            print(f"   表列表:")
            for row in tables_result[1][:10]:
                print(f"     - {row['TABLE_NAME']}")
            if table_count > 10:
                print(f"     ... 还有 {table_count - 10} 个表")

        return True

    except Exception as e:
        print(f"\n❌ 数据库连接失败!")
        print(f"   错误类型: {type(e).__name__}")
        print(f"   错误信息: {str(e)}")
        return False

    finally:
        await Tortoise.close_connections()
        print(f"\n🔌 数据库连接已关闭")


if __name__ == "__main__":
    success = asyncio.run(test_database_connection())
    print("\n" + "=" * 60)
    if success:
        print("✅ 测试完成 - 数据库连接正常")
    else:
        print("❌ 测试完成 - 数据库连接失败")
    print("=" * 60)
    sys.exit(0 if success else 1)
