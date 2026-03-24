/**
 * 功能点管理API
 */
import api from './index'
import type { Requirement, RequirementCreate, RequirementUpdate, RequirementListResponse } from '@/types/requirement'

export const requirementApi = {
  /**
   * 获取功能点列表
   */
  list(params?: {
    page?: number
    page_size?: number
    project_id?: number
    version_id?: number
    category?: string
    priority?: string
    keyword?: string
    sort_by?: string
    order?: 'asc' | 'desc'
  }): Promise<RequirementListResponse> {
    return api.get('/requirements', { params })
  },

  /**
   * 获取功能点详情
   */
  get(id: number): Promise<Requirement> {
    return api.get(`/requirements/${id}`)
  },

  /**
   * 根据ID列表获取功能点
   */
  getByIds(ids: number[]): Promise<Requirement[]> {
    return api.post('/requirements/by-ids', { ids })
  },

  /**
   * 创建功能点
   */
  create(data: RequirementCreate): Promise<Requirement> {
    return api.post('/requirements', data)
  },

  /**
   * 更新功能点
   */
  update(id: number, data: RequirementUpdate): Promise<Requirement> {
    return api.put(`/requirements/${id}`, data)
  },

  /**
   * 删除功能点
   */
  delete(id: number, deleteTestcases: boolean = false): Promise<{ message: string; deleted_testcase_count?: number }> {
    return api.delete(`/requirements/${id}`, { params: { delete_testcases: deleteTestcases } })
  },

  /**
   * 批量删除功能点
   */
  batchDelete(ids: number[], deleteTestcases: boolean = false): Promise<{ message: string; deleted_count: number; deleted_testcase_count?: number }> {
    return api.post('/requirements/batch-delete', { ids, delete_testcases: deleteTestcases })
  },

  /**
   * 分析需求文档
   */
  analyze(formData: FormData, modelConfig?: {
    requirement_analyze_model?: { provider: string; custom_id?: number; model?: string }
  }): Promise<{ task_id: string; message: string }> {
    // 如果有模型配置，添加到 formData
    if (modelConfig?.requirement_analyze_model) {
      formData.append('llm_config', JSON.stringify({
        requirement_analyze_model: modelConfig.requirement_analyze_model
      }))
    }
    return api.post('/requirements/analyze', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },

  /**
   * 批量分析多个需求文档（并行处理）
   */
  analyzeMultiple(
    files: File[],
    requirementName: string,
    projectId?: number,
    versionId?: number,
    modelConfig?: {
      requirement_analyze_model?: { provider: string; custom_id?: number; model?: string }
    }
  ): Promise<{ task_id: string; total_files: number; message: string }> {
    const formData = new FormData()

    // 添加多个文件
    files.forEach((file, index) => {
      formData.append(`files`, file)
    })

    formData.append('requirement_name', requirementName)

    if (projectId) {
      formData.append('project_id', projectId.toString())
    }

    if (versionId) {
      formData.append('version_id', versionId.toString())
    }

    // 添加模型配置
    if (modelConfig?.requirement_analyze_model) {
      formData.append('llm_config', JSON.stringify({
        requirement_analyze_model: modelConfig.requirement_analyze_model
      }))
    }

    return api.post('/requirements/analyze-multiple', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },

  /**
   * 获取项目功能点统计
   */
  getStats(projectId: number): Promise<{
    project_id: number
    total: number
    by_category: Record<string, number>
    by_priority: Record<string, number>
  }> {
    return api.get(`/requirements/stats/project/${projectId}`)
  },

  /**
   * 导出功能点（根据任务ID）
   */
  export(taskId: string): Promise<{
    data: any[]
    format: string
  }> {
    return api.get(`/requirements/export/${taskId}`)
  },
}

export default requirementApi
