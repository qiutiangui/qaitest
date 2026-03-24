<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Upload, FileText, Send, Loader, CheckCircle, XCircle, RefreshCw, Eye, RotateCcw, Clock, Trash2, Layers, ListChecks, ChevronRight, Plus, Settings } from 'lucide-vue-next'
import { ElMessage, ElMessageBox } from 'element-plus'
import useProjectStore from '@/stores/project'
import useVersionStore from '@/stores/version'
import useRequirementStore from '@/stores/requirement'
import { requirementApi } from '@/api/requirement'
import { aiTasksApi } from '@/api/aiTasks'
import type { Project } from '@/types/project'
import type { Requirement } from '@/types/requirement'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()
const versionStore = useVersionStore()
const requirementStore = useRequirementStore()

// Tab 切换
const activeTab = ref('analyze') // 'analyze' | 'requirements' | 'functions'

// ==================== Tab1: 需求分析 ====================
const requirementName = ref('')
const selectedProjectId = ref<number | null>(null)
const selectedVersionId = ref<number | null>(null)
const requirementDescription = ref('')
const uploadedFile = ref<File | null>(null)
const fileName = ref('')

// 模型选择
const selectedRequirementAnalyzeModel = ref('')

// 状态
const isAnalyzing = ref(false)
const taskId = ref('')
const analysisComplete = ref(false)
const savedRequirementIds = ref<number[]>([])

// 轮询相关
const pollInterval = ref<number | null>(null)

// 项目和版本列表
const projects = computed(() => projectStore.projects)
const versions = computed(() => {
  if (!selectedProjectId.value) return []
  return versionStore.versions.filter(v => v.project_id === selectedProjectId.value)
})

onMounted(async () => {
  await projectStore.fetchProjects({ page_size: 100 })
  // 加载所有版本数据用于Tab2显示
  await versionStore.fetchVersions({ page_size: 100 })

  if (route.query.project_id) {
    selectedProjectId.value = Number(route.query.project_id)
    await loadVersions()
  }

  // 加载需求数据用于Tab2
  loadRequirementGroups()
})

const loadVersions = async () => {
  if (selectedProjectId.value) {
    await versionStore.fetchVersions({ project_id: selectedProjectId.value })
  }
}

const handleProjectChange = () => {
  selectedVersionId.value = null
  loadVersions()
}

const handleFileUpload = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files[0]) {
    const file = target.files[0]
    const validTypes = ['.txt', '.md', '.pdf', '.docx']
    const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase()

    if (!validTypes.includes(ext)) {
      ElMessage.warning('请上传 txt、md、pdf 或 docx 格式的文件')
      return
    }

    uploadedFile.value = file
    fileName.value = file.name
    ElMessage.success(`文件已选择: ${file.name}`)
  }
}

const clearFile = () => {
  uploadedFile.value = null
  fileName.value = ''
}

const startAnalysis = async () => {
  if (!selectedProjectId.value) {
    ElMessage.warning('请选择项目')
    return
  }

  if (!requirementDescription.value && !uploadedFile.value) {
    ElMessage.warning('请输入需求描述或上传需求文档')
    return
  }

  isAnalyzing.value = true
  analysisComplete.value = false
  savedRequirementIds.value = []

  taskId.value = `task-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`

  try {
    const formData = new FormData()
    formData.append('project_id', String(selectedProjectId.value))
    formData.append('requirement_name', requirementName.value)
    if (selectedVersionId.value) {
      formData.append('version_id', String(selectedVersionId.value))
    }
    formData.append('description', requirementDescription.value)
    if (uploadedFile.value) {
      formData.append('file', uploadedFile.value)
    }

    // 构建模型配置
    const modelConfig: any = {}
    if (selectedRequirementAnalyzeModel.value) {
      modelConfig.requirement_analyze_model = selectedRequirementAnalyzeModel.value
    }

    const result = await requirementApi.analyze(formData, modelConfig)
    taskId.value = result.task_id

    // 启动轮询查询任务状态
    startPolling(result.task_id)

  } catch (error: any) {
    ElMessage.error(error.message || '启动分析失败')
    isAnalyzing.value = false
  }
}

// 轮询查询任务状态
const startPolling = (currentTaskId: string) => {
  stopPolling()
  pollInterval.value = window.setInterval(async () => {
    try {
      const result = await aiTasksApi.getRequirementTask(currentTaskId)
      
      if (result.status === 'completed') {
        stopPolling()
        handleAnalysisComplete({ saved_ids: result.saved_ids })
      } else if (result.status === 'failed') {
        stopPolling()
        handleAnalysisError(result.error_message || '需求分析失败')
      }
    } catch (error) {
      console.error('查询任务状态失败:', error)
    }
  }, 2000)
}

