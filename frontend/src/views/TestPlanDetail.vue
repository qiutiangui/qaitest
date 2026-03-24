<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Play, CheckCircle, XCircle, AlertCircle, Clock, Edit2, Trash2, Target, TrendingUp, CheckSquare, BarChart3, Save, X, FileText } from 'lucide-vue-next'
import useTestplanStore from '@/stores/testplan'
import useTestcaseStore from '@/stores/testcase'
import DetailHeader from '@/components/detail/DetailHeader.vue'
import DetailCard from '@/components/detail/DetailCard.vue'
import EditableField from '@/components/detail/EditableField.vue'
import StatusBadge from '@/components/detail/StatusBadge.vue'

const route = useRoute()
const router = useRouter()
const testplanStore = useTestplanStore()
const testcaseStore = useTestcaseStore()

// 计划ID
const planId = computed(() => Number(route.params.id))

// 编辑模式
const isEditing = ref(false)
const formData = ref({
  name: '',
  description: '',
  start_time: '',
  end_time: ''
})

// 添加用例弹窗
const showAddCasesDialog = ref(false)
const selectedTestcases = ref<number[]>([])

// 执行状态选项
const executionStatuses = ['未执行', '通过', '失败', '阻塞']

// 当前计划详情
const planDetail = computed(() => testplanStore.currentTestplan)

