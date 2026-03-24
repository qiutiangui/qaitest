<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { Download, Search, Eye, Trash2, FileSpreadsheet, Check, Edit, Plus, FileText, ClipboardList, X, Save, ListChecks, Database, Info } from 'lucide-vue-next'
import { ElMessage, ElMessageBox } from 'element-plus'
import useTestcaseStore from '@/stores/testcase'
import useProjectStore from '@/stores/project'
import useRequirementStore from '@/stores/requirement'
import { testcaseApi } from '@/api/testcase'
import { formatDateTime } from '@/utils/date'
import DetailCard from '@/components/detail/DetailCard.vue'
import EditableField from '@/components/detail/EditableField.vue'
import StatusBadge from '@/components/detail/StatusBadge.vue'
import StepFlow from '@/components/detail/StepFlow.vue'

const testcaseStore = useTestcaseStore()
const projectStore = useProjectStore()
const requirementStore = useRequirementStore()

// 筛选条件
const selectedProject = ref<number | undefined>()
const selectedPriority = ref<string | undefined>()
const searchKeyword = ref('')

// 分页
const currentPage = ref(1)
const pageSize = ref(10)

// 批量选择
const selectedIds = ref<number[]>([])

// 全选状态
const selectAll = ref(false)

// 详情弹窗
const showDetail = ref(false)
const detailTestcase = ref<any>(null)

// 编辑弹窗
const showEditDialog = ref(false)
const editForm = ref<any>({
  id: 0,
  title: '',
  description: '',
  project_id: undefined,
  requirement_id: undefined,
  test_type: '',
  priority: '',
  status: '',
  preconditions: '',
  test_data: '',
  steps: [],
  remarks: ''
})
const saving = ref(false)

// 新建弹窗
const showCreateDialog = ref(false)
const createForm = ref<any>({
  title: '',
  project_id: undefined,
  requirement_id: undefined,
  description: '',
  priority: '中',
  status: '未开始',
  test_type: '功能测试',
  preconditions: '',
  test_data: '',
  steps: [],
  remarks: ''
})
const creating = ref(false)

// 导出格式选择
const showExportDialog = ref(false)
const exportFormat = ref<'excel' | 'markdown'>('excel')
const exporting = ref(false)

// 优先级选项
const priorities = ['高', '中', '低']

// 计算总页数
const totalPages = computed(() => Math.ceil(testcaseStore.total / pageSize.value))

// 是否有选中的用例
const hasSelection = computed(() => selectedIds.value.length > 0)

// 获取用例列表
async function fetchList() {
  await testcaseStore.fetchTestcases({
    page: currentPage.value,
    page_size: pageSize.value,
    project_id: selectedProject.value,
    priority: selectedPriority.value,
    keyword: searchKeyword.value || undefined,
  })
}

// 搜索
function handleSearch() {
  currentPage.value = 1
  fetchList()
}

