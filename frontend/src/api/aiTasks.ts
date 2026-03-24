/**
 * AI任务状态查询API
 */
import api from './index'

// 任务日志条目
export interface TaskLogEntry {
  timestamp: string
  agent: string
  agent_name: string
  level: 'info' | 'success' | 'error' | 'warning'
  type: 'thinking' | 'response' | 'error' | 'complete' | 'stream'
  content: string
}

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

// 需求分析任务状态
export interface RequirementTaskStatus {
  id: number
  task_id: string
  project_id: number | null
  requirement_name: string
  version_id: number | null
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  progress: number
  current_phase: string | null
  current_phase_code: string | null
  phases: PhaseProgress[]
  total_requirements: number
  saved_count: number
  saved_ids: number[]
  result: any
  error_message: string | null
  error_details: any
  logs: TaskLogEntry[]
  duration: number | null
  created_at: string | null
  updated_at: string | null
  started_at: string | null
  completed_at: string | null
}

// 测试用例生成任务状态
export interface TestcaseTaskStatus {
  id: number
  task_id: string
  project_id: number
  version_id: number | null
  function_ids: number[]
  function_names: string[]
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  progress: number
  current_phase: string | null
  current_phase_code: string | null
  phases: PhaseProgress[]
  total_functions: number
  total_testcases: number
  saved_count: number
  saved_ids: number[]
  result: any
  error_message: string | null
  error_details: any
  logs: TaskLogEntry[]
  duration: number | null
  created_at: string | null
  updated_at: string | null
  started_at: string | null
  completed_at: string | null
}

// 日志查询响应
export interface LogsResponse {
  task_id: string
  status: string
  progress: number
  current_phase: string | null
  total_logs: number
  new_logs: TaskLogEntry[]
}

export const aiTasksApi = {
  /**
   * 获取需求分析任务详情
   */
  getRequirementTask(taskId: string): Promise<RequirementTaskStatus> {
    return api.get(`/ai-tasks/requirement-analysis/${taskId}`)
  },

  /**
   * 获取需求分析任务日志（增量加载）
   */
  getRequirementTaskLogs(taskId: string, afterIndex: number = 0): Promise<LogsResponse> {
    return api.get(`/ai-tasks/requirement-analysis/${taskId}/logs`, {
      params: { after_index: afterIndex }
    })
  },

  /**
   * 获取测试用例生成任务详情
   */
  getTestcaseTask(taskId: string): Promise<TestcaseTaskStatus> {
    return api.get(`/ai-tasks/testcase-generation/${taskId}`)
  },

  /**
   * 获取测试用例生成任务日志（增量加载）
   */
  getTestcaseTaskLogs(taskId: string, afterIndex: number = 0): Promise<LogsResponse> {
    return api.get(`/ai-tasks/testcase-generation/${taskId}/logs`, {
      params: { after_index: afterIndex }
    })
  },

  /**
   * 获取需求分析任务列表
   */
  listRequirementTasks(params?: {
    project_id?: number
    status?: string
    page?: number
    page_size?: number
  }): Promise<{
    total: number
    page: number
    page_size: number
    items: RequirementTaskStatus[]
  }> {
    return api.get('/ai-tasks/requirement-analysis/list', { params })
  },

  /**
   * 获取测试用例生成任务列表
   */
  listTestcaseTasks(params?: {
    project_id?: number
    status?: string
    page?: number
    page_size?: number
  }): Promise<{
    total: number
    page: number
    page_size: number
    items: TestcaseTaskStatus[]
  }> {
    return api.get('/ai-tasks/testcase-generation/list', { params })
  },

  /**
   * 删除需求分析任务
   */
  deleteRequirementTask(taskId: string): Promise<{ message: string }> {
    return api.delete(`/ai-tasks/requirement-analysis/${taskId}`)
  },

  /**
   * 删除测试用例生成任务
   */
  deleteTestcaseTask(taskId: string): Promise<{ message: string }> {
    return api.delete(`/ai-tasks/testcase-generation/${taskId}`)
  },

  /**
   * 取消需求分析任务
   */
  cancelRequirementTask(taskId: string): Promise<{ message: string }> {
    return api.post(`/ai-tasks/requirement-analysis/${taskId}/cancel`)
  },

  /**
   * 取消测试用例生成任务
   */
  cancelTestcaseTask(taskId: string): Promise<{ message: string }> {
    return api.post(`/ai-tasks/testcase-generation/${taskId}/cancel`)
  },

  /**
   * 重试需求分析任务
   */
  retryRequirementTask(taskId: string): Promise<{ task_id: string; message: string }> {
    return api.post('/ai-tasks/requirement-analysis/retry', { task_id: taskId })
  },

  /**
   * 重试用例生成任务
   */
  retryTestcaseTask(taskId: string): Promise<{ task_id: string; message: string }> {
    return api.post('/ai-tasks/testcase-generation/retry', { task_id: taskId })
  },

  /**
   * 获取任务统计
   */
  getStats(): Promise<{
    requirement_analysis: {
      total: number
      completed: number
      failed: number
      running: number
      pending: number
    }
    testcase_generation: {
      total: number
      completed: number
      failed: number
      running: number
      pending: number
    }
  }> {
    return api.get('/ai-tasks/stats')
  },
}

export default aiTasksApi
