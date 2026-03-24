<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Edit, Delete, View, Trash2 } from 'lucide-vue-next'
import useRequirementStore from '@/stores/requirement'
import useProjectStore from '@/stores/project'
import useVersionStore from '@/stores/version'
import type { Requirement, RequirementCreate, RequirementUpdate } from '@/types/requirement'
import { formatDateTime } from '@/utils/date'

const router = useRouter()
const route = useRoute()
const requirementStore = useRequirementStore()
const projectStore = useProjectStore()
const versionStore = useVersionStore()

// 搜索筛选
const keyword = ref('')
const selectedProject = ref<number | undefined>()
const selectedVersion = ref<number | undefined>()
const selectedCategory = ref<string>('')
const selectedPriority = ref<string>('')
const selectedRequirementName = ref<string>('') // 新增：所属需求筛选
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

// 检查是否选中
const isSelected = (id: number) => selectedIds.value.includes(id)

// 对话框
const dialogVisible = ref(false)
const dialogTitle = ref('新建功能点')
const isEdit = ref(false)
const editingId = ref<number | null>(null)
const formData = ref<RequirementCreate | RequirementUpdate>({
  name: '',
  project_id: 0,
  version_id: undefined,
  description: '',
  category: '',
  module: '',
  priority: '',
  acceptance_criteria: '',
  keywords: ''
})

// 详情弹窗
const showDetail = ref(false)
const detailRequirement = ref<Requirement | null>(null)

// 类别和优先级选项
const categoryOptions = ['功能需求', '非功能需求', '界面需求', '数据需求', '安全需求', '性能需求']
const priorityOptions = ['高', '中', '低']

// 总页数
const totalPages = computed(() => Math.ceil(requirementStore.total / pageSize.value))

// 过滤版本（根据选择的项目 - 用于对话框）
const filteredVersions = computed(() => {
  if (!formData.value.project_id) return []
  return versionStore.versions.filter(v => v.project_id === formData.value.project_id)
})

// 搜索区域的版本列表（根据选中的项目过滤）
const searchVersions = computed(() => {
  if (!selectedProject.value) return versionStore.versions
  return versionStore.versions.filter(v => v.project_id === selectedProject.value)
})

// 获取唯一的需求名称列表（根据当前筛选条件）
const requirementNames = computed(() => {
  const names = new Set<string>()
  requirementStore.requirements.forEach(r => {
    if (r.requirement_name) names.add(r.requirement_name)
  })
  return Array.from(names).sort()
})