// 统计数据
const stats = computed(() => {
  if (!planDetail.value) return null
  
  const total = planDetail.value.total_cases
  const passed = planDetail.value.passed_cases
  const failed = planDetail.value.failed_cases
  const blocked = planDetail.value.blocked_cases
  const notExecuted = planDetail.value.not_executed_cases
  const passRate = planDetail.value.pass_rate
  
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

// 获取状态颜色
function getStatusColor(status: string) {
  const colors: Record<string, string> = {
    '未开始': 'bg-gray-100 text-gray-700',
    '进行中': 'bg-blue-100 text-blue-700',
    '已完成': 'bg-green-100 text-green-700',
    '已归档': 'bg-gray-100 text-gray-500',
  }
  return colors[status] || 'bg-gray-100 text-gray-700'
}

// 获取执行状态图标和颜色
function getExecutionStatusStyle(status: string) {
  const styles: Record<string, { icon: any; color: string; bgColor: string }> = {
    '未执行': { icon: Clock, color: 'text-gray-600', bgColor: 'bg-gray-100' },
    '通过': { icon: CheckCircle, color: 'text-green-600', bgColor: 'bg-green-100' },
    '失败': { icon: XCircle, color: 'text-red-600', bgColor: 'bg-red-100' },
    '阻塞': { icon: AlertCircle, color: 'text-orange-600', bgColor: 'bg-orange-100' },
  }
  return styles[status] || styles['未执行']
}

// 获取计划详情
async function fetchDetail() {
  await testplanStore.fetchTestplan(planId.value)
}

// 开始编辑
function handleEdit() {
  if (!planDetail.value) return
  isEditing.value = true
  formData.value = {
    name: planDetail.value.name || '',
    description: planDetail.value.description || '',
    start_time: planDetail.value.start_time || '',
    end_time: planDetail.value.end_time || ''
  }
}

// 取消编辑
function handleCancel() {
  isEditing.value = false
  formData.value = {
    name: '',
    description: '',
    start_time: '',
    end_time: ''
  }
}

// 保存
async function handleSave() {
  if (!planDetail.value) return
  
  try {
    await testplanStore.updateTestplan(planId.value, formData.value)
    ElMessage.success('保存成功')
    isEditing.value = false
    await fetchDetail()
  } catch {
    ElMessage.error('保存失败')
  }
}

// 删除
async function handleDelete() {
  if (!planDetail.value) return
  
  try {
    await ElMessageBox.confirm(
      `确定要删除测试计划「${planDetail.value.name}」吗？`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await testplanStore.deleteTestplan(planPlan.value.id)
    ElMessage.success('删除成功')
    router.push('/testplans')
  } catch {
    // 用户取消
  }
}

// 打开添加用例弹窗
async function openAddCasesDialog() {
  await testcaseStore.fetchTestcases({ page_size: 100 })
  selectedTestcases.value = []
  showAddCasesDialog.value = true
}

// 添加用例到计划
async function handleAddCases() {
  if (selectedTestcases.value.length === 0) {
    alert('请选择要添加的用例')
    return
  }
  
  await testplanStore.addCasesToPlan(planId.value, selectedTestcases.value)
  showAddCasesDialog.value = false
  fetchDetail()
}

// 更新执行状态
async function updateStatus(testcaseId: number, status: string) {
  await testplanStore.updateExecutionStatus(
    planId.value,
    testcaseId,
    status
  )
  fetchDetail()
}

// 切换计划状态
async function togglePlanStatus(status: string) {
  await testplanStore.updateTestplan(planId.value, { status })
  fetchDetail()
}

onMounted(() => {
  fetchDetail()
})
</script>

<template>
  <div class="testplan-detail-page p-6 max-w-7xl mx-auto">
    <!-- 加载中 -->
    <div v-if="!planDetail" class="text-center py-20">
      <div class="inline-flex items-center gap-2 text-text-secondary">
        <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-primary" />
        <span>加载中...</span>
      </div>
    </div>

    <template v-else>
      <!-- Header -->
      <DetailHeader 
        :title="planDetail.name"
        :subtitle="planDetail.description || '暂无描述'"
        back-to="/testplans"
      >
        <template #actions>
          <StatusBadge 
            v-if="planDetail.status" 
            :status="planDetail.status" 
            type="plan" 
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
              <Edit2 class="w-4 h-4" />
              编辑
            </button>
            <button class="px-3 py-1.5 text-white/80 hover:text-red-200 hover:bg-red-500/20 rounded-lg transition-colors flex items-center gap-1" @click="handleDelete">
              <Trash2 class="w-4 h-4" />
              删除
            </button>
            <button class="px-3 py-1.5 bg-white text-blue-600 hover:bg-white/90 rounded-lg font-medium transition-colors flex items-center gap-2" @click="openAddCasesDialog">
              <Plus class="w-4 h-4" />
              添加用例
            </button>
          </template>
        </template>
      </DetailHeader>

      <!-- 基本信息 -->
      <DetailCard title="基本信息" :icon="FileText" class="mb-6">
        <div class="grid grid-cols-2 gap-6">
          <EditableField 
            label="计划名称" 
            v-model="formData.name"
            :editable="isEditing"
            required
            :span="2"
          />
          <EditableField 
            label="计划描述" 
            v-model="formData.description"
            :editable="isEditing"
            type="textarea"
            :span="2"
            :rows="3"
          />
          <EditableField 
            label="开始时间" 
            v-model="formData.start_time"
            :editable="isEditing"
            type="date"
          />
          <EditableField 
            label="结束时间" 
            v-model="formData.end_time"
            :editable="isEditing"
            type="date"
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

      <!-- 用例列表 -->
      <DetailCard title="测试用例执行情况" :icon="CheckSquare" class="mb-6">
        <div v-if="!planDetail.test_plan_cases || planDetail.test_plan_cases.length === 0" class="text-center py-12">
          <CheckSquare class="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p class="text-text-secondary">暂无用例，请点击"添加用例"按钮添加测试用例</p>
        </div>

        <div v-else class="space-y-3">
          <div
            v-for="planCase in planDetail.test_plan_cases"
            :key="planCase.id"
            class="border border-gray-100 rounded-xl p-4 hover:bg-gray-50 transition-all hover:shadow-md"
          >
            <div class="flex items-center justify-between">
              <div class="flex-1">
                <div class="font-medium text-text-primary text-lg mb-2">
                  用例 #{{ planCase.test_case_id }}
                </div>
                <div class="flex items-center gap-4 text-sm text-text-secondary">
                  <div v-if="planCase.executor" class="flex items-center gap-1">
                    <Clock class="w-3.5 h-3.5" />
                    <span>执行人：{{ planCase.executor }}</span>
                  </div>
                  <div v-if="planCase.notes">备注：{{ planCase.notes }}</div>
                </div>
              </div>

              <div class="flex items-center gap-2">
                <button
                  v-for="status in executionStatuses"
                  :key="status"
                  :class="[
                    'px-4 py-2 rounded-lg text-sm font-medium transition-all',
                    planCase.execution_status === status
                      ? 'shadow-md transform scale-105 ' + getExecutionStatusStyle(status).bgColor + ' ' + getExecutionStatusStyle(status).color
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200',
                  ]"
                  @click="updateStatus(planCase.test_case_id, status)"
                >
                  <component 
                    :is="getExecutionStatusStyle(status).icon" 
                    v-if="planCase.execution_status === status"
                    class="w-4 h-4 inline mr-1" 
                  />
                  {{ status }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </DetailCard>

      <!-- 状态操作 -->
      <DetailCard title="状态操作" :icon="BarChart3">
        <div class="flex items-center gap-3">
          <button
            :class="[
              'px-6 py-3 rounded-xl transition-all font-medium',
              planDetail.status === '进行中'
                ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-lg transform scale-105'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200',
            ]"
            @click="togglePlanStatus('进行中')"
          >
            <Play class="w-4 h-4 inline mr-2" />
            开始执行
          </button>
          <button
            :class="[
              'px-6 py-3 rounded-xl transition-all font-medium',
              planDetail.status === '已完成'
                ? 'bg-gradient-to-r from-green-500 to-green-600 text-white shadow-lg transform scale-105'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200',
            ]"
            @click="togglePlanStatus('已完成')"
          >
            <CheckCircle class="w-4 h-4 inline mr-2" />
            标记完成
          </button>
          <button
            :class="[
              'px-6 py-3 rounded-xl transition-all font-medium',
              planDetail.status === '已归档'
                ? 'bg-gradient-to-r from-gray-600 to-gray-700 text-white shadow-lg transform scale-105'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200',
            ]"
            @click="togglePlanStatus('已归档')"
          >
            归档
          </button>
        </div>
      </DetailCard>
    </template>

    <!-- 添加用例弹窗 -->
    <div
      v-if="showAddCasesDialog"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      @click.self="showAddCasesDialog = false"
    >
      <div class="bg-white rounded-lg shadow-xl w-[800px] max-h-[80vh] overflow-y-auto">
        <div class="p-6">
          <h2 class="text-xl font-semibold text-text-primary mb-4">添加测试用例</h2>

          <div v-if="testcaseStore.testcases.length === 0" class="text-center py-10 text-text-secondary">
            暂无可添加的测试用例
          </div>

          <div v-else>
            <div class="mb-4">
              <label class="flex items-center gap-2">
                <input
                  type="checkbox"
                  :checked="selectedTestcases.length === testcaseStore.testcases.length"
                  @change="selectedTestcases = selectedTestcases.length === testcaseStore.testcases.length ? [] : testcaseStore.testcases.map(t => t.id)"
                />
                <span class="text-sm text-text-secondary">全选</span>
              </label>
            </div>

            <div class="grid grid-cols-1 gap-2 max-h-96 overflow-y-auto">
              <label
                v-for="testcase in testcaseStore.testcases"
                :key="testcase.id"
                class="flex items-center gap-3 p-3 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors"
                :class="{ 'border-primary bg-blue-50': selectedTestcases.includes(testcase.id) }"
              >
                <input
                  v-model="selectedTestcases"
                  type="checkbox"
                  :value="testcase.id"
                />
                <div class="flex-1">
                  <div class="font-medium text-text-primary">{{ testcase.title }}</div>
                  <div class="text-sm text-text-secondary">
                    优先级：{{ testcase.priority || '-' }} | 类型：{{ testcase.test_type || '-' }}
                  </div>
                </div>
              </label>
            </div>
          </div>

          <div class="flex items-center justify-between mt-6">
            <div class="text-sm text-text-secondary">
              已选择 {{ selectedTestcases.length }} 个用例
            </div>
            <div class="flex items-center gap-2">
              <button class="btn-secondary" @click="showAddCasesDialog = false">取消</button>
              <button class="btn-primary" @click="handleAddCases">添加</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
