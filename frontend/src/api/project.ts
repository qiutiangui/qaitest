/**
 * 项目管理API
 */
import api from './index'
import type { Project, ProjectCreate, ProjectUpdate, ProjectListResponse } from '@/types/project'

export const projectApi = {
  /**
   * 获取项目列表
   */
  list(params?: {
    page?: number
    page_size?: number
    keyword?: string
    status?: string
  }): Promise<ProjectListResponse> {
    return api.get('/projects', { params })
  },

  /**
   * 获取项目详情
   */
  get(id: number): Promise<Project> {
    return api.get(`/projects/${id}`)
  },

  /**
   * 创建项目
   */
  create(data: ProjectCreate): Promise<Project> {
    return api.post('/projects', data)
  },

  /**
   * 更新项目
   */
  update(id: number, data: ProjectUpdate): Promise<Project> {
    return api.put(`/projects/${id}`, data)
  },

  /**
   * 删除项目
   */
  delete(id: number): Promise<void> {
    return api.delete(`/projects/${id}`)
  },
}

export default projectApi