// 加载数据
async function loadData() {
  await requirementStore.fetchRequirements({
    page: currentPage.value,
    page_size: pageSize.value,
    project_id: selectedProject.value,
    version_id: selectedVersion.value,
    category: selectedCategory.value || undefined,
    priority: selectedPriority.value || undefined,
    requirement_name: selectedRequirementName.value || undefined, // 新增：需求名称筛选
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

// 获取版本名称
function getVersionName(versionId: number | null): string {
  if (!versionId) return '-'
  const version = versionStore.versions.find(v => v.id === versionId)
  return version?.version_name || version?.version_number || '-'
}

// 获取项目名称
function getProjectName(projectId: number): string {
  const project = projectStore.projects.find(p => p.id === projectId)
  return project?.name || '-'
}

// 格式化日期
function formatDate(date: string | null): string {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN')
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
  selectedVersion.value = undefined
  selectedCategory.value = ''
  selectedPriority.value = ''
  selectedRequirementName.value = '' // 新增
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
  currentPage.value = 1
  loadData()
}

// 新建功能点
function handleCreate() {
  isEdit.value = false
  dialogTitle.value = '新建功能点'
  formData.value = {
    name: '',
    project_id: selectedProject.value || (projectStore.projects[0]?.id ?? 0),
    version_id: undefined,
    description: '',
    category: '',
    module: '',
    priority: '',
    acceptance_criteria: '',
    keywords: ''
  }
  dialogVisible.value = true
}

// 项目变化时清空版本选择
function handleProjectChange() {
  formData.value.version_id = undefined
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
function handleView(req: Requirement) {
  detailRequirement.value = req
  showDetail.value = true
}

// 删除功能点
async function handleDelete(req: Requirement) {
  try {
    await ElMessageBox.confirm(
      `确定要删除功能点「${req.name}」吗？`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await requirementStore.deleteRequirement(req.id)
    ElMessage.success('删除成功')
    loadData()
  } catch {
    // 用户取消
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
        type: 'warning'
      }
    )
    
    await requirementStore.batchDeleteRequirements(selectedIds.value)
    ElMessage.success(`成功删除 ${selectedIds.value.length} 个功能点`)
    selectedIds.value = []
    loadData()
  } catch {
    // 用户取消
  }
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
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

// 监听项目变化
watch(selectedProject, () => {
  selectedVersion.value = undefined  // 清空版本选择
  currentPage.value = 1
  loadData()
})

// 初始化
onMounted(async () => {
  // 如果有路由参数
  if (route.query.project_id) {
    selectedProject.value = Number(route.query.project_id)
  }
  
  // 加载项目列表
  await projectStore.fetchProjects({ page_size: 100 })
  
  // 加载版本列表
  await versionStore.fetchVersions({ page_size: 100 })
  
  // 加载功能点
  await loadData()
})
</script>

<template>
  <div class="requirement-list-page">
    <!-- 页面标题 -->
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-semibold text-text-primary">功能点管理</h1>
      <div class="flex items-center gap-3">
        <!-- 批量删除按钮 -->
        <button 
          v-if="selectedIds.length > 0"
          class="btn-danger flex items-center gap-2"
          @click="handleBatchDelete"
        >
          <Trash2 class="w-4 h-4" />
          批量删除 ({{ selectedIds.length }})
        </button>
        <button class="btn-primary flex items-center gap-2" @click="handleCreate">
          <Plus class="w-4 h-4" />
          新建功能点
        </button>
      </div>
    </div>

    <!-- 搜索筛选区 -->
    <div class="card mb-4">
      <div class="flex flex-wrap items-center gap-4">
        <!-- 项目选择 -->
        <div class="flex items-center gap-2">
          <label class="text-sm text-text-secondary whitespace-nowrap">项目：</label>
          <select 
            v-model="selectedProject" 
            class="input-field w-48"
            style="background-color: white; color: #303133;"
          >
            <option :value="undefined">全部项目</option>
            <option 
              v-for="project in projectStore.projects" 
              :key="project.id" 
              :value="project.id"
              style="background-color: white; color: #303133;"
            >
              {{ project.name }}
            </option>
          </select>
        </div>

        <!-- 版本选择 -->
        <div class="flex items-center gap-2">
          <label class="text-sm text-text-secondary whitespace-nowrap">版本：</label>
          <select 
            v-model="selectedVersion" 
            class="input-field w-40"
            style="background-color: white; color: #303133;"
            @change="handleSearch"
          >
            <option :value="undefined">全部版本</option>
            <option 
              v-for="version in searchVersions" 
              :key="version.id" 
              :value="version.id"
              style="background-color: white; color: #303133;"
            >
              {{ version.version_name || version.version_number }}
            </option>
          </select>
        </div>

        <!-- 关键词搜索 -->
        <div class="flex items-center gap-2 flex-1 min-w-[200px]">
          <div class="relative flex-1">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-placeholder" />
            <input 
              v-model="keyword"
              type="text" 
              placeholder="搜索功能点名称..." 
              class="input-field pl-10 w-full"
              @keyup.enter="handleSearch"
            />
          </div>
        </div>

        <!-- 类别筛选 -->
        <div class="flex items-center gap-2">
          <label class="text-sm text-text-secondary whitespace-nowrap">类别：</label>
          <select 
            v-model="selectedCategory" 
            class="input-field w-32"
            style="background-color: white; color: #303133;"
            @change="handleSearch"
          >
            <option value="">全部</option>
            <option v-for="cat in categoryOptions" :key="cat" :value="cat" style="background-color: white; color: #303133;">{{ cat }}</option>
          </select>
        </div>

        <!-- 优先级筛选 -->
        <div class="flex items-center gap-2">
          <label class="text-sm text-text-secondary whitespace-nowrap">优先级：</label>
          <select 
            v-model="selectedPriority" 
            class="input-field w-24"
            style="background-color: white; color: #303133;"
            @change="handleSearch"
          >
            <option value="">全部</option>
            <option v-for="p in priorityOptions" :key="p" :value="p" style="background-color: white; color: #303133;">{{ p }}</option>
          </select>
        </div>

        <!-- 所属需求筛选 -->
        <div class="flex items-center gap-2">
          <label class="text-sm text-text-secondary whitespace-nowrap">所属需求：</label>
          <select 
            v-model="selectedRequirementName" 
            class="input-field w-48"
            style="background-color: white; color: #303133;"
            @change="handleSearch"
          >
            <option value="">全部</option>
            <option v-for="name in requirementNames" :key="name" :value="name" style="background-color: white; color: #303133;">{{ name }}</option>
          </select>
        </div>

        <!-- 排序 -->
        <div class="flex items-center gap-2">
          <label class="text-sm text-text-secondary whitespace-nowrap">排序：</label>
          <select 
            v-model="sortBy" 
            class="input-field w-28"
            @change="handleSearch"
          >
            <option value="created_at">创建时间</option>
            <option value="updated_at">更新时间</option>
            <option value="priority">优先级</option>
          </select>
          <select 
            v-model="sortOrder" 
            class="input-field w-20"
            @change="handleSearch"
          >
            <option value="desc">降序</option>
            <option value="asc">升序</option>
          </select>
        </div>

        <!-- 操作按钮 -->
        <div class="flex items-center gap-2">
          <button class="btn-secondary" @click="handleSearch">搜索</button>
          <button class="btn-ghost" @click="handleReset">重置</button>
        </div>
      </div>
    </div>

    <!-- 数据列表 -->
    <div class="card">
      <div v-if="requirementStore.loading" class="text-center py-10">
        加载中...
      </div>
      <div v-else-if="requirementStore.requirements.length === 0" class="text-center py-10 text-text-secondary">
        暂无功能点，点击"新建功能点"添加
      </div>
      <div v-else>
        <!-- 表格 -->
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
              <th class="text-left py-3 px-4 text-sm font-medium text-text-secondary">版本</th>
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
              class="border-b border-gray-100 hover:bg-background-secondary transition-colors"
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
                <div 
                  class="text-sm font-medium text-primary cursor-pointer hover:text-primary/80 transition-colors"
                  @click="handleView(req)"
                >
                  {{ req.name }}
                </div>
              </td>
              <td class="py-3 px-4">
                <span class="text-sm text-text-secondary">
                  {{ req.requirement_name || '-' }}
                </span>
              </td>
              <td class="py-3 px-4 text-sm text-text-secondary">
                {{ getProjectName(req.project_id) }}
              </td>
              <td class="py-3 px-4 text-sm text-text-secondary">
                {{ req.module || '-' }}
              </td>
              <td class="py-3 px-4 text-sm text-text-secondary">
                {{ getVersionName(req.version_id) }}
              </td>
              <td class="py-3 px-4">
                <span v-if="req.category" class="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs">
                  {{ req.category }}
                </span>
                <span v-else class="text-text-placeholder">-</span>
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
                    @click="handleView(req)"
                    title="查看详情"
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
                    <Delete class="w-4 h-4" />
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
          <div class="flex items-center gap-2">
            <select 
              v-model="pageSize" 
              class="input-field w-20"
              @change="handleSizeChange(pageSize)"
            >
              <option :value="10">10条</option>
              <option :value="20">20条</option>
              <option :value="50">50条</option>
            </select>
            <div class="flex items-center gap-1">
              <button 
                class="px-3 py-1.5 rounded border border-gray-200 text-sm disabled:opacity-50"
                :disabled="currentPage === 1"
                @click="handlePageChange(currentPage - 1)"
              >
                上一页
              </button>
              <span class="px-3 py-1.5 text-sm">
                {{ currentPage }} / {{ totalPages || 1 }}
              </span>
              <button 
                class="px-3 py-1.5 rounded border border-gray-200 text-sm disabled:opacity-50"
                :disabled="currentPage >= totalPages"
                @click="handlePageChange(currentPage + 1)"
              >
                下一页
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 新建/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px">
      <el-form :model="formData" label-width="100px">
        <!-- 功能点名称 -->
        <el-form-item label="功能点名称" required>
          <el-input v-model="formData.name" placeholder="请输入功能点名称" />
        </el-form-item>

        <!-- 项目选择 (仅新建时显示) -->
        <el-form-item v-if="!isEdit" label="所属项目" required>
          <el-select v-model="formData.project_id" placeholder="请选择项目" @change="handleProjectChange">
            <el-option
              v-for="project in projectStore.projects"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
        </el-form-item>

        <!-- 版本选择 (仅新建时显示) -->
        <el-form-item v-if="!isEdit" label="关联版本">
          <el-select v-model="formData.version_id" placeholder="不关联版本" clearable>
            <el-option
              v-for="version in filteredVersions"
              :key="version.id"
              :label="version.version_name || version.version_number"
              :value="version.id"
            />
          </el-select>
        </el-form-item>

        <!-- 描述 -->
        <el-form-item label="功能点描述">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="4"
            placeholder="请输入功能点描述"
          />
        </el-form-item>

        <!-- 类别和优先级 -->
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="类别">
              <el-select v-model="formData.category" placeholder="请选择" clearable>
                <el-option
                  v-for="cat in categoryOptions"
                  :key="cat"
                  :label="cat"
                  :value="cat"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="优先级">
              <el-select v-model="formData.priority" placeholder="请选择" clearable>
                <el-option
                  v-for="p in priorityOptions"
                  :key="p"
                  :label="p"
                  :value="p"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 所属模块 -->
        <el-form-item label="所属模块">
          <el-input v-model="formData.module" placeholder="请输入所属模块" />
        </el-form-item>

        <!-- 验收标准 -->
        <el-form-item label="验收标准">
          <el-input
            v-model="formData.acceptance_criteria"
            type="textarea"
            :rows="3"
            placeholder="请输入验收标准"
          />
        </el-form-item>

        <!-- 关键词 -->
        <el-form-item label="关键词">
          <el-input v-model="formData.keywords" placeholder="多个关键词用逗号分隔" />
        </el-form-item>
      </el-form>
      <template #footer>
        <button class="btn-secondary" @click="dialogVisible = false">取消</button>
        <button class="btn-primary ml-2" @click="handleSave">确定</button>
      </template>
    </el-dialog>

    <!-- 详情弹窗 -->
    <div
      v-if="showDetail && detailRequirement"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      @click.self="showDetail = false"
    >
      <div class="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <div class="p-6">
          <!-- 弹窗标题 -->
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-xl font-semibold text-text-primary">功能点详情</h2>
            <button
              class="text-text-secondary hover:text-text-primary transition-colors"
              @click="showDetail = false"
            >
              ✕
            </button>
          </div>

          <!-- 基本信息 -->
          <div class="space-y-4">
            <div>
              <label class="text-sm text-text-secondary">功能点名称</label>
              <p class="text-text-primary font-medium">{{ detailRequirement.name }}</p>
            </div>

            <div class="grid grid-cols-3 gap-4">
              <div>
                <label class="text-sm text-text-secondary">所属项目</label>
                <p class="text-text-primary">{{ getProjectName(detailRequirement.project_id) }}</p>
              </div>
              <div>
                <label class="text-sm text-text-secondary">所属版本</label>
                <p class="text-text-primary">{{ getVersionName(detailRequirement.version_id) }}</p>
              </div>
              <div>
                <label class="text-sm text-text-secondary">所属模块</label>
                <p class="text-text-primary">{{ detailRequirement.module || '-' }}</p>
              </div>
            </div>

            <div class="grid grid-cols-3 gap-4">
              <div>
                <label class="text-sm text-text-secondary">类别</label>
                <p class="text-text-primary">{{ detailRequirement.category || '-' }}</p>
              </div>
              <div>
                <label class="text-sm text-text-secondary">优先级</label>
                <p class="text-text-primary">{{ detailRequirement.priority || '-' }}</p>
              </div>
              <div>
                <label class="text-sm text-text-secondary">关键词</label>
                <p class="text-text-primary">{{ detailRequirement.keywords || '-' }}</p>
              </div>
            </div>

            <div>
              <label class="text-sm text-text-secondary">功能点描述</label>
              <p class="text-text-primary whitespace-pre-wrap">
                {{ detailRequirement.description || '无' }}
              </p>
            </div>

            <div>
              <label class="text-sm text-text-secondary">验收标准</label>
              <p class="text-text-primary whitespace-pre-wrap">
                {{ detailRequirement.acceptance_criteria || '无' }}
              </p>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="text-sm text-text-secondary">创建时间</label>
                <p class="text-text-primary">{{ formatDate(detailRequirement.created_at) }}</p>
              </div>
              <div>
                <label class="text-sm text-text-secondary">更新时间</label>
                <p class="text-text-primary">{{ formatDate(detailRequirement.updated_at) }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
