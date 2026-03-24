-- 迁移数据库表结构 - 添加缺失的列
-- 目标表: requirement_analysis_tasks

ALTER TABLE requirement_analysis_tasks
    ADD COLUMN IF NOT EXISTS current_phase VARCHAR(50) DEFAULT NULL COMMENT '当前阶段名称',
    ADD COLUMN IF NOT EXISTS current_phase_code VARCHAR(50) DEFAULT NULL COMMENT '当前阶段代码',
    ADD COLUMN IF NOT EXISTS phases JSON DEFAULT NULL COMMENT '阶段进度列表',
    ADD COLUMN IF NOT EXISTS total_requirements INT DEFAULT 0 COMMENT '分析出的需求总数',
    ADD COLUMN IF NOT EXISTS saved_count INT DEFAULT 0 COMMENT '成功保存的功能点数',
    ADD COLUMN IF NOT EXISTS saved_ids JSON DEFAULT NULL COMMENT '保存的功能点ID列表',
    ADD COLUMN IF NOT EXISTS result JSON DEFAULT NULL COMMENT '任务结果详情',
    ADD COLUMN IF NOT EXISTS error_message TEXT DEFAULT NULL COMMENT '错误信息',
    ADD COLUMN IF NOT EXISTS error_details JSON DEFAULT NULL COMMENT '错误详情',
    ADD COLUMN IF NOT EXISTS logs JSON DEFAULT NULL COMMENT '执行日志列表',
    ADD COLUMN IF NOT EXISTS started_at DATETIME DEFAULT NULL COMMENT '开始执行时间',
    ADD COLUMN IF NOT EXISTS completed_at DATETIME DEFAULT NULL COMMENT '完成时间';

-- 同时检查 testcase_generation_tasks 表是否有相同问题
-- 如果表存在但缺少列，也需要添加
