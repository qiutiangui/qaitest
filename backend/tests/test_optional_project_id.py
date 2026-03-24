#!/usr/bin/env python3
"""
测试 project_id 为 None 的情况
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.database import init_db, close_db
from app.models import Requirement, TestCase, AITestTask


async def test_optional_project_id():
    """测试可选的 project_id"""
    await init_db()

    try:
        req1 = await Requirement.create(
            project_id=None,
            requirement_name="测试需求",
            name="测试功能点",
            description="这是一个测试功能点",
            priority="高"
        )
        print(f"✓ 成功创建无 project_id 的 Requirement: {req1.id}")

        req2 = await Requirement.create(
            project_id=1,
            requirement_name="测试需求2",
            name="测试功能点2",
            description="这是另一个测试功能点",
            priority="中"
        )
        print(f"✓ 成功创建有 project_id 的 Requirement: {req2.id}")

        tc1 = await TestCase.create(
            project_id=None,
            requirement_id=req1.id,
            title="测试用例1",
            description="这是一个测试用例",
            priority="高"
        )
        print(f"✓ 成功创建无 project_id 的 TestCase: {tc1.id}")

        tc2 = await TestCase.create(
            project_id=1,
            requirement_id=req2.id,
            title="测试用例2",
            description="这是另一个测试用例",
            priority="中"
        )
        print(f"✓ 成功创建有 project_id 的 TestCase: {tc2.id}")

        task1 = await AITestTask.create(
            task_id="test_task_001",
            project_id=None,
            task_name="测试任务",
            status="completed",
            progress=100
        )
        print(f"✓ 成功创建无 project_id 的 AITestTask: {task1.id}")

        reqs_no_project = await Requirement.filter(project_id=None)
        print(f"✓ 查询到 {len(reqs_no_project)} 个无 project_id 的 Requirement")

        reqs_with_project = await Requirement.filter(project_id=1)
        print(f"✓ 查询到 {len(reqs_with_project)} 个 project_id=1 的 Requirement")

        print("\n所有测试通过！")

        await task1.delete()
        await tc1.delete()
        await tc2.delete()
        await req1.delete()
        await req2.delete()
        print("✓ 测试数据已清理")

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(test_optional_project_id())
