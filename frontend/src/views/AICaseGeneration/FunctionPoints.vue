<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, View, Trash2, TestTube, Loader, X, FileText, CheckSquare, Save, Settings, CheckCircle, Tag } from 'lucide-vue-next'
import useRequirementStore from '@/stores/requirement'
import useProjectStore from '@/stores/project'
import useTestcaseStore from '@/stores/testcase'
import useVersionStore from '@/stores/version'
import { testcaseApi } from '@/api/testcase'
import type { Requirement, RequirementCreate, RequirementUpdate } from '@/types/requirement'
import { formatDateTime } from '@/utils/date'
import DetailCard from '@/components/detail/DetailCard.vue'
import EditableField from '@/components/detail/EditableField.vue'
import StatusBadge from '@/components/detail/StatusBadge.vue'

const router = useRouter()
const route = useRoute()
const requirementStore = useRequirementStore()
const projectStore = useProjectStore()
const testcaseStore = useTestcaseStore()
const versionStore = useVersionStore()

// 详情弹窗
const showDetail = ref(false)
const detailRequirement = ref<Requirement | null>(null)

// 搜索筛选
const keyword = ref('')
const selectedProject = ref<number | undefined>()
const selectedCategory = ref<string>('')
const selectedPriority = ref<string>('')
const selectedRequirementName = ref<string>('')
const sortBy = ref('created_at')
const sortOrder = ref<'asc' | 'desc'>('desc')

// 分页
const currentPage = ref(1)
const pageSize = ref(10)

// 批量选择
const selectedIds = ref<number[]>([])
const isAllSelected = computed(() => {
  return requirementStore.requirements.length > 0 &&
         selectedIds.value.length === requirementStore.requirements.length
})

// 对话框
const dialogVisible = ref(false)
const dialogTitle = ref('新建功能点')
const isEdit = ref(false)
const editingId = ref<number | null>(null)
const formData = ref<RequirementCreate | RequirementUpdate>({
  name: '',
  project_id: 0,
  description: '',
  category: '',
  module: '',
  priority: '',
  acceptance_criteria: '',
  keywords: ''
})

// 生成测试用例状态
const isGenerating = ref(false)
const generatingIds = ref<number[]>([])

// 类别和优先级选项
const categoryOptions = ['功能需求', '非功能需求', '界面需求', '数据需求', '安全需求', '性能需求']
const priorityOptions = ['高', '中', '低']

// 总页数
const totalPages = computed(() => Math.ceil(requirementStore.total / pageSize.value))

// 获取唯一的需求名称列表
const requirementNames = computed(() => {
  const names = new Set<string>()
  requirementStore.requirements.forEach(r => {
    if (r.requirement_name) names.add(r.requirement_name)
  })
  return Array.from(names).sort()
})

// 加载需求数据（基于需求分析任务）
async function loadRequirementGroups() {
  requirementLoading.value = true
  try {
    const response = await api.get('/ai-tasks/requirements/list', {
      params: {
        page: requirementPage.value,
        page_size: requirementPageSize.value,
        project_id: selectedProject.value || undefined,
        keyword: keyword.value || undefined
      }
    })
    
    requirementGroups.value = response.items || []
    requirementTotal.value = response.total || 0
  } catch (error) {
    console.error('加载需求数据失败:', error)
    ElMessage.error('加载需求数据失败')
  } finally {
    requirementLoading.value = false
  }
}

// 加载数据
async function loadData() {
  await requirementStore.fetchRequirements({
    page: currentPage.value,
    page_size: pageSize.value,
    project_id: selectedProject.value,
    category: selectedCategory.value || undefined,
    priority: selectedPriority.value || undefined,
    requirement_name: selectedRequirementName.value || undefined,
    keyword: keyword.value || undefined,
    sort_by: sortBy.value,
    order: sortOrder.value
  })
}

// 初始化
onMounted(async () => {
  await Promise.all([
    projectStore.fetchProjects({ page_size: 100 }),
    versionStore.fetchVersions({ page_size: 100 })
  ])
  
  // 从 URL 查询参数中获取筛选条件
  if (route.query.requirement_name) {
    selectedRequirementName.value = String(route.query.requirement_name)
  }
  
  loadData()
})

