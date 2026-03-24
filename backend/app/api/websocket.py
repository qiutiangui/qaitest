"""
WebSocket API - 实时通信
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
from loguru import logger

router = APIRouter()


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 按任务ID存储连接
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, task_id: str):
        """建立连接"""
        await websocket.accept()
        if task_id not in self.active_connections:
            self.active_connections[task_id] = set()
        self.active_connections[task_id].add(websocket)
        logger.info(f"WebSocket连接建立: task_id={task_id}, 当前连接数={len(self.active_connections[task_id])}")
    
    def disconnect(self, websocket: WebSocket, task_id: str):
        """断开连接"""
        if task_id in self.active_connections:
            self.active_connections[task_id].discard(websocket)
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]
        logger.info(f"WebSocket连接断开: task_id={task_id}")
    
    async def send_message(self, task_id: str, message: dict):
        """发送消息到指定任务的所有连接"""
        if task_id in self.active_connections:
            for connection in self.active_connections[task_id]:
                await connection.send_json(message)
    
    async def broadcast(self, message: dict):
        """广播消息到所有连接"""
        for task_id in self.active_connections:
            await self.send_message(task_id, message)


manager = ConnectionManager()


@router.websocket("/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    """WebSocket端点"""
    await manager.connect(websocket, task_id)
    try:
        while True:
            # 接收客户端消息（心跳检测等）
            data = await websocket.receive_json()
            
            # 处理心跳
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            else:
                # 其他消息处理
                logger.debug(f"收到WebSocket消息: task_id={task_id}, data={data}")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, task_id)
    except Exception as e:
        logger.error(f"WebSocket异常: {e}")
        manager.disconnect(websocket, task_id)


async def push_agent_message(
    task_id: str, 
    agent_name: str, 
    content: str, 
    message_type: str = "thinking",
    extra_data: dict = None,
    progress: int = None
):
    """
    推送Agent消息到前端
    
    Args:
        task_id: 任务ID
        agent_name: Agent名称
        content: 消息内容
        message_type: 消息类型 (thinking/response/error/complete)
        extra_data: 额外数据
        progress: 进度值（用例生成阶段进度 0-100），会自动转换为整体进度
    """
    from datetime import datetime
    
    # 智能体名称映射为用户友好的名称
    agent_display_names = {
        # Agent内部名称
        "RequirementAcquireAgent": "需求获取",
        "RequirementAnalysisAgent": "需求分析",
        "RequirementReviewAgent": "完整性检查",
        "RequirementOutputAgent": "数据保存",
        "TestcaseGenerateAgent": "用例生成",
        "TestcaseReviewAgent": "用例评审",
        "TestcaseFormatAgent": "格式优化",
        "TestcaseFinalizeAgent": "整体定稿",
        "TestcaseInDatabaseAgent": "数据保存",
        "RAGIndexAgent": "文档索引",
        "ReviewAgent": "AI评审",
        # 流程步骤代码（用于前端进度条）
        "step2_analysis": "需求分析",
        "step3_review": "需求评审",
        "step4_generate": "测试用例生成",
        "step5_review": "测试用例评审",
        # 兼容旧代码
        "requirement_analysis": "需求分析",
        "testcase_generation": "测试用例生成",
        "用例生成": "用例生成",
        "用例评审": "用例评审",
        "格式优化": "格式优化",
        "数据保存": "数据保存",
        "System": "系统",
    }
    
    display_name = agent_display_names.get(agent_name, agent_name)
    
    message = {
        "type": message_type,
        "agent": agent_name,  # 保留原始名称供前端判断
        "agent_code": agent_name,  # 保留原始名称
        "content": content,
        "timestamp": datetime.now().isoformat(),
    }
    
    if extra_data:
        message["data"] = extra_data
    
    # 添加进度字段（用于前端任务记录页面的进度条同步）
    # 将用例生成阶段进度转换为整体进度: 整体 = 40 + (阶段进度 * 0.6)
    if progress is not None:
        message["progress"] = 40 + int(progress * 0.6)
    else:
        # 从content中解析进度标签
        import re
        progress_match = re.search(r'\[PROGRESS\](\d+)\[/PROGRESS\]', content)
        if progress_match:
            phase_progress = int(progress_match.group(1))
            message["progress"] = 40 + int(phase_progress * 0.6)
    
    await manager.send_message(task_id, message)


# 兼容性别名
async def push_to_websocket(task_id: str, agent_name: str, content: str, message_type: str = "thinking", extra_data: dict = None, progress: int = None):
    """
    推送消息到WebSocket（兼容性别名）
    """
    await push_agent_message(task_id, agent_name, content, message_type, extra_data, progress)
