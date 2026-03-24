/**
 * 测试计划管理Store
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { TestPlan, TestPlanDetail, TestPlanCreate, TestPlanUpdate } from '@/types/testplan'
import testplanApi from '@/api/testplan'

export const useTestplanStore = defineStore('testplan', () => {
  const testplans = ref<TestPlan[]>([])
  const currentTestplan = ref<TestPlanDetail | null>(null)
  const total = ref(0)
  const loading = ref(false)

  async function fetchTestplans(params?: {
    page?: number
    page_size?: number
    project_id?: number
    version_id?: number
    status?: string
  }) {
    loading.value = true
    try {
      const res = await testplanApi.list(params)
      testplans.value = res.items
      total.value = res.total
    } finally {
      loading.value = false
    }
  }

  async function fetchTestplan(id: number) {
    loading.value = true
    try {
      currentTestplan.value = await testplanApi.get(id)
    } finally {
      loading.value = false
    }
  }

  async function createTestplan(data: TestPlanCreate) {
    const testplan = await testplanApi.create(data)
    testplans.value.unshift(testplan)
    total.value++
    return testplan
  }

  async function updateTestplan(id: number, data: TestPlanUpdate) {
    const testplan = await testplanApi.update(id, data)
    const index = testplans.value.findIndex(t => t.id === id)
    if (index !== -1) {
      testplans.value[index] = testplan
    }
    return testplan
  }

  async function deleteTestplan(id: number) {
    await testplanApi.delete(id)
    testplans.value = testplans.value.filter(t => t.id !== id)
    total.value--
  }

  async function addCasesToPlan(planId: number, testcaseIds: number[]) {
    return await testplanApi.addCases(planId, testcaseIds)
  }

  async function updateExecutionStatus(
    planId: number,
    testcaseId: number,
    executionStatus: string,
    executor?: string,
    notes?: string
  ) {
    return await testplanApi.updateExecutionStatus(planId, testcaseId, {
      execution_status: executionStatus,
      executor,
      notes,
    })
  }

  return {
    testplans,
    currentTestplan,
    total,
    loading,
    fetchTestplans,
    fetchTestplan,
    createTestplan,
    updateTestplan,
    deleteTestplan,
    addCasesToPlan,
    updateExecutionStatus,
  }
})

export default useTestplanStore
