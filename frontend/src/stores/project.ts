/**
 * 项目管理Store
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Project, ProjectCreate, ProjectUpdate } from '@/types/project'
import projectApi from '@/api/project'

export const useProjectStore = defineStore('project', () => {
  const projects = ref<Project[]>([])
  const currentProject = ref<Project | null>(null)
  const total = ref(0)
  const loading = ref(false)

  /**
   * 获取项目列表
   */
  async function fetchProjects(params?: {
    page?: number
    page_size?: number
    keyword?: string
    status?: string
  }) {
    loading.value = true
    try {
      const res = await projectApi.list(params)
      projects.value = res.items
      total.value = res.total
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取项目详情
   */
  async function fetchProject(id: number) {
    loading.value = true
    try {
      currentProject.value = await projectApi.get(id)
    } finally {
      loading.value = false
    }
  }

  /**
   * 创建项目
   */
  async function createProject(data: ProjectCreate) {
    const project = await projectApi.create(data)
    projects.value.unshift(project)
    total.value++
    return project
  }

  /**
   * 更新项目
   */
  async function updateProject(id: number, data: ProjectUpdate) {
    const project = await projectApi.update(id, data)
    const index = projects.value.findIndex(p => p.id === id)
    if (index !== -1) {
      projects.value[index] = project
    }
    if (currentProject.value?.id === id) {
      currentProject.value = project
    }
    return project
  }

  /**
   * 删除项目
   */
  async function deleteProject(id: number) {
    await projectApi.delete(id)
    projects.value = projects.value.filter(p => p.id !== id)
    total.value--
  }

  return {
    projects,
    currentProject,
    total,
    loading,
    fetchProjects,
    fetchProject,
    createProject,
    updateProject,
    deleteProject,
  }
})

export default useProjectStore