// 重置筛选
function handleReset() {
  selectedProject.value = undefined
  selectedPriority.value = undefined
  searchKeyword.value = ''
  currentPage.value = 1
  fetchList()
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

function handleSizeChange(size: number) {
  pageSize.value = size
  currentPage.value = 1  // 重置到第一页
  fetchList()
}

// 查看详情
async function viewDetail(id: number) {
  const testcase = await testcaseApi.get(id)
  detailTestcase.value = testcase
  showDetail.value = true
}

// 删除用例
async function deleteTestcase(id: number, title: string) {
  try {
    await ElMessageBox.confirm(`确定删除测试用例「${title}」吗？`, '删除确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await testcaseStore.deleteTestcase(id)
    ElMessage.success('删除成功')
    fetchList()
  } catch {
    // 取消删除
  }
}

// 批量删除
async function handleBatchDelete() {
  if (selectedIds.value.length === 0) {
    ElMessage.warning('请先选择要删除的测试用例')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定删除选中的 ${selectedIds.value.length} 个测试用例吗？`,
      '批量删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await testcaseApi.batchDelete(selectedIds.value)
    ElMessage.success(`成功删除 ${selectedIds.value.length} 个测试用例`)
    selectedIds.value = []
    selectAll.value = false
    fetchList()
  } catch {
    // 取消删除
  }
}

// 全选/取消全选
function handleSelectAll() {
  if (selectAll.value) {
    selectedIds.value = testcaseStore.testcases.map((tc: any) => tc.id)
  } else {
    selectedIds.value = []
  }
}

// 切换单个用例选择
function toggleSelect(id: number) {
  const index = selectedIds.value.indexOf(id)
  if (index > -1) {
    selectedIds.value.splice(index, 1)
  } else {
    selectedIds.value.push(id)
  }
  selectAll.value = selectedIds.value.length === testcaseStore.testcases.length
}

// 导出用例
async function handleExport() {
  if (!selectedProject.value) {
    ElMessage.warning('请先选择项目')
    return
  }
  
  exporting.value = true
  try {
    const result = await testcaseApi.export(selectedProject.value, exportFormat.value)
    
    if (exportFormat.value === 'markdown') {
      const blob = new Blob([result.content!], { type: 'text/markdown' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `测试用例_${new Date().toISOString().split('T')[0]}.md`
      a.click()
      URL.revokeObjectURL(url)
    } else {
      const blob = new Blob([result.content!], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `测试用例_${new Date().toISOString().split('T')[0]}.xlsx`
      a.click()
      URL.revokeObjectURL(url)
    }
    
    showExportDialog.value = false
    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}

// 获取项目名称
function getProjectName(projectId: number | null): string {
  if (!projectId) return '-'
  const project = projectStore.projects.find(p => p.id === projectId)
  return project?.name || '-'
}

// 获取功能点名称
function getFunctionPointName(fpId: number | null): string {
  if (!fpId) return '-'
  const fp = requirementStore.requirements.find(r => r.id === fpId)
  return fp?.name || '-'
}

// 格式化测试步骤
function formatSteps(steps: any[] | undefined): string {
  if (!steps || steps.length === 0) return '-'
  return steps
    .sort((a, b) => a.step_number - b.step_number)
    .map(s => `${s.step_number}、${s.description}`)
    .join('\n')
}

// 打开编辑弹窗
async function openEditDialog(id: number) {
  const testcase = await testcaseApi.get(id)
  editForm.value = {
    id: testcase.id,
    title: testcase.title,
    description: testcase.description || '',
    project_id: testcase.project_id,
    requirement_id: testcase.requirement_id,
    test_type: testcase.test_type || '',
    priority: testcase.priority || '',
    status: testcase.status || '',
    preconditions: testcase.preconditions || '',
    test_data: testcase.test_data || '',
    steps: testcase.steps || [],
    remarks: testcase.remarks || ''
  }
  showEditDialog.value = true
}

// 保存编辑
async function saveEdit() {
  if (!editForm.value.title) {
    ElMessage.warning('请输入用例标题')
    return
  }

  saving.value = true
  try {
    await testcaseStore.updateTestcase(editForm.value.id, {
      title: editForm.value.title,
      description: editForm.value.description,
      project_id: editForm.value.project_id,
      requirement_id: editForm.value.requirement_id,
      test_type: editForm.value.test_type,
      priority: editForm.value.priority,
      status: editForm.value.status,
      preconditions: editForm.value.preconditions,
      test_data: editForm.value.test_data,
      steps: editForm.value.steps,
      remarks: editForm.value.remarks
    })
    ElMessage.success('保存成功')
    showEditDialog.value = false
    fetchList()
  } catch {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

// 打开新建弹窗
function openCreateDialog() {
  createForm.value = {
    title: '',
    project_id: selectedProject.value,
    requirement_id: undefined,
    description: '',
    priority: '中',
    status: '未开始',
    test_type: '功能测试',
    preconditions: '',
    test_data: '',
    steps: []
  }
  showCreateDialog.value = true
}

// 添加测试步骤
function addStep() {
  createForm.value.steps.push({
    step_number: createForm.value.steps.length + 1,
    description: '',
    expected_result: ''
  })
}

// 删除测试步骤
function removeStep(index: number) {
  createForm.value.steps.splice(index, 1)
  // 重新编号
  createForm.value.steps.forEach((step: any, i: number) => {
    step.step_number = i + 1
  })
}

// 保存新建
async function saveCreate() {
  if (!createForm.value.title) {
    ElMessage.warning('请输入用例标题')
    return
  }

  creating.value = true
  try {
    await testcaseStore.createTestcase(createForm.value)
    ElMessage.success('创建成功')
    showCreateDialog.value = false
    fetchList()
  } catch (error) {
    ElMessage.error('创建失败')
  } finally {
    creating.value = false
  }
}

onMounted(async () => {
  await Promise.all([
    projectStore.fetchProjects({ page_size: 100 }),
    requirementStore.fetchRequirements({ page_size: 100 })
  ])
  fetchList()
})
</script>

<template>
  <div class="test-cases-page p-6">
    <!-- 页面标题 -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-semibold text-text-primary">测试用例</h1>
        <p class="text-text-secondary text-sm mt-1">
          查看和管理所有测试用例
        </p>
      </div>
      <div class="flex items-center gap-3">
        <button
          class="btn-primary flex items-center gap-2"
          @click="openCreateDialog"
        >
          <Plus class="w-4 h-4" />
          新建用例
        </button>
        <button
          v-if="hasSelection"
          class="btn-danger flex items-center gap-2"
          @click="handleBatchDelete"
        >
          <Trash2 class="w-4 h-4" />
          批量删除 ({{ selectedIds.length }})
        </button>
        <button
          class="btn-primary flex items-center gap-2"
          @click="showExportDialog = true"
        >
          <Download class="w-4 h-4" />
          导出
        </button>
      </div>
    </div>

    <!-- 筛选和搜索区域 -->
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

        <!-- 优先级筛选 -->
        <div class="flex items-center gap-2">
          <label class="text-sm text-text-secondary">优先级：</label>
          <select
            v-model="selectedPriority"
            class="input-field w-32"
            @change="handleFilterChange"
          >
            <option :value="undefined">全部</option>
            <option v-for="p in priorities" :key="p" :value="p">{{ p }}</option>
          </select>
        </div>

        <!-- 搜索框 -->
        <div class="flex items-center gap-2 flex-1 min-w-[200px]">
          <input
            v-model="searchKeyword"
            type="text"
            placeholder="搜索测试用例..."
            class="input-field flex-1"
            @keyup.enter="handleSearch"
          />
        </div>

        <button @click="handleSearch" class="btn-primary">搜索</button>
        <button @click="handleReset" class="btn-secondary">重置</button>
      </div>
    </div>

    <!-- 用例列表 -->
    <div class="card">
      <div v-if="testcaseStore.loading" class="text-center py-10">
        加载中...
      </div>
      <div v-else-if="testcaseStore.testcases.length === 0" class="text-center py-10 text-text-secondary">
        暂无测试用例
      </div>
      <div v-else>
        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-200">
              <th class="text-center py-3 px-4 w-12">
                <input
                  type="checkbox"
                  v-model="selectAll"
                  @change="handleSelectAll"
                  class="w-4 h-4 cursor-pointer"
                />
              </th>
              <th class="text-left py-3 px-4 text-sm font-medium text-text-secondary">用例标题</th>
              <th class="text-left py-3 px-4 text-sm font-medium text-text-secondary">所属需求</th>
              <th class="text-left py-3 px-4 text-sm font-medium text-text-secondary">关联功能点</th>
              <th class="text-left py-3 px-4 text-sm font-medium text-text-secondary">所属项目</th>
              <th class="text-left py-3 px-4 text-sm font-medium text-text-secondary">优先级</th>
              <th class="text-left py-3 px-4 text-sm font-medium text-text-secondary">创建时间</th>
              <th class="text-right py-3 px-4 text-sm font-medium text-text-secondary">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="tc in testcaseStore.testcases"
              :key="tc.id"
              :class="[
                'border-b border-gray-100 transition-colors',
                selectedIds.includes(tc.id) ? 'bg-blue-50' : 'hover:bg-gray-50'
              ]"
            >
              <td class="py-3 px-4 text-center">
                <input
                  type="checkbox"
                  :checked="selectedIds.includes(tc.id)"
                  @change="toggleSelect(tc.id)"
                  class="w-4 h-4 cursor-pointer"
                />
              </td>
              <td class="py-3 px-4">
                <span class="text-sm font-medium text-primary cursor-pointer hover:text-primary/80" @click="viewDetail(tc.id)">
                  {{ tc.title }}
                </span>
              </td>
              <td class="py-3 px-4 text-sm text-text-secondary">
                {{ tc.requirement_name || '-' }}
              </td>
              <td class="py-3 px-4 text-sm text-text-secondary">
                {{ getFunctionPointName(tc.requirement_id) }}
              </td>
              <td class="py-3 px-4 text-sm text-text-secondary">
                {{ getProjectName(tc.project_id) }}
              </td>
              <td class="py-3 px-4">
                <span
                  v-if="tc.priority"
                  :class="[
                    'px-2 py-0.5 rounded text-xs',
                    tc.priority === '高' ? 'bg-red-100 text-red-700' :
                    tc.priority === '中' ? 'bg-orange-100 text-orange-700' :
                    'bg-green-100 text-green-700'
                  ]"
                >
                  {{ tc.priority }}
                </span>
                <span v-else class="text-text-placeholder">-</span>
              </td>
              <td class="py-3 px-4 text-sm text-text-secondary">
                {{ formatDateTime(tc.created_at) }}
              </td>
              <td class="py-3 px-4">
                <div class="flex items-center justify-end gap-2">
                  <button
                    class="p-1.5 text-text-secondary hover:text-primary hover:bg-primary/10 rounded transition-colors"
                    @click="viewDetail(tc.id)"
                    title="查看"
                  >
                    <Eye class="w-4 h-4" />
                  </button>
                  <button
                    class="p-1.5 text-text-secondary hover:text-primary hover:bg-primary/10 rounded transition-colors"
                    @click="openEditDialog(tc.id)"
                    title="编辑"
                  >
                    <Edit class="w-4 h-4" />
                  </button>
                  <button
                    class="p-1.5 text-text-secondary hover:text-red-500 hover:bg-red-50 rounded transition-colors"
                    @click="deleteTestcase(tc.id, tc.title)"
                    title="删除"
                  >
                    <Trash2 class="w-4 h-4" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>

        <!-- 分页 -->
        <div class="flex items-center justify-between mt-4 pt-4 border-t border-gray-100">
          <div class="text-sm text-text-secondary">
            共 {{ testcaseStore.total }} 条记录
          </div>
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="testcaseStore.total"
            layout="sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handlePageChange"
          />
        </div>
      </div>
    </div>

    <!-- 详情弹窗 -->
    <div v-if="showDetail" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-6">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-5xl max-h-[90vh] overflow-hidden flex flex-col">
        <!-- Header -->
        <div class="bg-gradient-to-r from-blue-500 to-cyan-500 px-6 py-5 flex items-center justify-between">
          <div class="flex items-center gap-3">
            <FileText class="w-6 h-6 text-white" />
            <h3 class="text-xl font-bold text-white">测试用例详情</h3>
          </div>
          <button 
            @click="showDetail = false" 
            class="text-white/80 hover:text-white transition-colors p-1 hover:bg-white/10 rounded-lg"
          >
            <X class="w-6 h-6" />
          </button>
        </div>

        <!-- Content -->
        <div v-if="detailTestcase" class="flex-1 overflow-y-auto p-6 space-y-4">
          <!-- 基本信息 -->
          <DetailCard title="基本信息" :icon="FileText">
            <div class="grid grid-cols-2 gap-6">
              <EditableField
                label="用例标题"
                :model-value="detailTestcase.title"
                :editable="false"
                :span="2"
              />
              <EditableField
                label="用例描述"
                :model-value="detailTestcase.description"
                :editable="false"
                type="textarea"
                :span="2"
              />
              <EditableField
                label="所属项目"
                :model-value="getProjectName(detailTestcase.project_id)"
                :editable="false"
              />
              <EditableField
                label="关联功能点"
                :model-value="detailTestcase.requirement_name || getFunctionPointName(detailTestcase.requirement_id)"
                :editable="false"
              />
              <EditableField
                label="测试类型"
                :model-value="detailTestcase.test_type"
                :editable="false"
              />
            </div>
          </DetailCard>

          <!-- 前置条件 -->
          <DetailCard title="前置条件" :icon="ListChecks">
            <EditableField
              :model-value="detailTestcase.preconditions"
              :editable="false"
              type="textarea"
              :rows="3"
            />
          </DetailCard>

          <!-- 测试数据 -->
          <DetailCard title="测试数据" :icon="Database">
            <EditableField
              :model-value="detailTestcase.test_data"
              :editable="false"
              type="textarea"
              :rows="3"
            />
          </DetailCard>

          <!-- 测试步骤 -->
          <DetailCard title="测试步骤" :icon="ClipboardList">
            <StepFlow :steps="detailTestcase.steps?.sort((a: any, b: any) => a.step_number - b.step_number)" />
          </DetailCard>

          <!-- 其他信息 -->
          <DetailCard title="其他信息" :icon="Info">
            <div class="grid grid-cols-4 gap-6">
              <div>
                <label class="block text-sm font-medium text-text-secondary mb-2">优先级</label>

                <StatusBadge
                  v-if="detailTestcase.priority"
                  :status="detailTestcase.priority"
                  type="priority"
                />
                <span v-else class="text-text-placeholder">-</span>
              </div>
              <div>
                <label class="block text-sm font-medium text-text-secondary mb-2">状态</label>
                <StatusBadge
                  v-if="detailTestcase.status"
                  :status="detailTestcase.status"
                />
                <span v-else class="text-text-placeholder">-</span>
              </div>
              <div>
                <label class="block text-sm font-medium text-text-secondary mb-2">创建者</label>
                <p class="text-text-primary">{{ detailTestcase.creator || '-' }}</p>
              </div>
              <div>
                <label class="block text-sm font-medium text-text-secondary mb-2">备注</label>
                <p class="text-text-primary">{{ detailTestcase.remarks || '-' }}</p>
              </div>
            </div>
          </DetailCard>
        </div>
      </div>
    </div>

    <!-- 导出对话框 -->
    <div v-if="showExportDialog" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl w-full max-w-md">
        <div class="p-6 border-b border-gray-200">
          <h3 class="text-lg font-semibold text-text-primary">导出测试用例</h3>
        </div>
        <div class="p-6 space-y-4">
          <div>
            <label class="block text-sm font-medium text-text-primary mb-2">导出格式</label>
            <div class="flex gap-4">
              <label class="flex items-center gap-2 cursor-pointer">
                <input type="radio" v-model="exportFormat" value="excel" class="text-primary" />
                <span class="text-sm text-text-primary">Excel</span>
              </label>
              <label class="flex items-center gap-2 cursor-pointer">
                <input type="radio" v-model="exportFormat" value="markdown" class="text-primary" />
                <span class="text-sm text-text-primary">Markdown</span>
              </label>
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-text-primary mb-2">导出范围</label>
            <select v-model="selectedProject" class="input-field w-full">
              <option :value="undefined">全部项目</option>
              <option v-for="project in projectStore.projects" :key="project.id" :value="project.id">
                {{ project.name }}
              </option>
            </select>
          </div>
        </div>
        <div class="p-6 border-t border-gray-200 flex justify-end gap-3">
          <button @click="showExportDialog = false" class="btn-secondary">取消</button>
          <button @click="handleExport" :disabled="exporting" class="btn-primary flex items-center gap-2">
            <Download class="w-4 h-4" />
            {{ exporting ? '导出中...' : '导出' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 编辑弹窗 -->
    <div v-if="showEditDialog" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-6">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-5xl max-h-[90vh] overflow-hidden flex flex-col">
        <!-- Header -->
        <div class="bg-gradient-to-r from-blue-500 to-cyan-500 px-6 py-5 flex items-center justify-between">
          <div class="flex items-center gap-3">
            <Edit class="w-6 h-6 text-white" />
            <h3 class="text-xl font-bold text-white">编辑测试用例</h3>
          </div>
          <button
            @click="showEditDialog = false"
            class="text-white/80 hover:text-white transition-colors p-1 hover:bg-white/10 rounded-lg"
          >
            <X class="w-6 h-6" />
          </button>
        </div>

        <!-- Content -->
        <div class="flex-1 overflow-y-auto p-6 space-y-4">
          <!-- 基本信息 -->
          <DetailCard title="基本信息" :icon="FileText">
            <div class="grid grid-cols-2 gap-6">
              <EditableField
                label="用例标题"
                v-model="editForm.title"
                editable
                required
                :span="2"
              />
              <EditableField
                label="用例描述"
                v-model="editForm.description"
                editable
                type="textarea"
                :span="2"
                :rows="3"
              />
              <EditableField
                label="所属项目"
                v-model="editForm.project_id"
                editable
                type="select"
                :options="projectStore.projects.map(p => ({ label: p.name, value: p.id }))"
              />
              <EditableField
                label="关联功能点"
                v-model="editForm.requirement_id"
                editable
                type="select"
                :options="requirementStore.requirements.map(r => ({ label: r.name, value: r.id }))"
              />
              <EditableField
                label="测试类型"
                v-model="editForm.test_type"
                editable
                placeholder="如：功能测试、性能测试等"
              />
            </div>
          </DetailCard>

          <!-- 前置条件 -->
          <DetailCard title="前置条件" :icon="ListChecks">
            <EditableField
              v-model="editForm.preconditions"
              editable
              type="textarea"
              :rows="3"
              placeholder="请输入前置条件"
            />
          </DetailCard>

          <!-- 测试数据 -->
          <DetailCard title="测试数据" :icon="Database">
            <EditableField
              v-model="editForm.test_data"
              editable
              type="textarea"
              :rows="3"
              placeholder="请输入测试数据"
            />
          </DetailCard>

          <!-- 测试步骤 -->
          <DetailCard title="测试步骤" :icon="ClipboardList">
            <div class="space-y-3">
              <div
                v-for="(step, index) in editForm.steps"
                :key="index"
                class="border border-gray-200 rounded-lg p-4"
              >
                <div class="flex items-start gap-3">
                  <div class="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-semibold text-sm flex-shrink-0">
                    {{ index + 1 }}
                  </div>
                  <div class="flex-1 space-y-3">
                    <input
                      v-model="step.description"
                      type="text"
                      class="input-field w-full"
                      placeholder="请输入步骤描述"
                    />
                    <input
                      v-model="step.expected_result"
                      type="text"
                      class="input-field w-full"
                      placeholder="预期结果"
                    />
                  </div>
                  <button
                    @click="editForm.steps.splice(index, 1)"
                    class="text-red-500 hover:text-red-600 p-1"
                  >
                    <Trash2 class="w-4 h-4" />
                  </button>
                </div>
              </div>
              <button
                @click="editForm.steps.push({ step_number: editForm.steps.length + 1, description: '', expected_result: '' })"
                class="w-full py-2 border-2 border-dashed border-gray-300 rounded-lg text-text-secondary hover:text-primary hover:border-primary transition-colors"
              >
                + 添加步骤
              </button>
            </div>
          </DetailCard>

          <!-- 其他信息 -->
          <DetailCard title="其他信息" :icon="Info">
            <div class="grid grid-cols-3 gap-6">
              <EditableField
                label="优先级"
                v-model="editForm.priority"
                editable
                type="select"
                :options="priorities.map(p => ({ label: p, value: p }))"
              />
              <EditableField
                label="状态"
                v-model="editForm.status"
                editable
                type="select"
                :options="statuses.map(s => ({ label: s, value: s }))"
              />
              <EditableField
                label="备注"
                v-model="editForm.remarks"
                editable
                placeholder="请输入备注"
              />
            </div>
          </DetailCard>
        </div>

        <!-- Footer -->
        <div class="border-t border-gray-200 px-6 py-4 flex justify-end gap-3 bg-gray-50">
          <button @click="showEditDialog = false" class="btn-secondary">取消</button>
          <button @click="saveEdit" :disabled="saving" class="btn-primary flex items-center gap-2">
            <Save class="w-4 h-4" />
            {{ saving ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 新建弹窗 -->
    <div v-if="showCreateDialog" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-6">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-5xl max-h-[90vh] overflow-hidden flex flex-col">
        <!-- Header -->
        <div class="bg-gradient-to-r from-green-500 to-emerald-500 px-6 py-5 flex items-center justify-between">
          <div class="flex items-center gap-3">
            <Plus class="w-6 h-6 text-white" />
            <h3 class="text-xl font-bold text-white">新建测试用例</h3>
          </div>
          <button
            @click="showCreateDialog = false"
            class="text-white/80 hover:text-white transition-colors p-1 hover:bg-white/10 rounded-lg"
          >
            <X class="w-6 h-6" />
          </button>
        </div>

        <!-- Content -->
        <div class="flex-1 overflow-y-auto p-6 space-y-4">
          <!-- 基本信息 -->
          <DetailCard title="基本信息" :icon="FileText">
            <div class="grid grid-cols-2 gap-6">
              <EditableField
                label="用例标题"
                v-model="createForm.title"
                editable
                required
                :span="2"
              />
              <EditableField
                label="用例描述"
                v-model="createForm.description"
                editable
                type="textarea"
                :span="2"
                :rows="3"
              />
              <EditableField
                label="所属项目"
                v-model="createForm.project_id"
                editable
                type="select"
                :options="projectStore.projects.map(p => ({ label: p.name, value: p.id }))"
              />
              <EditableField
                label="关联功能点"
                v-model="createForm.requirement_id"
                editable
                type="select"
                :options="requirementStore.requirements.map(r => ({ label: r.name, value: r.id }))"
              />
              <EditableField
                label="测试类型"
                v-model="createForm.test_type"
                editable
                placeholder="如：功能测试、性能测试等"
              />
            </div>
          </DetailCard>

          <!-- 前置条件 -->
          <DetailCard title="前置条件" :icon="ListChecks">
            <EditableField
              v-model="createForm.preconditions"
              editable
              type="textarea"
              :rows="3"
              placeholder="请输入前置条件"
            />
          </DetailCard>

          <!-- 测试数据 -->
          <DetailCard title="测试数据" :icon="Database">
            <EditableField
              v-model="createForm.test_data"
              editable
              type="textarea"
              :rows="3"
              placeholder="请输入测试数据"
            />
          </DetailCard>

          <!-- 测试步骤 -->
          <DetailCard title="测试步骤" :icon="ClipboardList">
            <div class="space-y-3">
              <div
                v-for="(step, index) in createForm.steps"
                :key="index"
                class="border border-gray-200 rounded-lg p-4"
              >
                <div class="flex items-start gap-3">
                  <div class="w-8 h-8 rounded-full bg-green-100 text-green-600 flex items-center justify-center font-semibold text-sm flex-shrink-0">
                    {{ index + 1 }}
                  </div>
                  <div class="flex-1 space-y-3">
                    <input
                      v-model="step.description"
                      type="text"
                      class="input-field w-full"
                      placeholder="请输入步骤描述"
                    />
                    <input
                      v-model="step.expected_result"
                      type="text"
                      class="input-field w-full"
                      placeholder="预期结果"
                    />
                  </div>
                  <button
                    @click="removeStep(index)"
                    class="text-red-500 hover:text-red-600 p-1"
                  >
                    <Trash2 class="w-4 h-4" />
                  </button>
                </div>
              </div>
              <button
                @click="addStep"
                class="w-full py-2 border-2 border-dashed border-gray-300 rounded-lg text-text-secondary hover:text-primary hover:border-primary transition-colors"
              >
                + 添加步骤
              </button>
            </div>
          </DetailCard>

          <!-- 其他信息 -->
          <DetailCard title="其他信息" :icon="Info">
            <div class="grid grid-cols-3 gap-6">
              <EditableField
                label="优先级"
                v-model="createForm.priority"
                editable
                type="select"
                :options="priorities.map(p => ({ label: p, value: p }))"
              />
              <EditableField
                label="状态"
                v-model="createForm.status"
                editable
                type="select"
                :options="statuses.map(s => ({ label: s, value: s }))"
              />
              <EditableField
                label="备注"
                v-model="createForm.remarks"
                editable
                placeholder="请输入备注"
              />
            </div>
          </DetailCard>
        </div>

        <!-- Footer -->
        <div class="border-t border-gray-200 px-6 py-4 flex justify-end gap-3 bg-gray-50">
          <button @click="showCreateDialog = false" class="btn-secondary">取消</button>
          <button @click="saveCreate" :disabled="creating" class="btn-primary flex items-center gap-2">
            <Check class="w-4 h-4" />
            {{ creating ? '创建中...' : '创建' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.test-cases-page {
  max-width: 1400px;
  margin: 0 auto;
}
</style>
