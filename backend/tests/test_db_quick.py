"""数据库连接测试（简化版）"""
import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tortoise import Tortoise
from app.config import settings


async def test():
    try:
        config = settings.tortoise_orm_config.copy()
        config['apps']['models']['models'] = ['app.models']

        await Tortoise.init(config=config)
        conn = Tortoise.get_connection('default')

        result = await conn.execute_query('SELECT 1 as test')
        print('✅ 数据库连接成功!')

        ver = await conn.execute_query('SELECT VERSION() as v')
        print(f'MySQL版本: {ver[1][0]["v"]}')

        db = await conn.execute_query('SELECT DATABASE() as db')
        print(f'当前数据库: {db[1][0]["db"]}')

        await Tortoise.close_connections()
        print('🔌 连接已关闭')

    except Exception as e:
        print(f'❌ 失败: {e}')
        import traceback
        traceback.print_exc()


asyncio.run(test())
