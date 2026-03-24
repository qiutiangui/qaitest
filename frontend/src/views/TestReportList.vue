<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { Plus, Trash2, Eye, Download } from 'lucide-vue-next'
import useTestreportStore from '@/stores/testreport'
import useTestplanStore from '@/stores/testplan'
import useProjectStore from '@/stores/project'
import { useRouter } from 'vue-router'
import { formatDateTime } from '@/utils/date'

const router = useRouter()
const testreportStore = useTestreportStore()
const testplanStore = useTestplanStore()
const projectStore = useProjectStore()

// 筛选条件
const selectedProject = ref<number | undefined>()
const selectedVersion = ref<number | undefined>()
const selectedStatus = ref<string | undefined>()

// 分页
const currentPage = ref(1)
const pageSize = ref(12)

// 创建报告弹窗
const showCreateDialog = ref(false)
const newReport = ref({
  title: '',
  test_plan_id: undefined as number | undefined,
  report_type: '执行报告',
  summary: '',
})

// 状态选项
const statuses = ['草稿', '已发布']

// 计算总页数
const totalPages = computed(() => Math.ceil(testreportStore.total / pageSize.value))

// 获取报告列表
async function fetchList() {
  await testreportStore.fetchTestreports({
    page: currentPage.value,
    page_size: pageSize.value,
    project_id: selectedProject.value,
    version_id: selectedVersion.value,
    status: selectedStatus.value,
  })
}

// 筛选变化
function handleFilterChange() {
  currentPage.value = 1
  fetchList()
}

// 分页变化
function handlePageChange(page: number) {
  currentPage.value = page
  fetchList()
}

// 打开创建报告弹窗
async function openCreateDialog() {
  await testplanStore.fetchTestplans({ page_size: 100, status: '已完成' })
  newReport.value = {
    title: '',
    test_plan_id: undefined,
    report_type: '执行报告',
    summary: '',
  }
  showCreateDialog.value = true
}

// 创建报告
async function handleCreate() {
  if (!newReport.value.title || !newReport.value.test_plan_id) {
    alert('请填写报告标题并选择测试计划')
    return
  }

  await testreportStore.createTestreport(newReport.value as any)
  showCreateDialog.value = false
  fetchList()
}

// 删除报告
async function deleteReport(id: number, title: string) {
  if (confirm(`确定要删除测试报告"${title}"吗？`)) {
    await testreportStore.deleteTestreport(id)
    fetchList()
  }
}

// 查看详情
function viewDetail(id: number) {
  router.push(`/testreports/${id}`)
}

// 导出报告
async function exportReport(id: number, format: 'html' | 'markdown' | 'csv') {
  // TODO: 调用导出API
  alert(`导出功能开发中，格式：${format}`)
}

// 获取状态颜色
function getStatusColor(status: string) {
  const colors: Record<string, string> = {
    '草稿': 'bg-gray-100 text-gray-700',
    '已发布': 'bg-green-100 text-green-700',
  }
  return colors[status] || 'bg-gray-100 text-gray-700'
}

onMounted(async () => {
  await projectStore.fetchProjects({ page_size: 100 })
  fetchList()
})
</script>