// 获取项目名称
function getProjectName(projectId: number): string {
  const project = projectStore.projects.find(p => p.id === projectId)
  return project?.name || '-'
}

// 搜索
function handleSearch() {
  currentPage.value = 1
  loadData()
}

// 重置筛选
function handleReset() {
  keyword.value = ''
  selectedProject.value = undefined
  selectedCategory.value = ''
  selectedPriority.value = ''
  selectedRequirementName.value = ''
  sortBy.value = 'created_at'
  sortOrder.value = 'desc'
  currentPage.value = 1
  loadData()
}

// 分页变化
function handlePageChange(page: number) {
  currentPage.value = page
  loadData()
}

function handleSizeChange(size: number) {
  pageSize.value = size
  currentPage.value = 1  // 重置到第一页
  loadData()
}

// 新建功能点
function handleCreate() {
  isEdit.value = false
  dialogTitle.value = '新建功能点'
  formData.value = {
    name: '',
    project_id: selectedProject.value || (projectStore.projects[0]?.id ?? 0),
    description: '',
    category: '',
    module: '',
    priority: '',
    acceptance_criteria: '',
    keywords: ''
  }
  dialogVisible.value = true
}

// 编辑功能点
function handleEdit(req: Requirement) {
  isEdit.value = true
  editingId.value = req.id
  dialogTitle.value = '编辑功能点'
  formData.value = {
    name: req.name,
    project_id: req.project_id,
    description: req.description || '',
    category: req.category || '',
    module: req.module || '',
    priority: req.priority || '',
    acceptance_criteria: req.acceptance_criteria || '',
    keywords: req.keywords || ''
  }
  dialogVisible.value = true
}

// 查看详情
async function handleView(req: Requirement) {
  await requirementStore.fetchRequirement(req.id)
  detailRequirement.value = requirementStore.currentRequirement
  showDetail.value = true
}

// 保存功能点
async function handleSave() {
  try {
    if (isEdit.value && editingId.value) {
      await requirementStore.updateRequirement(editingId.value, formData.value as RequirementUpdate)
      ElMessage.success('更新成功')
    } else {
      await requirementStore.createRequirement(formData.value as RequirementCreate)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadData()
  } catch (error: any) {
    ElMessage.error(error.message || '操作失败')
  }
}

// 删除功能点
async function handleDelete(req: Requirement) {
  try {
    const result = await ElMessageBox.confirm(
      `确定删除功能点「${req.name}」吗？`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
        distinguishCancelAndClose: true,
        showCancelButton: true,
        message: `
          <div>
            <p style="margin-bottom: 12px;">确定删除功能点「${req.name}」吗？</p>
            <label style="display: flex; align-items: center; cursor: pointer;">
              <input type="checkbox" id="deleteTestcases" style="margin-right: 8px;" />
              <span>同时删除关联的测试用例</span>
            </label>
          </div>
        `,
        dangerouslyUseHTMLString: true,
      }
    )
    
    // 获取复选框状态
    const checkbox = document.getElementById('deleteTestcases') as HTMLInputElement
    const deleteTestcases = checkbox?.checked || false
    
    const res = await requirementStore.deleteRequirement(req.id, deleteTestcases)
    
    let message = '删除成功'
    if (deleteTestcases && res.deleted_testcase_count) {
      message += `，已同步删除 ${res.deleted_testcase_count} 个测试用例`
    }
    
    ElMessage.success(message)
    loadData()
    selectedIds.value = selectedIds.value.filter(id => id !== req.id)
  } catch {
    // 取消删除
  }
}

// 全选/取消全选
function handleSelectAll(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.checked) {
    selectedIds.value = requirementStore.requirements.map(r => r.id)
  } else {
    selectedIds.value = []
  }
}

