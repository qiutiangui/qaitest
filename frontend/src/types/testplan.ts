/**
 * 测试计划相关类型定义
 */
export interface TestPlanCase {
  id: number
  test_plan_id: number
  test_case_id: number
  execution_status: string
  executed_at: string | null
  executor: string | null
  notes: string | null
}

export interface TestPlan {
  id: number
  project_id: number
  version_id: number | null
  name: string
  description: string | null
  status: string
  start_time: string | null
  end_time: string | null
  created_at: string
}

export interface TestPlanDetail extends TestPlan {
  test_plan_cases?: TestPlanCase[]
  total_cases: number
  passed_cases: number
  failed_cases: number
  blocked_cases: number
  not_executed_cases: number
  pass_rate: number
}

export interface TestPlanCreate {
  name: string
  project_id: number
  version_id?: number
  description?: string
  status?: string
  start_time?: string
  end_time?: string
}

export interface TestPlanUpdate {
  name?: string
  description?: string
  status?: string
  start_time?: string
  end_time?: string
}

export interface ExecutionStatusUpdate {
  execution_status: string
  executor?: string
  notes?: string
}

export interface TestPlanListResponse {
  total: number
  items: TestPlan[]
}
