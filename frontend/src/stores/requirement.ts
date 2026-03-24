/**
 * 功能点管理Store
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Requirement, RequirementCreate, RequirementUpdate } from '@/types/requirement'
import requirementApi from '@/api/requirement'

export const useRequirementStore = defineStore('requirement', () => {
  const requirements = ref<Requirement[]>([])
  const currentRequirement = ref<Requirement | null>(null)
  const total = ref(0)
  const loading = ref(false)

  async function fetchRequirements(params?: {
    page?: number
    page_size?: number
    project_id?: number
    version_id?: number
    category?: string
    priority?: string
    keyword?: string
    sort_by?: string
    order?: 'asc' | 'desc'
  }) {
    loading.value = true
    try {
      const res = await requirementApi.list(params)
      requirements.value = res.items
      total.value = res.total
    } finally {
      loading.value = false
    }
  }

  async function fetchRequirement(id: number) {
    loading.value = true
    try {
      currentRequirement.value = await requirementApi.get(id)
    } finally {
      loading.value = false
    }
  }

  async function createRequirement(data: RequirementCreate) {
    const requirement = await requirementApi.create(data)
    requirements.value.unshift(requirement)
    total.value++
    return requirement
  }

  async function updateRequirement(id: number, data: RequirementUpdate) {
    const requirement = await requirementApi.update(id, data)
    const index = requirements.value.findIndex(r => r.id === id)
    if (index !== -1) {
      requirements.value[index] = requirement
    }
    return requirement
  }

  async function deleteRequirement(id: number, deleteTestcases: boolean = false) {
    const result = await requirementApi.delete(id, deleteTestcases)
    requirements.value = requirements.value.filter(r => r.id !== id)
    total.value--
    return result
  }

  async function batchDeleteRequirements(ids: number[], deleteTestcases: boolean = false) {
    const result = await requirementApi.batchDelete(ids, deleteTestcases)
    requirements.value = requirements.value.filter(r => !ids.includes(r.id))
    total.value -= ids.length
    return result
  }

  return {
    requirements,
    currentRequirement,
    total,
    loading,
    fetchRequirements,
    fetchRequirement,
    createRequirement,
    updateRequirement,
    deleteRequirement,
    batchDeleteRequirements,
  }
})

export default useRequirementStore
