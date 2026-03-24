import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/ai-cases/generate',
  },
  {
    path: '/projects',
    name: 'ProjectList',
    component: () => import('@/views/ProjectList.vue'),
    meta: { title: '项目管理' },
  },
  // ============ 设置模块 ============
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings/index.vue'),
    redirect: '/settings/model',
    children: [
      {
        path: 'model',
        name: 'SettingsModel',
        component: () => import('@/views/Settings/ModelConfig.vue'),
        meta: { title: '模型配置' }
      },
      {
        path: 'prompt',
        name: 'SettingsPrompt',
        component: () => import('@/views/Settings/PromptManage.vue'),
        meta: { title: '提示词管理' }
      }
    ]
  },
  // ============ AI用例生成模块 ============
  {
    path: '/ai-cases',
    name: 'AICaseGeneration',
    component: () => import('@/views/AICaseGeneration/index.vue'),
    meta: { title: 'AI用例生成' },
    redirect: '/ai-cases/generate',
    children: [
      {
        path: 'generate',
        name: 'AICaseGenerate',
        component: () => import('@/views/AICaseGeneration/Generate.vue'),
        meta: { title: '用例生成' }
      },
      {
        path: 'task-records',
        name: 'AITest',
        component: () => import('@/views/AITest/AITestListPage.vue'),
        meta: { title: '任务记录' }
      },
      {
        path: 'task-records/:taskId',
        name: 'AITestDetail',
        component: () => import('@/views/AITest/AITestDetailPage.vue'),
        meta: { title: '任务详情' }
      },
      {
        path: 'function-points',
        name: 'AICaseFunctionPoints',
        component: () => import('@/views/AICaseGeneration/FunctionPoints.vue'),
        meta: { title: '需求管理' }
      },
      {
        path: 'test-cases',
        name: 'AICaseTestCases',
        component: () => import('@/views/AICaseGeneration/TestCases.vue'),
        meta: { title: '测试用例' }
      }
    ]
  },
  {
    path: '/requirements/:id',
    name: 'RequirementDetail',
    component: () => import('@/views/RequirementDetail.vue'),
    meta: { title: '功能点详情' },
  },
  {
    path: '/testplans',
    name: 'TestPlanList',
    component: () => import('@/views/TestPlanList.vue'),
    meta: { title: '测试计划' },
  },
  {
    path: '/testplans/:id',
    name: 'TestPlanDetail',
    component: () => import('@/views/TestPlanDetail.vue'),
    meta: { title: '测试计划详情' },
  },
  {
    path: '/testreports',
    name: 'TestReportList',
    component: () => import('@/views/TestReportList.vue'),
    meta: { title: '测试报告' },
  },
  {
    path: '/testreports/:id',
    name: 'TestReportDetail',
    component: () => import('@/views/TestReportDetail.vue'),
    meta: { title: '测试报告详情' },
  },
  {
    path: '/testcases/:id',
    name: 'TestCaseDetail',
    component: () => import('@/views/TestCaseDetail.vue'),
    meta: { title: '测试用例详情' },
  },
  {
    path: '/versions',
    name: 'VersionList',
    component: () => import('@/views/VersionList.vue'),
    meta: { title: '版本管理' },
  },
  {
    path: '/versions/:id',
    name: 'VersionDetail',
    component: () => import('@/views/VersionDetail.vue'),
    meta: { title: '版本详情' },
  },
  {
    path: '/versions/compare',
    name: 'VersionCompare',
    component: () => import('@/views/VersionCompare.vue'),
    meta: { title: '版本对比' },
  },
  // 旧路由重定向（兼容历史书签）
  {
    path: '/requirements/analysis',
    redirect: '/ai-cases/generate'
  },
  {
    path: '/testcases/generate',
    redirect: '/ai-cases/generate'
  },
  {
    path: '/requirements',
    redirect: '/ai-cases/function-points'
  },
  {
    path: '/testcases',
    redirect: '/ai-cases/test-cases'
  },
  // 旧任务路由重定向
  {
    path: '/ai-test',
    redirect: '/ai-cases/task-records'
  },
  {
    path: '/ai-test/:taskId',
    redirect: (to) => `/ai-cases/task-records/${to.params.taskId}`
  },
  {
    path: '/ai-tasks',
    redirect: '/ai-cases/task-records'
  },
  {
    path: '/tasks',
    redirect: '/ai-cases/task-records'
  },
  {
    path: '/tasks/:type/:taskId',
    redirect: (to) => `/ai-cases/task-records/${to.params.taskId}`
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  document.title = `${to.meta.title || 'qaitest'} - qaitest智测平台`
  next()
})

export default router
