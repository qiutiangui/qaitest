/**
 * 版本管理API
 */
import api from './index'
import type { 
  ProjectVersion, 
  VersionCreate, 
  VersionUpdate, 
  VersionSnapshot,
  VersionCompareResult 
} from '@/types/version'

export const versionApi = {
  /**
   * 获取版本列表
   */
  list(params?: { project_id?: number; status?: string }): Promise<{ items: ProjectVersion[] }> {
    return api.get('/versions', { params })
  },

  /**
   * 获取版本详情
   */
  get(id: number): Promise<ProjectVersion> {
    return api.get(`/versions/${id}`)
  },

  /**
   * 创建版本
   */
  create(data: VersionCreate): Promise<ProjectVersion> {
    return api.post('/versions', data)
  },

  /**
   * 更新版本
   */
  update(id: number, data: VersionUpdate): Promise<ProjectVersion> {
    return api.put(`/versions/${id}`, data)
  },

  /**
   * 删除版本
   */
  delete(id: number): Promise<void> {
    return api.delete(`/versions/${id}`)
  },

  /**
   * 发布版本
   */
  release(id: number): Promise<{ message: string; version: ProjectVersion }> {
    return api.post(`/versions/${id}/release`)
  },

  /**
   * 归档版本
   */
  archive(id: number): Promise<{ message: string; version: ProjectVersion }> {
    return api.post(`/versions/${id}/archive`)
  },

  /**
   * 创建快照
   */
  createSnapshot(id: number, snapshotType: string): Promise<VersionSnapshot> {
    return api.post(`/versions/${id}/snapshot`, null, { params: { snapshot_type: snapshotType } })
  },

  /**
   * 获取快照列表
   */
  getSnapshots(id: number): Promise<{ items: VersionSnapshot[] }> {
    return api.get(`/versions/${id}/snapshot`)
  },

  /**
   * 版本对比
   */
  compare(versionAId: number, versionBId: number): Promise<VersionCompareResult> {
    return api.get(`/versions/compare/${versionAId}/${versionBId}`)
  },

  /**
   * 创建基线
   */
  createBaseline(id: number): Promise<VersionSnapshot> {
    return api.post(`/versions/${id}/baseline`)
  },

  /**
   * 版本回溯
   */
  rollback(id: number): Promise<{ message: string; version_id: number }> {
    return api.post(`/versions/${id}/rollback`)
  },

  /**
   * 获取变更日志
   */
  getChangelog(id: number): Promise<{ version_id: number; version_number: string; entries: any[] }> {
    return api.get(`/versions/${id}/changelog`)
  },
}

export default versionApi
