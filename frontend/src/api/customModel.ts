/**
 * 前端模型配置API
 */
import api from './index'

export interface CustomModel {
  id: number
  name: string
  display_name: string
  base_url: string
  default_model: string
  description?: string
  enabled: boolean
  created_at: string
  updated_at?: string
}

export interface CustomModelCreate {
  name: string
  display_name: string
  base_url: string
  api_key: string
  default_model: string
  description?: string
}

export interface TestConnectionResult {
  success: boolean
  message: string
  response?: string
}

export const customModelApi = {
  /**
   * 获取自定义模型列表
   */
  list: () => {
    return api.get<CustomModel[]>("/models/custom/")
  },

  /**
   * 创建自定义模型
   */
  create: (data: CustomModelCreate) => {
    return api.post<CustomModel>("/models/custom/", data)
  },

  /**
   * 更新自定义模型
   */
  update: (id: number, data: Partial<CustomModelCreate>) => {
    return api.put<CustomModel>(`/models/custom/${id}`, data)
  },

  /**
   * 删除自定义模型
   */
  delete: (id: number) => {
    return api.delete(`/models/custom/${id}`)
  },

  /**
   * 启用/禁用模型
   */
  toggle: (id: number) => {
    return api.post(`/models/custom/${id}/toggle`)
  },

  /**
   * 测试模型连接
   */
  test: (id: number) => {
    return api.post<TestConnectionResult>(`/models/custom/${id}/test`)
  },

  /**
   * 测试连接（创建前）
   */
  testConnection: (data: CustomModelCreate) => {
    return api.post<TestConnectionResult>("/models/custom/test-connection", data)
  },

  /**
   * 获取所有可用模型（包括内置和自定义）
   */
  getAllAvailable: () => {
    return api.get("/models/custom/all/available")
  }
}
