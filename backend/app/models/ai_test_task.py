"""
AI测试任务模型 - 统一的需求分析和用例生成任务
"""
from tortoise import fields, models
from datetime import datetime


class AITestTask(models.Model):
    """
    AI测试任务表 - 统一记录需求分析和用例生成的完整流程
    
    一个任务包含两个阶段：
    1. 需求分析阶段：文档解析 → 功能点提取 → 功能点保存
    2. 用例生成阶段：用例设计 → 用例评审 → 用例保存
    """

    id = fields.IntField(pk=True, description="任务ID")
    task_id = fields.CharField(max_length=100, unique=True, description="任务唯一ID")
    project_id = fields.IntField(null=True, description="关联项目ID")
    version_id = fields.IntField(null=True, description="关联版本ID")
    
    # 任务基本信息
    task_name = fields.CharField(max_length=255, null=True, description="任务名称/需求名称")
    
    # 任务整体状态
    status = fields.CharField(
        max_length=20,
        default="pending",
        description="状态：pending/running/completed/failed/cancelled"
    )
    progress = fields.IntField(default=0, description="整体进度：0-100")
    
    # ========== 阶段1: 需求分析 ==========
    requirement_phase_status = fields.CharField(
        max_length=20,
        default="pending",
        description="需求分析阶段状态"
    )
    requirement_phase_progress = fields.IntField(default=0, description="需求分析阶段进度")
    total_requirements = fields.IntField(default=0, description="分析出的功能点总数")
    saved_requirements = fields.IntField(default=0, description="成功保存的功能点数")
    saved_requirement_ids = fields.JSONField(null=True, description="保存的功能点ID列表")
    
    # ========== 阶段2: 用例生成 ==========
    testcase_phase_status = fields.CharField(
        max_length=20,
        default="pending",
        description="用例生成阶段状态"
    )
    testcase_phase_progress = fields.IntField(default=0, description="用例生成阶段进度")
    total_testcases = fields.IntField(default=0, description="生成的用例总数")
    saved_testcases = fields.IntField(default=0, description="成功保存的用例数")
    saved_testcase_ids = fields.JSONField(null=True, description="保存的用例ID列表")
    
    # 任务输入（保存原始输入信息）
    input_source = fields.CharField(max_length=50, null=True, description="输入来源：file/feishu/description")
    input_filename = fields.CharField(max_length=255, null=True, description="原始文件名")
    document_content = fields.TextField(null=True, description="原始文档内容（可空，节省存储）")
    
    # 当前执行阶段
    current_phase = fields.CharField(max_length=50, null=True, description="当前阶段：requirement_analysis/testcase_generation")
    current_phase_code = fields.CharField(max_length=50, null=True, description="当前阶段代码")
    phases = fields.JSONField(null=True, description="阶段详情列表")
    
    # 执行结果
    result = fields.JSONField(null=True, description="任务结果详情")
    error_message = fields.TextField(null=True, description="错误信息")
    error_details = fields.JSONField(null=True, description="错误详情")
    
    # 日志（持久化）
    logs = fields.JSONField(null=True, description="执行日志列表")
    
    # 模型配置
    generation_model = fields.CharField(max_length=100, null=True, description="用例生成模型")
    review_model = fields.CharField(max_length=100, null=True, description="评审模型")
    
    # 时间戳
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    started_at = fields.DatetimeField(null=True, description="开始执行时间")
    completed_at = fields.DatetimeField(null=True, description="完成时间")

    class Meta:
        table = "ai_test_tasks"
        table_description = "AI测试任务表"
        indexes = [
            ("project_id",),
            ("version_id",),
            ("status",),
            ("created_at",),
        ]

    def __str__(self):
        return f"AITestTask({self.id}, {self.task_name}, {self.status})"

    async def add_log(self, agent: str, agent_name: str, content: str, level: str = "info", log_type: str = "info"):
        """添加日志条目"""
        from app.database import ensure_db_connection
        
        # 确保数据库连接可用
        if not await ensure_db_connection():
            import logging
            logging.warning(f"数据库连接不可用，跳过日志添加: task_id={self.task_id}")
            return
        
        if self.logs is None:
            self.logs = []

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "agent_name": agent_name,
            "level": level,
            "type": log_type,
            "content": content,
        }
        self.logs.append(log_entry)

        # 限制日志数量，防止数据库过大
        if len(self.logs) > 2000:
            self.logs = self.logs[-1000:]
        await self.save()

    async def update_phase(self, phase_code: str, phase_name: str, status: str = "running"):
        """更新当前阶段"""
        from app.database import ensure_db_connection
        
        # 确保数据库连接可用
        if not await ensure_db_connection():
            import logging
            logging.warning(f"数据库连接不可用，跳过阶段更新: task_id={self.task_id}")
            return
        
        self.current_phase = phase_name
        self.current_phase_code = phase_code

        if self.phases is None:
            self.phases = []

        # 查找或创建阶段
        found = False
        for phase in self.phases:
            if phase.get("code") == phase_code:
                phase["status"] = status
                if status == "running" and not phase.get("started_at"):
                    phase["started_at"] = datetime.now().isoformat()
                elif status in ["completed", "failed"]:
                    phase["completed_at"] = datetime.now().isoformat()
                found = True
                break

        if not found:
            self.phases.append({
                "code": phase_code,
                "name": phase_name,
                "status": status,
                "progress": 0,
                "started_at": datetime.now().isoformat() if status == "running" else None,
                "completed_at": None,
                "logs": [],
            })
        await self.save()
    
    async def update_requirement_progress(self, status: str = "running", progress: int = 0, 
                                          saved_count: int = 0, saved_ids: list = None):
        """更新需求分析阶段进度"""
        from app.database import ensure_db_connection
        
        # 确保数据库连接可用
        if not await ensure_db_connection():
            import logging
            logging.warning(f"数据库连接不可用，跳过需求进度更新: task_id={self.task_id}")
            return
        
        self.requirement_phase_status = status
        self.requirement_phase_progress = progress
        self.saved_requirements = saved_count
        if saved_ids:
            self.saved_requirement_ids = saved_ids
        
        # 根据阶段计算整体进度和状态
        if status == "running":
            self.progress = int(progress * 0.4)
            self.status = "running"
        elif status == "completed":
            self.progress = 40
            self.status = "running"  # 需求完成后，用例生成阶段可能还没开始，保持 running
        elif status == "failed":
            self.status = "failed"
        else:
            self.progress = 0
        
        if status == "running" and self.started_at is None:
            self.started_at = datetime.now()
        
        await self.save()
    
    async def update_testcase_progress(self, status: str = "running", progress: int = 0,
                                       saved_count: int = 0, saved_ids: list = None):
        """更新用例生成阶段进度"""
        from app.database import ensure_db_connection
        
        # 确保数据库连接可用
        if not await ensure_db_connection():
            import logging
            logging.warning(f"数据库连接不可用，跳过用例进度更新: task_id={self.task_id}")
            return
        
        self.testcase_phase_status = status
        self.testcase_phase_progress = progress
        self.saved_testcases = saved_count
        if saved_ids:
            self.saved_testcase_ids = saved_ids
        
        # 根据阶段计算整体进度和状态
        if status == "completed":
            self.progress = 100
            self.status = "completed"
        else:
            self.progress = 40 + int(progress * 0.6)
            self.status = "running"
        
        await self.save()
        
        # 推送 WebSocket 消息，通知前端进度更新
        try:
            from app.api.websocket import push_agent_message
            import asyncio
            # 尝试在当前事件循环中推送，如果失败则记录日志
            try:
                loop = asyncio.get_running_loop()
                # 如果有正在运行的事件循环，在其中推送
                loop.create_task(push_agent_message(
                    self.task_id,
                    "System",
                    f"[PROGRESS]{self.progress}[/PROGRESS]",
                    "progress",
                    {"phase": "testcase", "progress": self.progress}
                ))
            except RuntimeError:
                # 没有正在运行的事件循环，同步调用
                asyncio.run(push_agent_message(
                    self.task_id,
                    "System",
                    f"[PROGRESS]{self.progress}[/PROGRESS]",
                    "progress",
                    {"phase": "testcase", "progress": self.progress}
                ))
        except Exception as e:
            import logging
            logging.error(f"WebSocket推送失败: {e}")
    
    async def mark_complete(self, result: dict = None):
        """标记任务完成"""
        from app.database import ensure_db_connection
        
        # 确保数据库连接可用
        if not await ensure_db_connection():
            import logging
            logging.warning(f"数据库连接不可用，跳过任务完成标记: task_id={self.task_id}")
            return
        
        self.status = "completed"
        self.progress = 100
        self.completed_at = datetime.now()
        if result:
            self.result = result
        await self.save()
    
    async def mark_failed(self, error_message: str, error_details: dict = None):
        """标记任务失败"""
        from app.database import ensure_db_connection
        
        # 确保数据库连接可用
        if not await ensure_db_connection():
            import logging
            logging.warning(f"数据库连接不可用，跳过任务失败标记: task_id={self.task_id}")
            return
        
        self.status = "failed"
        self.error_message = error_message
        if error_details:
            self.error_details = error_details
        self.completed_at = datetime.now()
        await self.save()
    
    async def mark_cancelled(self):
        """标记任务取消"""
        from app.database import ensure_db_connection
        
        # 确保数据库连接可用
        if not await ensure_db_connection():
            import logging
            logging.warning(f"数据库连接不可用，跳过任务取消标记: task_id={self.task_id}")
            return
        
        self.status = "cancelled"
        self.error_message = "用户手动取消"
        self.completed_at = datetime.now()
        await self.save()
