/**
 * 测试报告相关类型定义
 */
export interface TestReport {
  id: number
  test_plan_id: number
  project_id: number
  version_id: number | null
  title: string
  report_type: string
  summary: string | null
  total_cases: number
  passed_cases: number
  failed_cases: number
  blocked_cases: number
  not_executed_cases: number
  pass_rate: number
  start_time: string | null
  end_time: string | null
  status: string
  created_by: string | null
  created_at: string
}

export interface TestReportDetail extends TestReport {
  execution_details?: {
    testcase_id: number
    title: string | null
    execution_status: string
    executor: string | null
    executed_at: string | null
    notes: string | null
  }[]
}

export interface TestReportCreate {
  title: string
  test_plan_id: number
  report_type?: string
  summary?: string
}

export interface TestReportUpdate {
  title?: string
  summary?: string
  status?: string
}

export interface TestReportListResponse {
  total: number
  items: TestReport[]
}
