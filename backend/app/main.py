"""
qaitest智测平台 - FastAPI主入口
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from loguru import logger
from tortoise.exceptions import OperationalError, IntegrityError
import asyncio

from app.config import settings
from app.database import init_db, close_db, check_db_connection
from app.api import projects, versions, requirements, testcases, testplans, testreports, websocket, model_config, custom_model, rag, ai_test_tasks, agent_prompts, llm_models, embedding_models, model_status


async def retry_db_operation(operation, max_retries=3, delay=1):
    """重试数据库操作"""
    last_error = None
    for attempt in range(max_retries):
        try:
            return await operation()
        except OperationalError as e:
            last_error = e
            logger.warning(f"数据库操作失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(delay * (attempt + 1))  # 指数退避
    raise last_error


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    logger.info(f"qaitest智测平台启动中... 环境: {settings.app_env}")
    
    # 检查 Milvus 连接（使用 Docker 部署的 Milvus）
    from pymilvus import connections
    try:
        connections.connect(
            alias="default",
            host=settings.milvus_host,
            port=settings.milvus_port,
            timeout=5
        )
        logger.info(f"✅ Milvus 已连接: {settings.milvus_host}:{settings.milvus_port}")
        connections.disconnect("default")
    except Exception as e:
        logger.warning(f"⚠️ Milvus 连接失败 ({settings.milvus_host}:{settings.milvus_port}): {e}")
        logger.warning("⚠️ RAG功能将不可用，请确保 Milvus 已启动: docker-compose -f docker-compose-milvus.yml up -d")
    
    await init_db()
    
    # 初始化默认提示词模板
    try:
        from app.models.agent_prompt import init_default_prompts
        await init_default_prompts()
    except Exception as e:
        logger.warning(f"初始化提示词模板失败: {e}")
    
    logger.info("qaitest智测平台启动完成")

    yield

    # 关闭时清理 - 等待所有运行中的任务完成后再关闭数据库连接
    logger.info("qaitest智测平台关闭中...")
    
    # 等待一段时间让正在运行的任务完成
    # Runtime模式的AI任务可能需要更多时间完成
    await asyncio.sleep(2)
    
    await close_db()
    logger.info("qaitest智测平台已关闭")


# 创建FastAPI应用
app = FastAPI(
    title="qaitest智测平台",
    description="企业级AI测试用例生成系统API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应配置具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理 - 数据库连接错误（不处理 IntegrityError，那是业务逻辑错误）
@app.exception_handler(OperationalError)
async def handle_db_operational_error(request: Request, exc: OperationalError):
    """处理数据库连接操作错误"""
    logger.error(f"数据库操作错误: {exc}")
    return JSONResponse(
        status_code=503,
        content={
            "detail": "数据库连接超时，请稍后重试",
            "error_type": "database_timeout"
        }
    )


# 全局异常处理 - 业务逻辑错误
@app.exception_handler(IntegrityError)
async def handle_integrity_error(request: Request, exc: IntegrityError):
    """处理数据库完整性错误（如重复ID等业务约束错误）"""
    logger.error(f"数据库完整性错误: {exc}")
    return JSONResponse(
        status_code=409,
        content={
            "detail": "数据冲突，请检查是否重复提交",
            "error_type": "data_conflict"
        }
    )


# 注册API路由
app.include_router(projects.router, prefix="/api/projects", tags=["项目管理"])
app.include_router(versions.router, prefix="/api/versions", tags=["版本管理"])
app.include_router(requirements.router, prefix="/api/requirements", tags=["功能点管理"])
app.include_router(testcases.router, prefix="/api/testcases", tags=["用例管理"])
app.include_router(testplans.router, prefix="/api/testplans", tags=["测试计划"])
app.include_router(testreports.router, prefix="/api/testreports", tags=["测试报告"])
app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])
app.include_router(model_config.router, prefix="/api/models", tags=["模型配置"])
app.include_router(custom_model.router, prefix="/api/models/custom", tags=["自定义模型管理"])
app.include_router(rag.router, prefix="/api/rag", tags=["RAG索引管理"])
app.include_router(ai_test_tasks.router, prefix="/api/ai-test", tags=["AI测试任务"])
app.include_router(agent_prompts.router, tags=["Agent提示词管理"])
app.include_router(llm_models.router, tags=["LLM模型管理"])
app.include_router(embedding_models.router, tags=["嵌入模型管理"])
app.include_router(model_status.router, tags=["模型状态"])


@app.get("/")
async def root():
    """根路径健康检查"""
    return {
        "name": "qaitest智测平台",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """健康检查接口"""
    db_healthy = await check_db_connection()
    return {
        "status": "healthy" if db_healthy else "degraded",
        "database": "connected" if db_healthy else "disconnected"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.app_port,
        reload=settings.app_debug,
    )
