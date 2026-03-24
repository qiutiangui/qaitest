"""
数据库迁移脚本 - 添加 model_info 字段到 ai_test_tasks 表

使用方法:
    cd backend
    PYTHONPATH=. python scripts/add_model_info_column.py
"""

import asyncio
import pymysql
from app.config import settings


def migrate():
    """添加 model_info 列到 ai_test_tasks 表"""
    
    print("开始数据库迁移...")
    print(f"数据库: {settings.db_host}:{settings.db_port}/{settings.db_name}")
    
    # 使用 pymysql 同步连接
    conn = pymysql.connect(
        host=settings.db_host,
        port=settings.db_port,
        user=settings.db_user,
        password=settings.db_password,
        db=settings.db_name,
        charset='utf8mb4'
    )
    
    try:
        with conn.cursor() as cursor:
            # 检查列是否存在
            cursor.execute("DESCRIBE ai_test_tasks")
            columns = [row[0] for row in cursor.fetchall()]
            
            if 'model_info' not in columns:
                print("➕ 添加 model_info 列...")
                cursor.execute("""
                    ALTER TABLE ai_test_tasks 
                    ADD COLUMN model_info JSON DEFAULT NULL
                    COMMENT '使用的模型信息记录'
                    AFTER review_model
                """)
                conn.commit()
                print("✅ model_info 列添加成功!")
            else:
                print("ℹ️ model_info 列已存在，跳过")
    finally:
        conn.close()
    
    print("✅ 迁移完成!")


if __name__ == "__main__":
    migrate()
