/**
 * 功能点（需求）相关类型定义
 */
export interface Requirement {
  id: number
  project_id: number
  version_id: number | null
  name: string
  description: string | null
  category: string | null
  module: string | null
  priority: string | null
  acceptance_criteria: string | null
  keywords: string | null
  created_at: string
  updated_at: string | null
}

export interface RequirementCreate {
  name: string
  project_id: number
  version_id?: number
  description?: string
  category?: string
  module?: string
  priority?: string
  acceptance_criteria?: string
  keywords?: string
}

export interface RequirementUpdate {
  name?: string
  description?: string
  category?: string
  module?: string
  priority?: string
  acceptance_criteria?: string
  keywords?: string
}

export interface RequirementListResponse {
  total: number
  items: Requirement[]
}
