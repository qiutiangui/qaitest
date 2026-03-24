/**
 * 测试报告管理API
 */
import api from './index'
import type { 
  TestReport, 
  TestReportDetail, 
  TestReportCreate, 
  TestReportUpdate,
  TestReportListResponse 
} from '@/types/testreport'

export const testreportApi = {
  /**
   * 获取报告列表
   */
  list(params?: {
    page?: number
    page_size?: number
    project_id?: number
    version_id?: number
    status?: string
  }): Promise<TestReportListResponse> {
    return api.get('/testreports', { params })
  },

  /**
   * 获取报告详情
   */
  get(id: number): Promise<TestReportDetail> {
    return api.get(`/testreports/${id}`)
  },

  /**
   * 创建报告
   */
  create(data: TestReportCreate): Promise<TestReport> {
    return api.post('/testreports', data)
  },

  /**
   * 更新报告
   */
  update(id: number, data: TestReportUpdate): Promise<TestReport> {
    return api.put(`/testreports/${id}`, data)
  },

  /**
   * 删除报告
   */
  delete(id: number): Promise<void> {
    return api.delete(`/testreports/${id}`)
  },

  /**
   * 导出报告
   */
  export(id: number, format: 'pdf' | 'html' | 'word' = 'pdf'): Promise<{ message: string }> {
    return api.get(`/testreports/${id}/export`, { params: { format } })
  },
}

export default testreportApi
