/**
 * 测试计划管理API
 */
import api from './index'
import type { 
  TestPlan, 
  TestPlanDetail, 
  TestPlanCreate, 
  TestPlanUpdate,
  ExecutionStatusUpdate,
  TestPlanListResponse 
} from '@/types/testplan'

export const testplanApi = {
  /**
   * 获取计划列表
   */
  list(params?: {
    page?: number
    page_size?: number
    project_id?: number
    version_id?: number
    status?: string
  }): Promise<TestPlanListResponse> {
    return api.get('/testplans', { params })
  },

  /**
   * 获取计划详情
   */
  get(id: number): Promise<TestPlanDetail> {
    return api.get(`/testplans/${id}`)
  },

  /**
   * 创建计划
   */
  create(data: TestPlanCreate): Promise<TestPlan> {
    return api.post('/testplans', data)
  },

  /**
   * 更新计划
   */
  update(id: number, data: TestPlanUpdate): Promise<TestPlan> {
    return api.put(`/testplans/${id}`, data)
  },

  /**
   * 删除计划
   */
  delete(id: number): Promise<void> {
    return api.delete(`/testplans/${id}`)
  },

  /**
   * 批量添加用例到计划
   */
  addCases(planId: number, testcaseIds: number[]): Promise<{ message: string }> {
    return api.post(`/testplans/${planId}/cases`, testcaseIds)
  },

  /**
   * 更新执行状态
   */
  updateExecutionStatus(
    planId: number, 
    testcaseId: number, 
    data: ExecutionStatusUpdate
  ): Promise<{ message: string }> {
    return api.put(`/testplans/${planId}/cases/${testcaseId}`, data)
  },
}

export default testplanApi
