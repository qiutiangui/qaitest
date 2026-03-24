"""
测试飞书知识库读取 - 同步版本
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.rag.readers import FeishuReader
from app.config import settings


async def main():
    app_id = settings.feishu_app_id
    app_secret = settings.feishu_app_secret

    if not app_id or not app_secret:
        print("❌ 飞书应用未配置，请检查 .env 中的 feishu_app_id / feishu_app_secret")
        return

    print(f"飞书应用ID: {app_id}")

    reader = FeishuReader(app_id=app_id, app_secret=app_secret)

    wiki_url = "https://my.feishu.cn/wiki/ChetwMJvMiMMNAk1qrFcZWz8nib"

    print(f"\n📖 正在读取知识库: {wiki_url}")
    print("-" * 50)

    try:
        docs = await reader.load_data_from_url(wiki_url)

        if docs:
            doc = docs[0]
            print(f"\n✅ 读取成功!")
            print(f"标题: {doc.metadata.get('title', 'N/A')}")
            print(f"内容长度: {len(doc.text)} 字符")
            print(f"\n预览内容 (前2000字):")
            print("-" * 50)
            print(doc.text[:2000])
            if len(doc.text) > 2000:
                print(f"\n... (还有 {len(doc.text) - 2000} 字)")
        else:
            print("❌ 无法获取文档内容")

    except Exception as e:
        print(f"❌ 读取失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