// 停止轮询
const stopPolling = () => {
  if (pollInterval.value) {
    clearInterval(pollInterval.value)
    pollInterval.value = null
  }
}

const handleAnalysisComplete = (data: any) => {
  isAnalyzing.value = false
  analysisComplete.value = true

  if (data?.saved_ids) {
    savedRequirementIds.value = data.saved_ids
    ElMessage.success(`需求分析完成！提取了 ${data.saved_ids.length} 个功能点`)
    // 刷新需求列表
    loadRequirementGroups()
  }
}

const handleAnalysisError = (message: string) => {
  isAnalyzing.value = false
  ElMessage.error(`分析失败: ${message}`)
}

const goToRequirementList = () => {
  activeTab.value = 'functions'
}

const resetForm = () => {
  requirementName.value = ''
  requirementDescription.value = ''
  uploadedFile.value = null
  fileName.value = ''
  analysisComplete.value = false
  savedRequirementIds.value = []
  stopPolling()
}

// ==================== Tab2: 需求列表（按requirement_name分组）====================
interface RequirementGroup {
  requirement_name: string
  project_id: number
  version_id: number | null
  count: number
  created_at: string
}

const requirementGroups = ref<RequirementGroup[]>([])
const groupsLoading = ref(false)
const groupFilterProject = ref<number | undefined>()

const loadRequirementGroups = async () => {
  groupsLoading.value = true
  try {
    const params = new URLSearchParams({ page_size: '100' })
    if (groupFilterProject.value) {
      params.append('project_id', String(groupFilterProject.value))
    }
    const response = await fetch(`/api/requirements/groups?${params}`)
    const data = await response.json()
    requirementGroups.value = data.items || []
  } catch (error) {
    console.error('加载需求分组失败:', error)
  } finally {
    groupsLoading.value = false
  }
}

const getProjectName = (projectId: number): string => {
  const project = projectStore.projects.find(p => p.id === projectId)
  return project?.name || '-'
}

const getVersionName = (versionId: number | null): string => {
  if (!versionId) return '项目级'
  const version = versionStore.versions.find(v => v.id === versionId)
  return version?.version_name || version?.version_number || '-'
}

const viewRequirementDetail = (group: RequirementGroup) => {
  activeTab.value = 'functions'
  requirementFilter.value = group.requirement_name
}

// 删除需求组
const deleteRequirementGroup = async (group: RequirementGroup) => {
  try {
    await ElMessageBox.confirm(
      `<p>确定删除需求「${group.requirement_name}」吗？</p>
       <p style="color: #e6a23c; margin-top: 10px;">⚠️ 删除后将同步执行以下操作：</p>
       <ul style="margin: 10px 0 0 20px;">
         <li>删除该需求下的所有功能点（共 ${group.count} 个）</li>
         <li>删除该需求在向量数据库中的检索数据</li>
       </ul>
       <p style="color: #f56c6c; margin-top: 10px;">此操作不可恢复，请谨慎操作！</p>`,
      '删除确认',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning', dangerouslyUseHTMLString: true }
    )
    
    // 调用后端API删除该需求下的所有功能点和向量数据
    const formData = new FormData()
    formData.append('project_id', String(group.project_id))
    formData.append('requirement_name', group.requirement_name)
    if (group.version_id) {
      formData.append('version_id', String(group.version_id))
    }
    
    const response = await fetch('/api/requirements/by-name/delete', {
      method: 'POST',
      body: formData
    })
    
    if (!response.ok) {
      throw new Error('删除失败')
    }
    
    const result = await response.json()
    console.log('删除结果:', result)
    
    ElMessage.success('删除成功')
    loadRequirementGroups()
  } catch {
    // 取消删除
  }
}

// ==================== Tab3: 功能点管理 ====================
const categoryOptions = ['功能需求', '非功能需求', '界面需求', '数据需求', '安全需求', '性能需求']
const selectedCategory = ref<string>('')
const requirementFilter = ref('')
const functionsProject = ref<number | undefined>()
const functionsVersion = ref<number | undefined>()
const functionsKeyword = ref('')
const functionsPage = ref(1)
const functionsPageSize = ref(10)
const functionsSortBy = ref('created_at')
const functionsSortOrder = ref<'asc' | 'desc'>('desc')

