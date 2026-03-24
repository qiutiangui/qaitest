/**
 * 版本管理Store
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ProjectVersion, VersionCreate, VersionUpdate } from '@/types/version'
import versionApi from '@/api/version'

export const useVersionStore = defineStore('version', () => {
  const versions = ref<ProjectVersion[]>([])
  const currentVersion = ref<ProjectVersion | null>(null)
  const loading = ref(false)

  /**
   * 获取版本列表
   */
  async function fetchVersions(params?: { project_id?: number; status?: string }) {
    loading.value = true
    try {
      const res = await versionApi.list(params)
      versions.value = res.items
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取版本详情
   */
  async function fetchVersion(id: number) {
    loading.value = true
    try {
      currentVersion.value = await versionApi.get(id)
    } finally {
      loading.value = false
    }
  }

  /**
   * 创建版本
   */
  async function createVersion(data: VersionCreate) {
    const version = await versionApi.create(data)
    versions.value.unshift(version)
    return version
  }

  /**
   * 更新版本
   */
  async function updateVersion(id: number, data: VersionUpdate) {
    const version = await versionApi.update(id, data)
    const index = versions.value.findIndex(v => v.id === id)
    if (index !== -1) {
      versions.value[index] = version
    }
    if (currentVersion.value?.id === id) {
      currentVersion.value = version
    }
    return version
  }

  /**
   * 删除版本
   */
  async function deleteVersion(id: number) {
    await versionApi.delete(id)
    versions.value = versions.value.filter(v => v.id !== id)
  }

  /**
   * 发布版本
   */
  async function releaseVersion(id: number) {
    const res = await versionApi.release(id)
    const index = versions.value.findIndex(v => v.id === id)
    if (index !== -1) {
      versions.value[index] = res.version
    }
    return res.version
  }

  /**
   * 归档版本
   */
  async function archiveVersion(id: number) {
    const res = await versionApi.archive(id)
    const index = versions.value.findIndex(v => v.id === id)
    if (index !== -1) {
      versions.value[index] = res.version
    }
    return res.version
  }

  /**
   * 创建基线
   */
  async function createBaseline(id: number) {
    const snapshot = await versionApi.createBaseline(id)
    const index = versions.value.findIndex(v => v.id === id)
    if (index !== -1) {
      versions.value[index].is_baseline = true
    }
    return snapshot
  }

  /**
   * 获取版本统计信息
   */
  async function getVersionStats(id: number) {
    // 临时从API获取统计信息
    const res = await versionApi.get(id)
    return {
      requirement_count: 0,
      testcase_count: 0,
      testplan_count: 0,
      report_count: 0,
    }
  }

  return {
    versions,
    currentVersion,
    loading,
    fetchVersions,
    fetchVersion,
    createVersion,
    updateVersion,
    deleteVersion,
    releaseVersion,
    archiveVersion,
    createBaseline,
    getVersionStats,
  }
})

export default useVersionStore
