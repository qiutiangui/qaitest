"""
Milvus 连接测试脚本
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.milvus_server import start_milvus_lite, stop_milvus_lite
from pymilvus import connections, utility
from app.config import settings


def test_milvus_connection():
    """测试 Milvus 连接"""
    print("=" * 60)
    print("Milvus 向量数据库连接测试")
    print("=" * 60)

    print(f"\n🔄 启动 Milvus Lite 服务器...")
    if not start_milvus_lite(settings.milvus_port):
        print("❌ 启动失败！")
        return False

    print(f"✅ Milvus Lite 已启动: localhost:{settings.milvus_port}")

    try:
        print(f"\n🔄 连接 Milvus 服务器...")
        connections.connect(
            alias="default",
            host="localhost",
            port=settings.milvus_port
        )
        print("✅ 连接成功!")

        print(f"\n📋 Milvus 版本: {utility.get_server_version()}")

        collections = utility.list_collections()
        print(f"\n📊 现有集合数量: {len(collections)}")
        if collections:
            print("集合列表:")
            for coll in collections[:10]:
                print(f"  - {coll}")

        connections.disconnect("default")
        print("\n🔌 已断开连接")

        return True

    except Exception as e:
        print(f"\n❌ 连接失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        stop_milvus_lite()


if __name__ == "__main__":
    success = test_milvus_connection()
    print("\n" + "=" * 60)
    if success:
        print("✅ 测试完成 - Milvus 连接正常")
    else:
        print("❌ 测试完成 - Milvus 连接失败")
    print("=" * 60)
    sys.exit(0 if success else 1)