// 批量选择
const functionsSelectedIds = ref<number[]>([])
const isAllFunctionsSelected = computed(() => {
  return requirementStore.requirements.length > 0 &&
         functionsSelectedIds.value.length === requirementStore.requirements.length
})

const functionsVersions = computed(() => {
  if (!functionsProject.value) return versionStore.versions
  return versionStore.versions.filter(v => v.project_id === functionsProject.value)
})

// 获取唯一的需求名称列表
const requirementNames = computed(() => {
  const names = new Set<string>()
  requirementStore.requirements.forEach(r => {
    if (r.requirement_name) names.add(r.requirement_name)
  })
  return Array.from(names).sort()
})

const loadFunctions = async () => {
  await requirementStore.fetchRequirements({
    page: functionsPage.value,
    page_size: functionsPageSize.value,
    project_id: functionsProject.value,
    version_id: functionsVersion.value,
    category: selectedCategory.value || undefined,
    requirement_name: requirementFilter.value || undefined,
    keyword: functionsKeyword.value || undefined,
    sort_by: functionsSortBy.value,
    order: functionsSortOrder.value
  })
}

const functionsTotalPages = computed(() => Math.ceil(requirementStore.total / functionsPageSize.value))

const handleFunctionsSearch = () => {
  functionsPage.value = 1
  loadFunctions()
}

const handleFunctionsPageChange = (page: number) => {
  functionsPage.value = page
  loadFunctions()
}

const handleViewFunction = (req: Requirement) => {
  router.push(`/requirements/${req.id}`)
}

const handleEditFunction = (req: Requirement) => {
  router.push(`/requirements/${req.id}?edit=true`)
}

const handleDeleteFunction = async (req: Requirement) => {
  try {
    await ElMessageBox.confirm(`确定删除功能点「${req.name}」吗？`, '删除确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await requirementStore.deleteRequirement(req.id)
    ElMessage.success('删除成功')
    loadFunctions()
    functionsSelectedIds.value = functionsSelectedIds.value.filter(id => id !== req.id)
  } catch {
    // 取消删除
  }
}

// 全选/取消全选
const handleFunctionsSelectAll = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.checked) {
    functionsSelectedIds.value = requirementStore.requirements.map(r => r.id)
  } else {
    functionsSelectedIds.value = []
  }
}