// 批量删除
async function handleBatchDelete() {
  if (selectedIds.value.length === 0) {
    ElMessage.warning('请先选择要删除的功能点')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedIds.value.length} 个功能点吗？`,
      '批量删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
        distinguishCancelAndClose: true,
        showCancelButton: true,
        message: `
          <div>
            <p style="margin-bottom: 12px;">确定要删除选中的 ${selectedIds.value.length} 个功能点吗？</p>
            <label style="display: flex; align-items: center; cursor: pointer;">
              <input type="checkbox" id="batchDeleteTestcases" style="margin-right: 8px;" />
              <span>同时删除关联的测试用例</span>
            </label>
          </div>
        `,
        dangerouslyUseHTMLString: true,
      }
    )

    // 获取复选框状态
    const checkbox = document.getElementById('batchDeleteTestcases') as HTMLInputElement
    const deleteTestcases = checkbox?.checked || false

    const res = await requirementStore.batchDeleteRequirements(selectedIds.value, deleteTestcases)
    
    let message = `成功删除 ${selectedIds.value.length} 个功能点`
    if (deleteTestcases && res.deleted_testcase_count) {
      message += `，已同步删除 ${res.deleted_testcase_count} 个测试用例`
    }
    
    ElMessage.success(message)
    selectedIds.value = []
    loadData()
  } catch {
    // 取消删除
  }
}

// 批量生成测试用例
async function handleGenerateTestCases() {
  if (selectedIds.value.length === 0) {
    ElMessage.warning('请先选择要生成用例的功能点')
    return
  }

  try {
    isGenerating.value = true
    generatingIds.value = [...selectedIds.value]

    const result = await testcaseApi.generate({
      requirement_ids: selectedIds.value,
      project_id: selectedProject.value || undefined,
    })

    ElMessage.success(`已开始生成测试用例，任务ID: ${result.task_id}`)
    
    // 跳转到任务记录页面
    router.push('/ai-cases/task-records')
  } catch (error: any) {
    ElMessage.error(error.message || '生成失败')
  } finally {
    isGenerating.value = false
    generatingIds.value = []
  }
}

// 单个功能点生成测试用例
async function handleGenerateSingle(req: Requirement) {
  try {
    isGenerating.value = true
    generatingIds.value = [req.id]

    const result = await testcaseApi.generate({
      requirement_ids: [req.id],
      project_id: req.project_id || undefined,
    })

    ElMessage.success(`已开始为「${req.name}」生成测试用例`)
    
    // 跳转到任务记录页面
    router.push('/ai-cases/task-records')
  } catch (error: any) {
    ElMessage.error(error.message || '生成失败')
  } finally {
    isGenerating.value = false
    generatingIds.value = []
  }
}

// 监听项目筛选变化
watch(selectedProject, () => {
  handleSearch()
})
</script>

<template>
  <div class="function-points-page p-6">
    <!-- 页面标题 -->
    <div class="mb-6">
      <h1 class="text-2xl font-semibold text-text-primary">需求管理</h1>
      <p class="text-text-secondary text-sm mt-1">
        管理功能点，支持批量生成测试用例
      </p>
    </div>

    <!-- 筛选和操作 -->
    <div class="card mb-4">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-text-primary">功能点列表</h3>
        <div class="flex items-center gap-2">
          <!-- 批量操作按钮 -->
          <button
            v-if="selectedIds.length > 0"
            @click="handleGenerateTestCases"
            :disabled="isGenerating"
            class="btn-primary flex items-center gap-2"
          >
            <Loader v-if="isGenerating" class="w-4 h-4 animate-spin" />
            <TestTube v-else class="w-4 h-4" />
            生成测试用例 ({{ selectedIds.length }})
          </button>
          <button
            v-if="selectedIds.length > 0"
            @click="handleBatchDelete"
            class="btn-danger flex items-center gap-2"
          >
            <Trash2 class="w-4 h-4" />
            批量删除 ({{ selectedIds.length }})
          </button>
          <button @click="handleCreate" class="btn-primary flex items-center gap-2">
            <Plus class="w-4 h-4" />
            新建功能点
          </button>
        </div>
      </div>

      <div class="flex flex-wrap items-center gap-4">
        <div class="flex items-center gap-2">
          <label class="text-sm text-text-secondary">项目：</label>
          <select v-model="selectedProject" class="input-field w-48">
            <option :value="undefined">全部项目</option>
            <option v-for="project in projectStore.projects" :key="project.id" :value="project.id">
              {{ project.name }}
            </option>
          </select>
        </div>
        <div class="flex items-center gap-2">
          <label class="text-sm text-text-secondary">类别：</label>
          <select v-model="selectedCategory" @change="handleSearch" class="input-field w-32">
            <option value="">全部</option>
            <option v-for="cat in categoryOptions" :key="cat" :value="cat">{{ cat }}</option>
          </select>
        </div>
        <div class="flex items-center gap-2">
          <label class="text-sm text-text-secondary">优先级：</label>
          <select v-model="selectedPriority" @change="handleSearch" class="input-field w-24">
            <option value="">全部</option>
            <option v-for="pri in priorityOptions" :key="pri" :value="pri">{{ pri }}</option>
          </select>
        </div>
        <div class="flex items-center gap-2">
          <label class="text-sm text-text-secondary">所属需求：</label>
          <select v-model="selectedRequirementName" @change="handleSearch" class="input-field w-40">
            <option value="">全部</option>
            <option v-for="name in requirementNames" :key="name" :value="name">{{ name }}</option>
          </select>
        </div>
        <div class="flex items-center gap-2 flex-1 min-w-[200px]">
          <input
            v-model="keyword"
            type="text"
            placeholder="搜索功能点..."
            class="input-field flex-1"
            @keyup.enter="handleSearch"
          />
        </div>
        <button @click="handleSearch" class="btn-primary">搜索</button>
        <button @click="handleReset" class="btn-secondary">重置</button>
      </div>
    </div>

    <!-- 功能点列表 -->
    <div class="card">
      <div v-if="requirementStore.loading" class="text-center py-10">
        加载中...
      </div>
      <div v-else-if="requirementStore.requirements.length === 0" class="text-center py-10 text-text-secondary">
        暂无功能点
      </div>
      <div v-else>
        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-200">
              <th class="w-10 py-3 px-4">
                <input
                  type="checkbox"
                  :checked="isAllSelected"
                  @change="handleSelectAll"
                  class="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary cursor-pointer"
                />
              </th>
              <th class="text-left py-3 px-4 text-sm font-medium text-text-secondary">功能点名称</th>
              <th class="text-left py-3 px-4 text-sm font-medium text-text-secondary">所属需求</th>
              <th class="text-left py-3 px-4 text-sm font-medium text-text-secondary">项目</th>
              <th class="text-left py-3 px-4 text-sm font-medium text-text-secondary">模块</th>
              <th class="text-left py-3 px-4 text-sm font-medium text-text-secondary">类别</th>
              <th class="text-left py-3 px-4 text-sm font-medium text-text-secondary">优先级</th>
              <th class="text-left py-3 px-4 text-sm font-medium text-text-secondary">创建时间</th>
              <th class="text-right py-3 px-4 text-sm font-medium text-text-secondary">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="req in requirementStore.requirements"
              :key="req.id"
              class="border-b border-gray-100 hover:bg-gray-50 transition-colors"
              :class="{ 'bg-primary/5': selectedIds.includes(req.id) }"
            >
              <td class="py-3 px-4" @click.stop>
                <input
                  type="checkbox"
                  v-model="selectedIds"
                  :value="req.id"
                  class="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary cursor-pointer"
                />
              </td>
              <td class="py-3 px-4">
                <span class="text-sm font-medium text-primary cursor-pointer hover:text-primary/80" @click="handleView(req)">
                  {{ req.name }}
                </span>
              </td>
              <td class="py-3 px-4 text-sm text-text-secondary">
                {{ req.requirement_name || '-' }}
              </td>
              <td class="py-3 px-4 text-sm text-text-secondary">
                {{ getProjectName(req.project_id) }}
              </td>
              <td class="py-3 px-4 text-sm text-text-secondary">
                {{ req.module || '-' }}
              </td>
              <td class="py-3 px-4 text-sm text-text-secondary">
                {{ req.category || '-' }}
              </td>
              <td class="py-3 px-4">
                <span
                  v-if="req.priority"
                  :class="[
                    'px-2 py-0.5 rounded text-xs',
                    req.priority === '高' ? 'bg-red-100 text-red-700' :
                    req.priority === '中' ? 'bg-orange-100 text-orange-700' :
                    'bg-green-100 text-green-700'
                  ]"
                >
                  {{ req.priority }}
                </span>
                <span v-else class="text-text-placeholder">-</span>
              </td>
              <td class="py-3 px-4 text-sm text-text-secondary">
                {{ formatDateTime(req.created_at) }}
              </td>
              <td class="py-3 px-4">
                <div class="flex items-center justify-end gap-2">
                  <button
                    class="p-1.5 text-text-secondary hover:text-primary hover:bg-primary/10 rounded transition-colors"
                    @click="handleGenerateSingle(req)"
                    :disabled="isGenerating && generatingIds.includes(req.id)"
                    title="生成测试用例"
                  >
                    <Loader v-if="isGenerating && generatingIds.includes(req.id)" class="w-4 h-4 animate-spin" />
                    <TestTube v-else class="w-4 h-4" />
                  </button>
                  <button
                    class="p-1.5 text-text-secondary hover:text-primary hover:bg-primary/10 rounded transition-colors"
                    @click="handleView(req)"
                    title="查看"
                  >
                    <View class="w-4 h-4" />
                  </button>
                  <button
                    class="p-1.5 text-text-secondary hover:text-primary hover:bg-primary/10 rounded transition-colors"
                    @click="handleEdit(req)"
                    title="编辑"
                  >
                    <Edit class="w-4 h-4" />
                  </button>
                  <button
                    class="p-1.5 text-text-secondary hover:text-red-500 hover:bg-red-50 rounded transition-colors"
                    @click="handleDelete(req)"
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
            共 {{ requirementStore.total }} 条记录
          </div>
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="requirementStore.total"
            layout="total, sizes, prev, pager, next, jumper"
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
            <h3 class="text-xl font-bold text-white">功能点详情</h3>
          </div>
          <button 
            @click="showDetail = false" 
            class="text-white/80 hover:text-white transition-colors p-1 hover:bg-white/10 rounded-lg"
          >
            <X class="w-6 h-6" />
          </button>
        </div>

        <!-- Content -->
        <div v-if="detailRequirement" class="flex-1 overflow-y-auto p-6 space-y-4">
          <!-- 基本信息 -->
          <DetailCard title="基本信息" :icon="FileText">
            <div class="grid grid-cols-2 gap-6">
              <EditableField
                label="功能点名称"
                :model-value="detailRequirement.name"
                :editable="false"
                :span="2"
              />
              <EditableField
                label="功能点描述"
                :model-value="detailRequirement.description"
                :editable="false"
                type="textarea"
                :span="2"
              />
              <EditableField
                label="所属项目"
                :model-value="projectStore.projects.find(p => p.id === detailRequirement.project_id)?.name"
                :editable="false"
              />
              <EditableField
                label="所属版本"
                :model-value="versionStore.versions.find(v => v.id === detailRequirement.version_id)?.version_name"
                :editable="false"
              />
              <EditableField
                label="所属模块"
                :model-value="detailRequirement.module"
                :editable="false"
              />
              <EditableField
                label="所属需求"
                :model-value="detailRequirement.requirement_name"
                :editable="false"
              />
            </div>
          </DetailCard>

          <!-- 属性信息 -->
          <DetailCard title="属性信息" :icon="Settings">
            <div class="grid grid-cols-4 gap-6">
              <div>
                <label class="block text-sm font-medium text-text-secondary mb-2">类别</label>
                <p class="text-text-primary">{{ detailRequirement.category || '-' }}</p>
              </div>
              <div>
                <label class="block text-sm font-medium text-text-secondary mb-2">优先级</label>
                <StatusBadge
                  v-if="detailRequirement.priority"
                  :status="detailRequirement.priority"
                  type="priority"
                />
                <span v-else class="text-text-placeholder">-</span>
              </div>
              <div>
                <label class="block text-sm font-medium text-text-secondary mb-2">创建时间</label>
                <p class="text-text-primary">{{ formatDateTime(detailRequirement.created_at) }}</p>
              </div>
              <div>
                <label class="block text-sm font-medium text-text-secondary mb-2">更新时间</label>
                <p class="text-text-primary">{{ formatDateTime(detailRequirement.updated_at) }}</p>
              </div>
            </div>
          </DetailCard>

          <!-- 验收标准 -->
          <DetailCard title="验收标准" :icon="CheckCircle">
            <EditableField
              :model-value="detailRequirement.acceptance_criteria"
              :editable="false"
              type="textarea"
              :rows="4"
            />
          </DetailCard>

          <!-- 关键词 -->
          <DetailCard title="关键词" :icon="Tag">
            <div class="flex flex-wrap gap-2">
              <span
                v-for="(keyword, index) in detailRequirement.keywords?.split(',').filter(k => k.trim())"
                :key="index"
                class="px-3 py-1 bg-blue-50 text-blue-600 rounded-full text-sm"
              >
                {{ keyword.trim() }}
              </span>
              <span v-if="!detailRequirement.keywords" class="text-text-placeholder">-</span>
            </div>
          </DetailCard>

          <!-- 关联测试用例 -->
          <DetailCard title="关联测试用例" :icon="CheckSquare">
            <div class="text-center py-12">
              <CheckSquare class="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p class="text-text-secondary">暂无关联的测试用例</p>
            </div>
          </DetailCard>
        </div>
      </div>
    </div>

    <!-- 新建/编辑对话框 -->
    <div v-if="dialogVisible" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-6" @click.self="dialogVisible = false">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-5xl max-h-[90vh] overflow-hidden flex flex-col">
        <!-- Header -->
        <div class="bg-gradient-to-r from-blue-500 to-cyan-500 px-6 py-5 flex items-center justify-between flex-shrink-0">
          <div class="flex items-center gap-3">
            <Edit class="w-6 h-6 text-white" />
            <h3 class="text-xl font-bold text-white">{{ dialogTitle }}</h3>
          </div>
          <button
            @click="dialogVisible = false"
            class="text-white/80 hover:text-white transition-colors p-1.5 hover:bg-white/10 rounded-lg"
          >
            <X class="w-6 h-6" />
          </button>
        </div>

        <!-- Body -->
        <div class="flex-1 overflow-y-auto p-6 space-y-4">
          <!-- 基本信息 -->
          <DetailCard title="基本信息" :icon="FileText">
            <div class="grid grid-cols-2 gap-6">
              <EditableField
                label="功能点名称"
                v-model="formData.name"
                editable
                required
                :span="2"
              />
              <EditableField
                label="功能点描述"
                v-model="formData.description"
                editable
                type="textarea"
                :span="2"
                :rows="3"
              />
              <EditableField
                label="所属项目"
                v-model="formData.project_id"
                editable
                type="select"
                required
                :options="projectStore.projects.map(p => ({ label: p.name, value: p.id }))"
              />
              <EditableField
                label="所属模块"
                v-model="formData.module"
                editable
                placeholder="请输入所属模块"
              />
            </div>
          </DetailCard>

          <!-- 属性设置 -->
          <DetailCard title="属性设置" :icon="Settings">
            <div class="grid grid-cols-2 gap-6">
              <EditableField
                label="类别"
                v-model="formData.category"
                editable
                type="select"
                :options="categoryOptions.map(c => ({ label: c, value: c }))"
                placeholder="请选择类别"
              />
              <EditableField
                label="优先级"
                v-model="formData.priority"
                editable
                type="select"
                :options="priorityOptions.map(p => ({ label: p, value: p }))"
                placeholder="请选择优先级"
              />
            </div>
          </DetailCard>

          <!-- 验收标准 -->
          <DetailCard title="验收标准" :icon="CheckCircle">
            <EditableField
              v-model="formData.acceptance_criteria"
              editable
              type="textarea"
              :rows="4"
              placeholder="请输入验收标准"
            />
          </DetailCard>

          <!-- 关键词 -->
          <DetailCard title="关键词" :icon="Tag">
            <EditableField
              v-model="formData.keywords"
              editable
              placeholder="多个关键词用逗号分隔"
            />
          </DetailCard>
        </div>

        <!-- Footer -->
        <div class="border-t border-gray-200 px-6 py-4 flex justify-end gap-3 bg-gray-50">
          <button @click="dialogVisible = false" class="btn-secondary">取消</button>
          <button @click="handleSave" class="btn-primary flex items-center gap-2">
            <Save class="w-4 h-4" />
            保存
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.function-points-page {
  max-width: 1400px;
  margin: 0 auto;
}
</style>
