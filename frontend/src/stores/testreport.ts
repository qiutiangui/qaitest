/**
 * 测试报告管理Store
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { TestReport, TestReportDetail, TestReportCreate, TestReportUpdate } from '@/types/testreport'
import testreportApi from '@/api/testreport'

export const useTestreportStore = defineStore('testreport', () => {
  const testreports = ref<TestReport[]>([])
  const currentTestreport = ref<TestReportDetail | null>(null)
  const total = ref(0)
  const loading = ref(false)

  async function fetchTestreports(params?: {
    page?: number
    page_size?: number
    project_id?: number
    version_id?: number
    status?: string
  }) {
    loading.value = true
    try {
      const res = await testreportApi.list(params)
      testreports.value = res.items
      total.value = res.total
    } finally {
      loading.value = false
    }
  }

  async function fetchTestreport(id: number) {
    loading.value = true
    try {
      currentTestreport.value = await testreportApi.get(id)
    } finally {
      loading.value = false
    }
  }

  async function createTestreport(data: TestReportCreate) {
    const testreport = await testreportApi.create(data)
    testreports.value.unshift(testreport)
    total.value++
    return testreport
  }

  async function updateTestreport(id: number, data: TestReportUpdate) {
    const testreport = await testreportApi.update(id, data)
    const index = testreports.value.findIndex(t => t.id === id)
    if (index !== -1) {
      testreports.value[index] = testreport
    }
    return testreport
  }

  async function deleteTestreport(id: number) {
    await testreportApi.delete(id)
    testreports.value = testreports.value.filter(t => t.id !== id)
    total.value--
  }

  async function exportTestreport(id: number, format: 'pdf' | 'html' | 'word' = 'pdf') {
    return await testreportApi.export(id, format)
  }

  return {
    testreports,
    currentTestreport,
    total,
    loading,
    fetchTestreports,
    fetchTestreport,
    createTestreport,
    updateTestreport,
    deleteTestreport,
    exportTestreport,
  }
})

export default useTestreportStore