// 批量删除功能点
const handleBatchDeleteFunctions = async () => {
  if (functionsSelectedIds.value.length === 0) {
    ElMessage.warning('请先选择要删除的功能点')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${functionsSelectedIds.value.length} 个功能点吗？`,
      '批量删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await requirementStore.batchDeleteRequirements(functionsSelectedIds.value)
    ElMessage.success(`成功删除 ${functionsSelectedIds.value.length} 个功能点`)
    functionsSelectedIds.value = []
    loadFunctions()
  } catch {
    // 取消删除
  }
}

// 监听Tab切换
watch(activeTab, (newTab) => {
  if (newTab === 'requirements') {
    loadRequirementGroups()
  } else if (newTab === 'functions') {
    loadFunctions()
  }
})

// 监听项目筛选变化
watch(functionsProject, () => {
  functionsVersion.value = undefined
  handleFunctionsSearch()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<template>
  <div class="requirement-analysis-page">
    <!-- 页面标题 -->
    <div class="mb-6">
      <h1 class="text-2xl font-semibold text-text-primary">AI需求分析</h1>
      <p class="text-text-secondary text-sm mt-1">
        AI智能提取功能点，统一管理需求和功能点
      </p>
    </div>

    <!-- Tab 切换 -->
    <div class="card mb-6">
      <div class="flex gap-6 border-b border-gray-200">
        <button
          @click="activeTab = 'analyze'"
          :class="[
            'pb-3 border-b-2 transition-colors',
            activeTab === 'analyze'
              ? 'border-primary text-primary font-medium'
              : 'border-transparent text-text-secondary hover:text-text-primary'
          ]"
        >
          <div class="flex items-center gap-2">
            <FileText class="w-4 h-4" />
            需求分析
          </div>
        </button>
        <button
          @click="activeTab = 'requirements'"
          :class="[
            'pb-3 border-b-2 transition-colors',
            activeTab === 'requirements'
              ? 'border-primary text-primary font-medium'
              : 'border-transparent text-text-secondary hover:text-text-primary'
          ]"
        >
          <div class="flex items-center gap-2">
            <Layers class="w-4 h-4" />
            需求列表
          </div>
        </button>
        <button
          @click="activeTab = 'functions'"
          :class="[
            'pb-3 border-b-2 transition-colors',
            activeTab === 'functions'
              ? 'border-primary text-primary font-medium'
              : 'border-transparent text-text-secondary hover:text-text-primary'
          ]"
        >
          <div class="flex items-center gap-2">
            <ListChecks class="w-4 h-4" />
            功能点管理
          </div>
        </button>
      </div>
    </div>

    <!-- ==================== Tab1: 需求分析 ==================== -->
    <div v-if="activeTab === 'analyze'">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- 左侧：输入区域 -->
        <div class="space-y-4">
          <!-- 项目和版本选择 -->
          <div class="card">
            <h3 class="text-lg font-medium text-text-primary mb-4">项目信息</h3>

            <div class="space-y-4">
              <div>
                <label class="block text-sm text-text-secondary mb-1">需求名称</label>
                <input
                  v-model="requirementName"
                  type="text"
                  class="input-field"
                  placeholder="例如：用户登录模块需求"
                />
                <p class="text-xs text-text-placeholder mt-1">
                  为本次需求分析命名，便于后续管理
                </p>
              </div>

              <div>
                <label class="block text-sm text-text-secondary mb-1">选择项目 *</label>
                <select
                  v-model="selectedProjectId"
                  @change="handleProjectChange"
                  class="input-field"
                >
                  <option :value="null">请选择项目</option>
                  <option v-for="project in projects" :key="project.id" :value="project.id">
                    {{ project.name }}
                  </option>
                </select>
              </div>

              <div>
                <label class="block text-sm text-text-secondary mb-1">选择版本（可选）</label>
                <select
                  v-model="selectedVersionId"
                  class="input-field"
                  :disabled="!selectedProjectId"
                >
                  <option :value="null">不关联版本</option>
                  <option v-for="version in versions" :key="version.id" :value="version.id">
                    {{ version.version_number }} ({{ version.status }})
                  </option>
                </select>
              </div>
            </div>
          </div>

          <!-- 文件上传 -->
          <div class="card">
            <h3 class="text-lg font-medium text-text-primary mb-4">需求文档</h3>

            <div
              class="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-primary transition-colors cursor-pointer"
              @click="$refs.fileInput?.click()"
            >
              <input
                ref="fileInput"
                type="file"
                accept=".txt,.md,.pdf,.docx"
                class="hidden"
                @change="handleFileUpload"
              />

              <div v-if="!fileName" class="space-y-2">
                <Upload class="w-10 h-10 mx-auto text-gray-400" />
                <p class="text-text-secondary">点击或拖拽上传需求文档</p>
                <p class="text-xs text-text-placeholder">支持 txt、md、pdf、docx 格式</p>
              </div>

              <div v-else class="flex items-center justify-center gap-2">
                <FileText class="w-5 h-5 text-primary" />
                <span class="text-text-primary">{{ fileName }}</span>
                <button
                  @click.stop="clearFile"
                  class="ml-2 text-gray-400 hover:text-red-500"
                >
                  <XCircle class="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>

          <!-- 需求描述 -->
          <div class="card">
            <h3 class="text-lg font-medium text-text-primary mb-4">需求描述</h3>

            <textarea
              v-model="requirementDescription"
              class="input-field min-h-[150px] resize-y"
              placeholder="请输入需求描述，例如：&#10;- 用户登录功能&#10;- 支持手机号和邮箱登录&#10;- 登录失败三次后需要验证码..."
            />
          </div>

          <!-- 操作按钮 -->
          <div class="flex gap-3">
            <button
              @click="startAnalysis"
              :disabled="isAnalyzing"
              class="btn-primary flex items-center gap-2 flex-1"
            >
              <Loader v-if="isAnalyzing" class="w-4 h-4 animate-spin" />
              <Send v-else class="w-4 h-4" />
              {{ isAnalyzing ? '分析中...' : '开始分析' }}
            </button>

            <button
              v-if="analysisComplete"
              @click="goToRequirementList"
              class="btn-secondary flex items-center gap-2"
            >
              <CheckCircle class="w-4 h-4" />
              查看功能点
            </button>

            <button
              v-if="analysisComplete"
              @click="resetForm"
              class="btn-secondary"
            >
              重新分析
            </button>
          </div>
        </div>

        <!-- 分析结果提示 -->
        <div v-if="analysisComplete && savedRequirementIds.length > 0" class="card mt-4 bg-green-50 border-green-200">
          <div class="flex items-start gap-3">
            <CheckCircle class="w-5 h-5 text-green-500 mt-0.5" />
            <div>
              <h4 class="text-green-700 font-medium">分析完成</h4>
              <p class="text-green-600 text-sm mt-1">
                成功提取并保存了 {{ savedRequirementIds.length }} 个功能点
              </p>
              <p class="text-green-500 text-xs mt-2">
                您可以在「功能点管理」中查看和编辑这些功能点
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ==================== Tab2: 需求列表 ==================== -->
    <div v-if="activeTab === 'requirements'">
      <!-- 筛选 -->
      <div class="card mb-4">
        <div class="flex items-center gap-4">
          <div class="flex items-center gap-2">
            <label class="text-sm text-text-secondary">项目：</label>
            <select v-model="groupFilterProject" @change="loadRequirementGroups" class="input-field w-48">
              <option :value="undefined">全部项目</option>
              <option v-for="project in projectStore.projects" :key="project.id" :value="project.id">
                {{ project.name }}
              </option>
            </select>
          </div>
          <button @click="loadRequirementGroups" class="btn-secondary flex items-center gap-2">
            <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': groupsLoading }" />
            刷新
          </button>
        </div>
      </div>

      <!-- 需求列表 -->
      <div v-if="groupsLoading" class="text-center py-10">
        <span class="text-text-secondary">加载中...</span>
      </div>
      <div v-else-if="requirementGroups.length === 0" class="card text-center py-10">
        <span class="text-text-secondary">暂无需求，请先进行需求分析</span>
      </div>
      <div v-else class="card">
        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-200">
              <th class="text-left py-3 px-4 text-sm font-medium text-text-secondary">需求名称</th>
              <th class="text-left py-3 px-4 text-sm font-medium text-text-secondary">项目</th>
              <th class="text-left py-3 px-4 text-sm font-medium text-text-secondary">版本</th>
              <th class="text-left py-3 px-4 text-sm font-medium text-text-secondary">功能点数量</th>
              <th class="text-left py-3 px-4 text-sm font-medium text-text-secondary">创建时间</th>
              <th class="text-right py-3 px-4 text-sm font-medium text-text-secondary">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="group in requirementGroups"
              :key="`${group.project_id}-${group.requirement_name}`"
              class="border-b border-gray-100 hover:bg-gray-50 transition-colors"
            >
              <td class="py-3 px-4">
                <span class="text-sm font-medium text-primary cursor-pointer hover:text-primary/80" @click="viewRequirementDetail(group)">
                  {{ group.requirement_name }}
                </span>
              </td>
              <td class="py-3 px-4 text-sm text-text-secondary">
                {{ getProjectName(group.project_id) }}
              </td>
              <td class="py-3 px-4 text-sm text-text-secondary">
                {{ getVersionName(group.version_id) }}
              </td>
              <td class="py-3 px-4">
                <span
                  class="px-2 py-0.5 bg-primary/10 text-primary rounded text-xs cursor-pointer hover:bg-primary/20"
                  @click="viewRequirementDetail(group)"
                >
                  {{ group.count }} 个功能点
                </span>
              </td>
              <td class="py-3 px-4 text-sm text-text-secondary">
                {{ new Date(group.created_at).toLocaleDateString() }}
              </td>
              <td class="py-3 px-4">
                <div class="flex items-center justify-end gap-2">
                  <button
                    class="p-1.5 text-text-secondary hover:text-primary hover:bg-primary/10 rounded transition-colors"
                    @click="viewRequirementDetail(group)"
                    title="查看功能点"
                  >
                    <ChevronRight class="w-4 h-4" />
                  </button>
                  <button
                    class="p-1.5 text-text-secondary hover:text-red-500 hover:bg-red-50 rounded transition-colors"
                    @click="deleteRequirementGroup(group)"
                    title="删除"
                  >
                    <Trash2 class="w-4 h-4" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ==================== Tab3: 功能点管理 ==================== -->
    <div v-if="activeTab === 'functions'">
      <!-- 筛选和操作 -->
      <div class="card mb-4">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-text-primary">功能点管理</h3>
          <div class="flex items-center gap-2">
            <!-- 批量删除按钮 -->
            <button
              v-if="functionsSelectedIds.length > 0"
              class="btn-danger flex items-center gap-2"
              @click="handleBatchDeleteFunctions"
            >
              <Trash2 class="w-4 h-4" />
              批量删除 ({{ functionsSelectedIds.length }})
            </button>
            <button class="btn-primary flex items-center gap-2" @click="router.push('/requirements')">
              <Plus class="w-4 h-4" />
              新建功能点
            </button>
          </div>
        </div>
        <div class="flex flex-wrap items-center gap-4">
          <div class="flex items-center gap-2">
            <label class="text-sm text-text-secondary">项目：</label>
            <select v-model="functionsProject" class="input-field w-48">
              <option :value="undefined">全部项目</option>
              <option v-for="project in projectStore.projects" :key="project.id" :value="project.id">
                {{ project.name }}
              </option>
            </select>
          </div>
          <div class="flex items-center gap-2">
            <label class="text-sm text-text-secondary">版本：</label>
            <select v-model="functionsVersion" @change="handleFunctionsSearch" class="input-field w-40">
              <option :value="undefined">全部版本</option>
              <option v-for="version in functionsVersions" :key="version.id" :value="version.id">
                {{ version.version_name || version.version_number }}
              </option>
            </select>
          </div>
          <div class="flex items-center gap-2">
            <label class="text-sm text-text-secondary">类别：</label>
            <select v-model="selectedCategory" @change="handleFunctionsSearch" class="input-field w-32">
              <option :value="undefined">全部</option>
              <option v-for="cat in categoryOptions" :key="cat" :value="cat">{{ cat }}</option>
            </select>
          </div>
          <div class="flex items-center gap-2 flex-1 min-w-[200px]">
            <input
              v-model="functionsKeyword"
              type="text"
              placeholder="搜索功能点..."
              class="input-field flex-1"
              @keyup.enter="handleFunctionsSearch"
            />
          </div>
          <div class="flex items-center gap-2">
            <label class="text-sm text-text-secondary">所属需求：</label>
            <select v-model="requirementFilter" @change="handleFunctionsSearch" class="input-field w-40">
              <option :value="undefined">全部</option>
              <option v-for="name in requirementNames" :key="name" :value="name">{{ name }}</option>
            </select>
          </div>
          <button @click="handleFunctionsSearch" class="btn-primary">搜索</button>
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
                    :checked="isAllFunctionsSelected"
                    @change="handleFunctionsSelectAll"
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
                class="border-b border-gray-100 hover:bg-gray-50 transition-colors"
                :class="{ 'bg-primary/5': functionsSelectedIds.includes(req.id) }"
              >
                <td class="py-3 px-4" @click.stop>
                  <input
                    type="checkbox"
                    v-model="functionsSelectedIds"
                    :value="req.id"
                    class="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary cursor-pointer"
                  />
                </td>
                <td class="py-3 px-4">
                  <span class="text-sm font-medium text-primary cursor-pointer hover:text-primary/80" @click="handleViewFunction(req)">
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
                  {{ getVersionName(req.version_id) }}
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
                  {{ new Date(req.created_at).toLocaleDateString() }}
                </td>
                <td class="py-3 px-4">
                  <div class="flex items-center justify-end gap-2">
                    <button
                      class="p-1.5 text-text-secondary hover:text-primary hover:bg-primary/10 rounded transition-colors"
                      @click="handleViewFunction(req)"
                      title="查看"
                    >
                      <Eye class="w-4 h-4" />
                    </button>
                    <button
                      class="p-1.5 text-text-secondary hover:text-red-500 hover:bg-red-50 rounded transition-colors"
                      @click="handleDeleteFunction(req)"
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
            <div class="flex items-center gap-2">
              <button
                class="px-3 py-1.5 rounded border border-gray-200 text-sm disabled:opacity-50"
                :disabled="functionsPage === 1"
                @click="handleFunctionsPageChange(functionsPage - 1)"
              >
                上一页
              </button>
              <span class="px-3 py-1.5 text-sm">
                {{ functionsPage }} / {{ functionsTotalPages || 1 }}
              </span>
              <button
                class="px-3 py-1.5 rounded border border-gray-200 text-sm disabled:opacity-50"
                :disabled="functionsPage >= functionsTotalPages"
                @click="handleFunctionsPageChange(functionsPage + 1)"
              >
                下一页
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>


  </div>

  <!-- 设置弹窗 -->
</template>

<style scoped>
.requirement-analysis-page {
  max-width: 1400px;
  margin: 0 auto;
}
</style>
