<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Download, FileText, FileSpreadsheet, File, Target, TrendingUp, CheckCircle, XCircle, AlertCircle, PieChart, Edit, Delete, Save, X } from 'lucide-vue-next'
import { ElMessage, ElMessageBox } from 'element-plus'
import useTestreportStore from '@/stores/testreport'
import DetailHeader from '@/components/detail/DetailHeader.vue'
import DetailCard from '@/components/detail/DetailCard.vue'
import EditableField from '@/components/detail/EditableField.vue'
import StatusBadge from '@/components/detail/StatusBadge.vue'

const route = useRoute()
const router = useRouter()
const testreportStore = useTestreportStore()

// 报告ID
const reportId = computed(() => Number(route.params.id))

// 编辑模式
const isEditing = ref(false)
const formData = ref({
  title: '',
  summary: ''
})

// 报告详情
const reportDetail = computed(() => testreportStore.currentTestreport)

// 导出格式选择弹窗
const showExportDialog = ref(false)
const exportFormat = ref<'html' | 'markdown' | 'csv'>('html')
const exporting = ref(false)

// 统计数据
const stats = computed(() => {
  if (!reportDetail.value) return null
  
  const total = reportDetail.value.total_cases
  const passed = reportDetail.value.passed_cases
  const failed = reportDetail.value.failed_cases
  const blocked = reportDetail.value.blocked_cases
  const notExecuted = reportDetail.value.not_executed_cases
  const passRate = reportDetail.value.pass_rate
  
  return {
    total,
    passed,
    failed,
    blocked,
    notExecuted,
    passRate,
    executedRate: total > 0 ? ((total - notExecuted) / total * 100).toFixed(1) : 0,
  }
})

// 执行状态统计
const statusStats = computed(() => {
  if (!stats.value) return []
  
  return [
    { label: '通过', value: stats.value.passed, color: '#10B981', bgColor: 'bg-green-500' },
    { label: '失败', value: stats.value.failed, color: '#EF4444', bgColor: 'bg-red-500' },
    { label: '阻塞', value: stats.value.blocked, color: '#F59E0B', bgColor: 'bg-orange-500' },
    { label: '未执行', value: stats.value.notExecuted, color: '#9CA3AF', bgColor: 'bg-gray-400' },
  ]
})

// 获取报告详情
async function fetchDetail() {
  await testreportStore.fetchTestreport(reportId.value)
}

// 开始编辑
function handleEdit() {
  if (!reportDetail.value) return
  isEditing.value = true
  formData.value = {
    title: reportDetail.value.title || '',
    summary: reportDetail.value.summary || ''
  }
}

// 取消编辑
function handleCancel() {
  isEditing.value = false
  formData.value = {
    title: '',
    summary: ''
  }
}

// 保存
async function handleSave() {
  if (!reportDetail.value) return
  
  try {
    await testreportStore.updateTestreport(reportId.value, formData.value)
    ElMessage.success('保存成功')
    isEditing.value = false
    await fetchDetail()
  } catch {
    ElMessage.error('保存失败')
  }
}

