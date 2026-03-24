"""
数据库配置模块
"""
from tortoise import Tortoise
from app.config import settings
from loguru import logger
import asyncio
import json


async def init_db():
    """初始化数据库连接"""
    try:
        await Tortoise.init(
            config=settings.tortoise_orm_config
        )
        logger.info("数据库连接初始化完成")

        # 导入所有模型以确保注册
        from app.models import AgentPromptTemplate, Project, ProjectVersion, VersionSnapshot, Requirement, TestCase, TestStep, TestPlan, TestPlanCase, TestReport, AITestTask, CustomModel  # noqa
        logger.info("所有模型已导入")

        # 测试连接
        await Tortoise.get_connection("default").execute_query("SELECT 1")
        logger.info("数据库连接测试通过")

        # 生成表结构
        await Tortoise.generate_schemas(safe=True)
        logger.info("数据库表结构生成完成")

        # 确保模型被导入
        from app.models import agent_prompt  # noqa

        # 等待连接池完全初始化
        await asyncio.sleep(0.2)
        
        # 初始化默认Agent提示词模板
        try:
            from app.models.agent_prompt import DEFAULT_PROMPTS
            conn = Tortoise.get_connection("default")
            
            for agent_type, config in DEFAULT_PROMPTS.items():
                # 检查是否已存在
                result = await conn.execute_query(
                    "SELECT id FROM agent_prompts WHERE agent_type = %s", 
                    [agent_type]
                )
                if result and result[1]:
                    logger.info(f"提示词模板 {agent_type} 已存在，跳过")
                    continue

                # 插入新记录
                await conn.execute_query(
                    """INSERT INTO agent_prompts 
                       (agent_type, name, description, system_prompt, user_prompt_template, 
                        variables, is_active, is_editable, version) 
                       VALUES (%s, %s, %s, %s, %s, %s, 1, 1, 1)""",
                    [
                        agent_type,
                        config["name"],
                        config["description"],
                        config["system_prompt"],
                        config.get("user_prompt_template"),
                        json.dumps(config.get("variables", [])) if config.get("variables") else None
                    ]
                )
                logger.info(f"提示词模板 {agent_type} 创建成功")
                
            logger.info(f"默认提示词模板初始化完成，共 {len(DEFAULT_PROMPTS)} 个")
        except Exception as e:
            logger.warning(f"Agent提示词模板初始化失败: {e}")

    except Exception as e:
        logger.error(f"数据库连接初始化失败: {e}")
        raise


async def close_db():
    """关闭数据库连接"""
    await Tortoise.close_connections()
    logger.info("数据库连接已关闭")


async def check_db_connection():
    """检查数据库连接状态"""
    try:
        conn = Tortoise.get_connection("default")
        await conn.execute_query("SELECT 1")
        return True
    except Exception as e:
        logger.warning(f"数据库连接检查失败: {e}")
        return False
