/**
 * AI测试任务API - 统一的需求分析和用例生成
 */
import api from './index'

// 阶段进度
export interface PhaseProgress {
  code: string
  name: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number
  started_at: string | null
  completed_at: string | null
  logs: string[]
}

// 任务日志条目
export interface TaskLogEntry {
  timestamp: string
  agent: string
  agent_name: string
  level: 'info' | 'success' | 'error' | 'warning'
  type: string
  content: string
}

// AI测试任务状态
export interface AITestTaskStatus {
  id: number
  task_id: string
  project_id: number | null
  version_id: number | null
  task_name: string | null
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  progress: number
  
  // 需求分析阶段
  requirement_phase_status: string
  requirement_phase_progress: number
  total_requirements: number
  saved_requirements: number
  
  // 用例生成阶段
  testcase_phase_status: string
  testcase_phase_progress: number
  total_testcases: number
  saved_testcases: number
  
  current_phase: string | null
  current_phase_code: string | null
  phases: PhaseProgress[]
  
  error_message: string | null
  logs: TaskLogEntry[]
  
  created_at: string | null
  started_at: string | null
  completed_at: string | null
  
  project_name?: string
}

// 功能点
export interface Requirement {
  id: number
  name: string
  description: string
  category: string
  module: string
  priority: string
  created_at: string
}

// 测试用例
export interface TestCase {
  id: number
  title: string
  priority: string
  status: string
  test_type: string
  created_at: string
}

// 日志查询响应
export interface LogsResponse {
  task_id: string
  status: string
  progress: number
  current_phase: string | null
  requirement_phase_status: string
  testcase_phase_status: string
  total_logs: number
  new_logs: TaskLogEntry[]
}

// 任务统计
export interface TaskStats {
  total: number
  running: number
  pending: number
  completed: number
  failed: number
}

export const aiTestApi = {
  /**
   * 创建AI测试任务
   */
  create(params: {
    project_id?: number
    version_id?: number
    task_name?: string
    description?: string
    file?: File
    llm_config?: {
      requirement_analyze_model?: { provider: string; custom_id?: number; model?: string }
      testcase_generate_model?: { provider: string; custom_id?: number; model?: string }
      testcase_review_model?: { provider: string; custom_id?: number; model?: string }
    }
  }): Promise<{ task_id: string; message: string }> {
    const formData = new FormData()
    if (params.project_id) formData.append('project_id', String(params.project_id))
    if (params.version_id) formData.append('version_id', String(params.version_id))
    if (params.task_name) formData.append('task_name', params.task_name)
    if (params.description) formData.append('description', params.description)
    if (params.file) formData.append('file', params.file)
    // 添加 llm_config
    if (params.llm_config) {
      formData.append('llm_config', JSON.stringify(params.llm_config))
    }

    return api.post('/ai-test/create', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  /**
   * 获取任务列表
   */
  listTasks(params?: {
    project_id?: number
    status?: string
    keyword?: string
    page?: number
    page_size?: number
  }): Promise<{
    total: number
    items: AITestTaskStatus[]
  }> {
    return api.get('/ai-test/list', { params })
  },

  /**
   * 获取任务详情
   */
  getTask(taskId: string): Promise<AITestTaskStatus> {
    return api.get(`/ai-test/${taskId}`)
  },

  /**
   * 获取任务关联的功能点
   */
  getRequirements(taskId: string): Promise<{
    total: number
    items: Requirement[]
  }> {
    return api.get(`/ai-test/${taskId}/requirements`)
  },

  /**
   * 获取任务关联的测试用例
   */
  getTestcases(taskId: string): Promise<{
    total: number
    items: TestCase[]
  }> {
    return api.get(`/ai-test/${taskId}/testcases`)
  },

  /**
   * 获取任务日志（增量加载）
   */
  getLogs(taskId: string, afterIndex: number = 0): Promise<LogsResponse> {
    return api.get(`/ai-test/${taskId}/logs`, {
      params: { after_index: afterIndex }
    })
  },

  /**
   * 删除任务
   */
  deleteTask(taskId: string, force: boolean = false): Promise<{ message: string }> {
    return api.delete(`/ai-test/${taskId}?force=${force}`)
  },

  /**
   * 取消任务
   */
  cancelTask(taskId: string): Promise<{ message: string; task_id: string }> {
    return api.post(`/ai-test/${taskId}/cancel`)
  },

  /**
   * 获取任务统计
   */
  getStats(): Promise<TaskStats> {
    return api.get('/ai-test/stats')
  },
}

export default aiTestApi
