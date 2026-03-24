"""添加 task_id 字段到 requirements 表"""
import pymysql
from app.config import settings

def add_task_id_column():
    connection = pymysql.connect(
        host=settings.db_host,
        port=settings.db_port,
        user=settings.db_user,
        password=settings.db_password,
        database=settings.db_name,
        charset='utf8mb4'
    )
    
    try:
        with connection.cursor() as cursor:
            # 检查字段是否已存在
            cursor.execute("DESCRIBE requirements")
            columns = [col[0] for col in cursor.fetchall()]
            
            if 'task_id' in columns:
                print("✅ task_id 字段已存在")
            else:
                # 添加字段
                cursor.execute("""
                    ALTER TABLE requirements 
                    ADD COLUMN task_id VARCHAR(100) NULL AFTER project_id
                """)
                connection.commit()
                print("✅ task_id 字段添加成功")
    finally:
        connection.close()

if __name__ == "__main__":
    add_task_id_column()
