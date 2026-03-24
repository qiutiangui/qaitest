/**
 * 版本管理相关类型定义
 */
export interface ProjectVersion {
  id: number
  project_id: number
  version_number: string
  version_name: string | null
  description: string | null
  status: string
  release_notes: string | null
  is_baseline: boolean
  created_by: string | null
  released_at: string | null
  created_at: string
  updated_at: string
}

export interface VersionCreate {
  version_number: string
  version_name?: string
  description?: string
  status?: string
  release_notes?: string
  project_id: number
}

export interface VersionUpdate {
  version_name?: string
  description?: string
  status?: string
  release_notes?: string
}

export interface VersionSnapshot {
  id: number
  version_id: number
  snapshot_type: string
  snapshot_data: Record<string, unknown>
  created_at: string
}

export interface VersionCompareResult {
  version_a: ProjectVersion
  version_b: ProjectVersion
  requirement_changes: Record<string, unknown>
  testcase_changes: Record<string, unknown>
  execution_changes: Record<string, unknown>
}