// 删除
async function handleDelete() {
  if (!reportDetail.value) return
  
  try {
    await ElMessageBox.confirm(
      `确定要删除测试报告「${reportDetail.value.title}」吗？`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await testreportStore.deleteTestreport(reportDetail.value.id)
    ElMessage.success('删除成功')
    router.push('/testreports')
  } catch {
    // 用户取消
  }
}

// 打开导出弹窗
function openExportDialog() {
  exportFormat.value = 'html'
  showExportDialog.value = true
}

// 导出报告
async function handleExport() {
  exporting.value = true
  try {
    // 简单实现：生成HTML报告
    if (exportFormat.value === 'html') {
      const htmlContent = generateHTMLReport()
      downloadFile(htmlContent, `测试报告_${reportDetail.value?.title}.html`, 'text/html')
    } else if (exportFormat.value === 'markdown') {
      const mdContent = generateMarkdownReport()
      downloadFile(mdContent, `测试报告_${reportDetail.value?.title}.md`, 'text/markdown')
    } else if (exportFormat.value === 'csv') {
      const csvContent = generateCSVReport()
      downloadFile(csvContent, `测试报告_${reportDetail.value?.title}.csv`, 'text/csv')
    }
    
    showExportDialog.value = false
  } catch (error) {
    console.error('导出失败:', error)
    alert('导出失败')
  } finally {
    exporting.value = false
  }
}

// 生成HTML报告
function generateHTMLReport(): string {
  if (!reportDetail.value || !stats.value) return ''
  
  return `
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>测试报告 - ${reportDetail.value.title}</title>
  <style>
    body { font-family: system-ui, -apple-system, sans-serif; padding: 40px; max-width: 1200px; margin: 0 auto; }
    h1 { color: #1f2937; border-bottom: 2px solid #3b82f6; padding-bottom: 10px; }
    .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin: 30px 0; }
    .stat-card { background: #f3f4f6; padding: 20px; border-radius: 8px; text-align: center; }
    .stat-value { font-size: 32px; font-weight: bold; margin-bottom: 5px; }
    .stat-label { color: #6b7280; }
    table { width: 100%; border-collapse: collapse; margin-top: 30px; }
    th, td { border: 1px solid #e5e7eb; padding: 12px; text-align: left; }
    th { background: #f9fafb; font-weight: 600; }
    .status-pass { color: #10b981; font-weight: 600; }
    .status-fail { color: #ef4444; font-weight: 600; }
    .status-block { color: #f59e0b; font-weight: 600; }
    .status-pending { color: #9ca3af; }
  </style>
</head>
<body>
  <h1>${reportDetail.value.title}</h1>
  
  <div class="stats">
    <div class="stat-card">
      <div class="stat-value">${stats.value.total}</div>
      <div class="stat-label">总用例数</div>
    </div>
    <div class="stat-card">
      <div class="stat-value" style="color: #10b981;">${stats.value.passed}</div>
      <div class="stat-label">通过</div>
    </div>
    <div class="stat-card">
      <div class="stat-value" style="color: #ef4444;">${stats.value.failed}</div>
      <div class="stat-label">失败</div>
    </div>
    <div class="stat-card">
      <div class="stat-value" style="color: #3b82f6;">${stats.value.passRate}%</div>
      <div class="stat-label">通过率</div>
    </div>
  </div>
  
  <h2>执行详情</h2>
  <table>
    <thead>
      <tr>
        <th>用例ID</th>
        <th>标题</th>
        <th>执行状态</th>
        <th>执行人</th>
        <th>备注</th>
      </tr>
    </thead>
    <tbody>
      ${reportDetail.value.execution_details?.map(detail => `
        <tr>
          <td>${detail.testcase_id}</td>
          <td>${detail.title || '-'}</td>
          <td class="status-${detail.execution_status === '通过' ? 'pass' : detail.execution_status === '失败' ? 'fail' : detail.execution_status === '阻塞' ? 'block' : 'pending'}">${detail.execution_status}</td>
          <td>${detail.executor || '-'}</td>
          <td>${detail.notes || '-'}</td>
        </tr>
      `).join('') || ''}
    </tbody>
  </table>
</body>
</html>
  `.trim()
}

// 生成Markdown报告
function generateMarkdownReport(): string {
  if (!reportDetail.value || !stats.value) return ''
  
  const lines = [
    `# 测试报告 - ${reportDetail.value.title}`,
    '',
    '## 执行概况',
    '',
    `- 总用例数：${stats.value.total}`,
    `- 通过：${stats.value.passed}`,
    `- 失败：${stats.value.failed}`,
    `- 阻塞：${stats.value.blocked}`,
    `- 未执行：${stats.value.notExecuted}`,
    `- 通过率：${stats.value.passRate}%`,
    '',
    '## 执行详情',
    '',
    '| 用例ID | 标题 | 执行状态 | 执行人 | 备注 |',
    '|--------|------|----------|--------|------|',
  ]
  
  reportDetail.value.execution_details?.forEach(detail => {
    lines.push(`| ${detail.testcase_id} | ${detail.title || '-'} | ${detail.execution_status} | ${detail.executor || '-'} | ${detail.notes || '-'} |`)
  })
  
  return lines.join('\n')
}

// 生成CSV报告
function generateCSVReport(): string {
  if (!reportDetail.value) return ''
  
  const lines = [
    '用例ID,标题,执行状态,执行人,备注',
  ]
  
  reportDetail.value.execution_details?.forEach(detail => {
    lines.push(`${detail.testcase_id},"${detail.title || ''}",${detail.execution_status},"${detail.executor || ''}","${detail.notes || ''}"`)
  })
  
  return '\ufeff' + lines.join('\n')
}

// 下载文件
function downloadFile(content: string, filename: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

// 获取执行状态样式
function getStatusStyle(status: string) {
  const styles: Record<string, { color: string; bgColor: string }> = {
    '未执行': { color: 'text-gray-600', bgColor: 'bg-gray-100' },
    '通过': { color: 'text-green-600', bgColor: 'bg-green-100' },
    '失败': { color: 'text-red-600', bgColor: 'bg-red-100' },
    '阻塞': { color: 'text-orange-600', bgColor: 'bg-orange-100' },
  }
  return styles[status] || styles['未执行']
}

// 获取状态颜色
function getStatusColor(status: string) {
  const colors: Record<string, string> = {
    '草稿': 'bg-gray-100 text-gray-700',
    '已发布': 'bg-green-100 text-green-700',
  }
  return colors[status] || 'bg-gray-100 text-gray-700'
}

onMounted(() => {
  fetchDetail()
})
</script>

<template>
  <div class="testreport-detail-page p-6 max-w-7xl mx-auto">
    <!-- 加载中 -->
    <div v-if="!reportDetail" class="text-center py-20">
      <div class="inline-flex items-center gap-2 text-text-secondary">
        <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-primary" />
        <span>加载中...</span>
      </div>
    </div>

    <template v-else>
      <!-- Header -->
      <DetailHeader 
        :title="reportDetail.title"
        :subtitle="reportDetail.summary || '暂无摘要'"
        back-to="/testreports"
      >
        <template #actions>
          <StatusBadge 
            v-if="reportDetail.status" 
            :status="reportDetail.status" 
          />
          <template v-if="isEditing">
            <button class="px-3 py-1.5 text-white/80 hover:text-white hover:bg-white/10 rounded-lg transition-colors flex items-center gap-1" @click="handleCancel">
              <X class="w-4 h-4" />
              取消
            </button>
            <button class="px-3 py-1.5 bg-white text-blue-600 hover:bg-white/90 rounded-lg font-medium transition-colors flex items-center gap-1" @click="handleSave">
              <Save class="w-4 h-4" />
              保存
            </button>
          </template>
          <template v-else>
            <button class="px-3 py-1.5 text-white/80 hover:text-white hover:bg-white/10 rounded-lg transition-colors flex items-center gap-1 border border-white/30" @click="handleEdit">
              <Edit class="w-4 h-4" />
              编辑
            </button>
            <button class="px-3 py-1.5 text-white/80 hover:text-red-200 hover:bg-red-500/20 rounded-lg transition-colors flex items-center gap-1" @click="handleDelete">
              <Delete class="w-4 h-4" />
              删除
            </button>
            <button class="px-3 py-1.5 bg-white text-blue-600 hover:bg-white/90 rounded-lg font-medium transition-colors flex items-center gap-2" @click="openExportDialog">
              <Download class="w-4 h-4" />
              导出报告
            </button>
          </template>
        </template>
      </DetailHeader>

      <!-- 基本信息 -->
      <DetailCard title="基本信息" :icon="FileText" class="mb-6">
        <div class="grid grid-cols-2 gap-6">
          <EditableField 
            label="报告标题" 
            v-model="formData.title"
            :editable="isEditing"
            required
            :span="2"
          />
          <EditableField 
            label="报告摘要" 
            v-model="formData.summary"
            :editable="isEditing"
            type="textarea"
            :span="2"
            :rows="3"
            placeholder="请输入报告摘要"
          />
          <EditableField 
            label="创建时间" 
            :model-value="reportDetail.created_at"
            type="date"
            :editable="false"
          />
          <EditableField 
            v-if="reportDetail.updated_at"
            label="更新时间" 
            :model-value="reportDetail.updated_at"
            type="date"
            :editable="false"
          />
        </div>
      </DetailCard>

      <!-- 统计卡片 -->
      <div v-if="stats" class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <!-- 总用例数 -->
        <div class="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-6 text-white shadow-lg hover:shadow-xl transition-shadow">
          <div class="flex items-center justify-between mb-2">
            <Target class="w-8 h-8 opacity-80" />
            <span class="text-4xl font-bold">{{ stats.total }}</span>
          </div>
          <div class="text-sm opacity-90">总用例数</div>
        </div>

        <!-- 通过 -->
        <div class="bg-gradient-to-br from-green-500 to-green-600 rounded-xl p-6 text-white shadow-lg hover:shadow-xl transition-shadow">
          <div class="flex items-center justify-between mb-2">
            <CheckCircle class="w-8 h-8 opacity-80" />
            <span class="text-4xl font-bold">{{ stats.passed }}</span>
          </div>
          <div class="text-sm opacity-90">通过率 {{ stats.passRate }}%</div>
        </div>

        <!-- 失败 -->
        <div class="bg-gradient-to-br from-red-500 to-red-600 rounded-xl p-6 text-white shadow-lg hover:shadow-xl transition-shadow">
          <div class="flex items-center justify-between mb-2">
            <XCircle class="w-8 h-8 opacity-80" />
            <span class="text-4xl font-bold">{{ stats.failed }}</span>
          </div>
          <div class="text-sm opacity-90">失败用例</div>
        </div>

        <!-- 执行进度 -->
        <div class="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl p-6 text-white shadow-lg hover:shadow-xl transition-shadow">
          <div class="flex items-center justify-between mb-2">
            <TrendingUp class="w-8 h-8 opacity-80" />
            <span class="text-4xl font-bold">{{ stats.executedRate }}%</span>
          </div>
          <div class="text-sm opacity-90 mb-2">执行进度</div>
          <div class="bg-white/20 rounded-full h-2 overflow-hidden">
            <div
              class="bg-white h-full transition-all duration-500"
              :style="{ width: `${stats.executedRate}%` }"
            />
          </div>
        </div>
      </div>

      <!-- 执行状态分布 -->
      <DetailCard v-if="stats" title="执行状态分布" :icon="PieChart" class="mb-6">
        <div class="flex items-center gap-8">
          <!-- 进度条 -->
          <div class="flex-1">
            <div class="bg-gray-100 rounded-xl h-12 flex overflow-hidden shadow-inner">
              <div
                v-for="stat in statusStats"
                :key="stat.label"
                :class="stat.bgColor"
                :style="{ width: `${stats.total > 0 ? stat.value / stats.total * 100 : 0}%` }"
                :title="`${stat.label}: ${stat.value}`"
                class="transition-all duration-500 hover:opacity-80"
              />
            </div>
            
            <div class="flex items-center justify-between mt-4">
              <div
                v-for="stat in statusStats"
                :key="stat.label"
                class="flex items-center gap-2"
              >
                <div :class="[stat.bgColor, 'w-4 h-4 rounded-full shadow-sm']" />
                <span class="text-sm text-text-secondary font-medium">
                  {{ stat.label }}: <span class="text-text-primary">{{ stat.value }}</span>
                </span>
              </div>
            </div>
          </div>
        </div>
      </DetailCard>

      <!-- 执行详情表格 -->
      <DetailCard title="执行详情" :icon="FileText">
        <div v-if="!reportDetail.execution_details || reportDetail.execution_details.length === 0" class="text-center py-12">
          <FileText class="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p class="text-text-secondary">暂无执行详情</p>
        </div>

        <div v-else class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="border-b-2 border-gray-100">
                <th class="text-left py-4 px-4 font-semibold text-text-secondary">用例ID</th>
                <th class="text-left py-4 px-4 font-semibold text-text-secondary">标题</th>
                <th class="text-left py-4 px-4 font-semibold text-text-secondary">执行状态</th>
                <th class="text-left py-4 px-4 font-semibold text-text-secondary">执行人</th>
                <th class="text-left py-4 px-4 font-semibold text-text-secondary">备注</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="detail in reportDetail.execution_details"
                :key="detail.testcase_id"
                class="border-b border-gray-50 hover:bg-gray-50 transition-colors"
              >
                <td class="py-4 px-4 text-text-primary font-medium">{{ detail.testcase_id }}</td>
                <td class="py-4 px-4 text-text-primary">{{ detail.title || '-' }}</td>
                <td class="py-4 px-4">
                  <StatusBadge 
                    :status="detail.execution_status"
                    type="execution"
                  />
                </td>
                <td class="py-4 px-4 text-text-secondary">{{ detail.executor || '-' }}</td>
                <td class="py-4 px-4 text-text-secondary">{{ detail.notes || '-' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </DetailCard>
    </template>

    <!-- 导出格式选择弹窗 -->
    <div
      v-if="showExportDialog"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      @click.self="showExportDialog = false"
    >
      <div class="bg-white rounded-lg shadow-xl w-96">
        <div class="p-6">
          <h3 class="text-lg font-semibold text-text-primary mb-4">选择导出格式</h3>
          
          <div class="space-y-3 mb-6">
            <label
              class="flex items-center gap-3 p-3 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors"
              :class="{ 'border-primary bg-blue-50': exportFormat === 'html' }"
            >
              <input
                v-model="exportFormat"
                type="radio"
                value="html"
                class="text-primary"
              />
              <FileText class="w-5 h-5 text-blue-600" />
              <div>
                <p class="font-medium text-text-primary">HTML格式</p>
                <p class="text-sm text-text-secondary">适合浏览器查看和打印</p>
              </div>
            </label>

            <label
              class="flex items-center gap-3 p-3 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors"
              :class="{ 'border-primary bg-blue-50': exportFormat === 'markdown' }"
            >
              <input
                v-model="exportFormat"
                type="radio"
                value="markdown"
                class="text-primary"
              />
              <File class="w-5 h-5 text-purple-600" />
              <div>
                <p class="font-medium text-text-primary">Markdown格式</p>
                <p class="text-sm text-text-secondary">适合文档编辑和版本控制</p>
              </div>
            </label>

            <label
              class="flex items-center gap-3 p-3 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors"
              :class="{ 'border-primary bg-blue-50': exportFormat === 'csv' }"
            >
              <input
                v-model="exportFormat"
                type="radio"
                value="csv"
                class="text-primary"
              />
              <FileSpreadsheet class="w-5 h-5 text-green-600" />
              <div>
                <p class="font-medium text-text-primary">CSV格式</p>
                <p class="text-sm text-text-secondary">适合Excel等表格软件</p>
              </div>
            </label>
          </div>

          <div class="flex items-center justify-end gap-2">
            <button class="btn-secondary" @click="showExportDialog = false">取消</button>
            <button
              class="btn-primary"
              :disabled="exporting"
              @click="handleExport"
            >
              {{ exporting ? '导出中...' : '导出' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
