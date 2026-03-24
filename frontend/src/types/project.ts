/**
 * 项目相关类型定义
 */
export interface Project {
  id: number
  name: string
  description: string | null
  status: string
  created_at: string
  updated_at: string
}

export interface ProjectCreate {
  name: string
  description?: string
  status?: string
}

export interface ProjectUpdate {
  name?: string
  description?: string
  status?: string
}

export interface ProjectListResponse {
  total: number
  items: Project[]
}
