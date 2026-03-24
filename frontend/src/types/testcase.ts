/**
 * 测试用例相关类型定义
 */
export interface TestStep {
  id: number
  test_case_id: number
  step_number: number
  description: string
  expected_result: string | null
  created_at: string
}

export interface TestCase {
  id: number
  project_id: number
  requirement_id: number | null
  requirement_name: string | null
  version_id: number | null
  title: string
  description: string | null
  priority: string | null
  status: string
  test_type: string | null
  preconditions: string | null
  test_data: string | null
  creator: string
  created_at: string
  steps?: TestStep[]
}

export interface TestCaseCreate {
  title: string
  project_id: number
  requirement_id?: number
  version_id?: number
  description?: string
  priority?: string
  status?: string
  test_type?: string
  preconditions?: string
  postconditions?: string
  steps?: {
    step_number: number
    description: string
    expected_result?: string
  }[]
}

export interface TestCaseUpdate {
  title?: string
  description?: string
  priority?: string
  status?: string
  test_type?: string
  preconditions?: string
  test_data?: string
}

export interface TestCaseListResponse {
  total: number
  items: TestCase[]
}
