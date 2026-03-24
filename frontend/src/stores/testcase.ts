/**
 * 测试用例管理Store
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { TestCase, TestCaseCreate, TestCaseUpdate } from '@/types/testcase'
import testcaseApi from '@/api/testcase'

export const useTestcaseStore = defineStore('testcase', () => {
  const testcases = ref<TestCase[]>([])
  const currentTestcase = ref<TestCase | null>(null)
  const total = ref(0)
  const loading = ref(false)

  async function fetchTestcases(params?: {
    page?: number
    page_size?: number
    project_id?: number
    requirement_id?: number
    priority?: string
    status?: string
    keyword?: string
    ids?: number[]  // 新增：按ID列表获取
  }) {
    loading.value = true
    try {
      let res
      if (params?.ids && params.ids.length > 0) {
        // 根据ID列表获取
        const items = await testcaseApi.getByIds(params.ids)
        testcases.value = items
        total.value = items.length
      } else {
        res = await testcaseApi.list(params)
        testcases.value = res.items
        total.value = res.total
      }
    } finally {
      loading.value = false
    }
  }

  async function fetchTestcase(id: number) {
    loading.value = true
    try {
      currentTestcase.value = await testcaseApi.get(id)
    } finally {
      loading.value = false
    }
  }

  async function createTestcase(data: TestCaseCreate) {
    const testcase = await testcaseApi.create(data)
    testcases.value.unshift(testcase)
    total.value++
    return testcase
  }

  async function updateTestcase(id: number, data: TestCaseUpdate) {
    const testcase = await testcaseApi.update(id, data)
    const index = testcases.value.findIndex(t => t.id === id)
    if (index !== -1) {
      testcases.value[index] = testcase
    }
    return testcase
  }

  async function deleteTestcase(id: number) {
    await testcaseApi.delete(id)
    testcases.value = testcases.value.filter(t => t.id !== id)
    total.value--
  }

  return {
    testcases,
    currentTestcase,
    total,
    loading,
    fetchTestcases,
    fetchTestcase,
    createTestcase,
    updateTestcase,
    deleteTestcase,
  }
})

export default useTestcaseStore
