/**
 * 测试用例管理API
 */
import api from './index'
import type { TestCase, TestCaseCreate, TestCaseUpdate, TestCaseListResponse } from '@/types/testcase'

export const testcaseApi = {
  /**
   * 获取用例列表
   */
  list(params?: {
    page?: number
    page_size?: number
    project_id?: number
    requirement_id?: number
    priority?: string
    status?: string
    keyword?: string
  }): Promise<TestCaseListResponse> {
    return api.get('/testcases', { params })
  },

  /**
   * 获取用例详情
   */
  get(id: number): Promise<TestCase> {
    return api.get(`/testcases/${id}`)
  },

  /**
   * 根据ID列表获取用例
   */
  getByIds(ids: number[]): Promise<TestCase[]> {
    return api.post('/testcases/by-ids', { ids })
  },

  /**
   * 创建用例
   */
  create(data: TestCaseCreate): Promise<TestCase> {
    return api.post('/testcases', data)
  },

  /**
   * 更新用例
   */
  update(id: number, data: TestCaseUpdate): Promise<TestCase> {
    return api.put(`/testcases/${id}`, data)
  },

  /**
   * 删除用例
   */
  delete(id: number): Promise<void> {
    return api.delete(`/testcases/${id}`)
  },

  /**
   * 批量删除用例
   */
  batchDelete(ids: number[]): Promise<{ message: string; deleted_count: number }> {
    return api.post('/testcases/batch-delete', ids)
  },

  /**
   * 生成测试用例
   */
  generate(data: {
    project_id: number
    requirement_ids: number[]
    version_id?: number
    task_id?: string
    llm_config?: {
      testcase_generate_model?: {
        provider: string
        model?: string
        api_key?: string
        base_url?: string
        custom_id?: number
      }
      testcase_review_model?: {
        provider: string
        model?: string
        api_key?: string
        base_url?: string
        custom_id?: number
      }
    }
  }): Promise<{ task_id: string; message: string }> {
    return api.post('/testcases/generate', data)
  },

  /**
   * 获取项目用例统计
   */
  getStats(projectId: number): Promise<{
    project_id: number
    total: number
    by_priority: Record<string, number>
    by_type: Record<string, number>
  }> {
    return api.get(`/testcases/stats/project/${projectId}`)
  },

  /**
   * 导出测试用例（根据任务ID）
   */
  export(taskId: string, format: 'excel' | 'markdown' = 'excel'): Promise<{
    data?: any[]
    content?: string
    format: string
  }> {
    return api.get(`/testcases/export/${taskId}`, { params: { format } })
  },
}

export default testcaseApi
