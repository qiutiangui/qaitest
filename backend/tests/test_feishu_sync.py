"""
同步测试飞书知识库读取
"""
import httpx
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.config import settings


def test_feishu():
    app_id = settings.feishu_app_id
    app_secret = settings.feishu_app_secret

    if not app_id or not app_secret:
        print("❌ 飞书应用未配置，请检查 .env 中的 feishu_app_id / feishu_app_secret")
        return

    url = 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal'
    response = httpx.post(url, json={'app_id': app_id, 'app_secret': app_secret}, timeout=30)
    token = response.json()['tenant_access_token']
    headers = {'Authorization': f'Bearer {token}'}

    wiki_url = "https://my.feishu.cn/wiki/ChetwMJvMiMMNAk1qrFcZWz8nib"
    match = re.search(r'/wiki/([a-zA-Z0-9]+)', wiki_url)
    doc_id = match.group(1) if match else wiki_url

    print(f"文档ID: {doc_id}")

    doc_url = f'https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}'
    resp = httpx.get(doc_url, headers=headers, timeout=30)
    result = resp.json()

    if result.get('code') != 0:
        print(f"获取文档失败: {result}")
        return

    doc = result.get('data', {}).get('document', {})
    title = doc.get('title', 'Untitled')
    print(f"标题: {title}")

    blocks_url = f'https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks?page_size=500'
    resp = httpx.get(blocks_url, headers=headers, timeout=30)
    blocks_result = resp.json()

    if blocks_result.get('code') != 0:
        print(f"获取块失败: {blocks_result}")
        return

    items = blocks_result.get('data', {}).get('items', [])
    print(f"块数量: {len(items)}")

    texts = []
    for block in items:
        block_type = block.get('block_type', 0)
        text = None

        if 'text' in block:
            elements = block['text'].get('elements', [])
            parts = []
            for elem in elements:
                if 'text_run' in elem:
                    parts.append(elem['text_run'].get('content', ''))
            text = ''.join(parts)

        if text:
            if block_type == 5:
                texts.append(f"# {text}")
            elif block_type == 6:
                texts.append(f"## {text}")
            elif block_type == 7:
                texts.append(f"### {text}")
            elif block_type in [13]:
                texts.append(f"1. {text}")
            elif block_type in [14]:
                texts.append(f"- {text}")
            elif block_type == 17:
                texts.append(f"> {text}")
            else:
                texts.append(text)

    content = "\n\n".join(texts)
    print(f"\n内容长度: {len(content)} 字符")
    print(f"\n预览 (前2000字):")
    print("-" * 50)
    print(content[:2000])

    if len(content) > 2000:
        print(f"\n... (还有 {len(content) - 2000} 字)")


if __name__ == "__main__":
    test_feishu()