<template>
  <div class="testreport-list-page">
    <!-- 页面标题 -->
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-semibold text-text-primary">测试报告</h1>
      <button class="btn-primary flex items-center gap-2" @click="openCreateDialog">
        <Plus class="w-4 h-4" />
        生成报告
      </button>
    </div>

    <!-- 筛选区域 -->
    <div class="card mb-4">
      <div class="flex flex-wrap items-center gap-4">
        <!-- 项目筛选 -->
        <div class="flex items-center gap-2">
          <label class="text-sm text-text-secondary">项目：</label>
          <select
            v-model="selectedProject"
            class="input-field w-48"
            @change="handleFilterChange"
          >
            <option :value="undefined">全部项目</option>
            <option
              v-for="project in projectStore.projects"
              :key="project.id"
              :value="project.id"
            >
              {{ project.name }}
            </option>
          </select>
        </div>

        <!-- 状态筛选 -->
        <div class="flex items-center gap-2">
          <label class="text-sm text-text-secondary">状态：</label>
          <select
            v-model="selectedStatus"
            class="input-field w-32"
            @change="handleFilterChange"
          >
            <option :value="undefined">全部</option>
            <option v-for="s in statuses" :key="s" :value="s">{{ s }}</option>
          </select>
        </div>
      </div>
    </div>

    <!-- 报告卡片列表 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="report in testreportStore.testreports"
        :key="report.id"
        class="card hover:shadow-md transition-shadow group"
      >
        <div class="flex items-start justify-between mb-2">
          <h3 class="text-lg font-medium text-text-primary">{{ report.title }}</h3>
          <div class="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              class="text-primary hover:text-primary-light transition-colors"
              title="查看详情"
              @click.stop="viewDetail(report.id)"
            >
              <Eye class="w-4 h-4" />
            </button>
            <button
              class="text-functional-danger hover:text-red-600 transition-colors"
              title="删除"
              @click.stop="deleteReport(report.id, report.title)"
            >
              <Trash2 class="w-4 h-4" />
            </button>
          </div>
        </div>

        <div class="flex items-center gap-4 text-sm text-text-secondary mb-3">
          <span>总用例: {{ report.total_cases }}</span>
          <span class="text-green-600 font-medium">通过率: {{ report.pass_rate }}%</span>
        </div>

        <div class="mb-3">
          <div class="flex justify-between text-xs text-text-secondary mb-1">
            <span>执行进度</span>
            <span>{{ report.total_cases > 0 ? ((report.total_cases - report.not_executed_cases) / report.total_cases * 100).toFixed(1) : 0 }}%</span>
          </div>
          <div class="bg-gray-200 rounded-full h-2 flex overflow-hidden">
            <div
              class="bg-green-500 h-2"
              :style="{ width: `${report.total_cases > 0 ? report.passed_cases / report.total_cases * 100 : 0}%` }"
            />
            <div
              class="bg-red-500 h-2"
              :style="{ width: `${report.total_cases > 0 ? report.failed_cases / report.total_cases * 100 : 0}%` }"
            />
            <div
              class="bg-orange-500 h-2"
              :style="{ width: `${report.total_cases > 0 ? report.blocked_cases / report.total_cases * 100 : 0}%` }"
            />
          </div>
        </div>

        <div class="flex items-center justify-between">
          <span :class="['px-2 py-0.5 rounded text-xs font-medium', getStatusColor(report.status)]">
            {{ report.status }}
          </span>
          <span class="text-xs text-text-placeholder">
            {{ formatDateTime(report.created_at) }}
          </span>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div
      v-if="testreportStore.testreports.length === 0 && !testreportStore.loading"
      class="card text-center py-10 text-text-secondary"
    >
      暂无测试报告
    </div>

    <!-- 加载中 -->
    <div v-if="testreportStore.loading" class="card text-center py-10 text-text-secondary">
      加载中...
    </div>

    <!-- 分页 -->
    <div v-if="testreportStore.total > 0" class="flex items-center justify-between mt-6 px-2">
      <div class="text-sm text-text-secondary">共 {{ testreportStore.total }} 条记录</div>
      <div class="flex items-center gap-2">
        <button
          class="px-3 py-1 rounded border border-gray-300 text-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="currentPage === 1"
          @click="handlePageChange(currentPage - 1)"
        >
          上一页
        </button>

        <div class="flex items-center gap-1">
          <button
            v-for="page in Math.min(totalPages, 5)"
            :key="page"
            :class="[
              'px-3 py-1 rounded text-sm transition-colors',
              currentPage === page
                ? 'bg-primary text-white'
                : 'border border-gray-300 hover:bg-gray-50',
            ]"
            @click="handlePageChange(page)"
          >
            {{ page }}
          </button>
          <span v-if="totalPages > 5" class="text-text-secondary px-2">...</span>
          <button
            v-if="totalPages > 5"
            :class="[
              'px-3 py-1 rounded text-sm transition-colors',
              currentPage === totalPages
                ? 'bg-primary text-white'
                : 'border border-gray-300 hover:bg-gray-50',
            ]"
            @click="handlePageChange(totalPages)"
          >
            {{ totalPages }}
          </button>
        </div>

        <button
          class="px-3 py-1 rounded border border-gray-300 text-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="currentPage === totalPages"
          @click="handlePageChange(currentPage + 1)"
        >
          下一页
        </button>
      </div>
    </div>

    <!-- 创建报告弹窗 -->
    <div
      v-if="showCreateDialog"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      @click.self="showCreateDialog = false"
    >
      <div class="bg-white rounded-lg shadow-xl w-[500px]">
        <div class="p-6">
          <h2 class="text-xl font-semibold text-text-primary mb-4">生成测试报告</h2>

          <div class="space-y-4">
            <div>
              <label class="block text-sm text-text-secondary mb-1">报告标题 *</label>
              <input
                v-model="newReport.title"
                type="text"
                class="input-field"
                placeholder="请输入报告标题"
              />
            </div>

            <div>
              <label class="block text-sm text-text-secondary mb-1">测试计划 *</label>
              <select v-model="newReport.test_plan_id" class="input-field">
                <option :value="undefined">请选择测试计划</option>
                <option
                  v-for="plan in testplanStore.testplans"
                  :key="plan.id"
                  :value="plan.id"
                >
                  {{ plan.name }} ({{ plan.status }})
                </option>
              </select>
            </div>

            <div>
              <label class="block text-sm text-text-secondary mb-1">报告类型</label>
              <select v-model="newReport.report_type" class="input-field">
                <option value="执行报告">执行报告</option>
                <option value="每日报告">每日报告</option>
                <option value="周期报告">周期报告</option>
              </select>
            </div>

            <div>
              <label class="block text-sm text-text-secondary mb-1">摘要</label>
              <textarea
                v-model="newReport.summary"
                class="input-field h-20 resize-none"
                placeholder="请输入报告摘要"
              />
            </div>
          </div>

          <div class="flex items-center justify-end gap-2 mt-6">
            <button class="btn-secondary" @click="showCreateDialog = false">取消</button>
            <button class="btn-primary" @click="handleCreate">生成报告</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
