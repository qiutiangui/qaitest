<script setup lang="ts">
import { ref, onMounted, computed, watch, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Send, Loader, CheckCircle, ListChecks, TestTube, Eye, Trash2, Search, Download, FileSpreadsheet, FileText } from 'lucide-vue-next'
import { ElMessage } from 'element-plus'
import useProjectStore from '@/stores/project'
import useRequirementStore from '@/stores/requirement'
import useVersionStore from '@/stores/version'
import useTestcaseStore from '@/stores/testcase'
import { testcaseApi } from '@/api/testcase'
import { aiTasksApi } from '@/api/aiTasks'
import type { Requirement } from '@/types/requirement'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()
const requirementStore = useRequirementStore()
const versionStore = useVersionStore()
const testcaseStore = useTestcaseStore()

// Tab 切换
const activeTab = ref('generate') // 'generate' | 'list'

// ==================== Tab1: 用例生成 ====================
const selectedProjectId = ref<number | null>(null)
const selectedVersionId = ref<number | null>(null)
const selectedRequirementIds = ref<number[]>([])

const isGenerating = ref(false)
const taskId = ref('')
const generationComplete = ref(false)
const savedTestcaseIds = ref<number[]>([])

// 轮询相关
const pollInterval = ref<number | null>(null)

const requirements = computed(() => requirementStore.requirements)
const projects = computed(() => projectStore.projects)
const versions = computed(() => {
  if (!selectedProjectId.value) return []
  return versionStore.versions.filter(v => v.project_id === selectedProjectId.value)
})

// ==================== Tab2: 用例管理 ====================
const listSelectedProject = ref<number | undefined>()
const listSelectedPriority = ref<string | undefined>()
const listSelectedStatus = ref<string | undefined>()
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(10)

const showDetail = ref(false)
const detailTestcase = ref<any>(null)

const showExportDialog = ref(false)
const exportFormat = ref<'excel' | 'markdown'>('excel')
const exporting = ref(false)

const priorities = ['高', '中', '低']
const statuses = ['未开始', '进行中', '已完成', '已阻塞']

const totalPages = computed(() => Math.ceil(testcaseStore.total / pageSize.value))

// ==================== 生命周期 ====================
onMounted(async () => {
  await projectStore.fetchProjects({ page_size: 100 })
  
  if (route.query.project_id) {
    selectedProjectId.value = Number(route.query.project_id)
    listSelectedProject.value = Number(route.query.project_id)
    await loadRequirements()
    await loadVersions()
    await fetchTestcaseList()
  }
})

onUnmounted(() => {
  stopPolling()
})

// 监听Tab切换
watch(activeTab, (newTab) => {
  if (newTab === 'list') {
    fetchTestcaseList()
  }
})

// ==================== Tab1 方法 ====================
const loadRequirements = async () => {
  if (selectedProjectId.value) {
    await requirementStore.fetchRequirements({ 
      project_id: selectedProjectId.value,
      page_size: 100 
    })
  }
}

const loadVersions = async () => {
  if (selectedProjectId.value) {
    await versionStore.fetchVersions({ project_id: selectedProjectId.value })
  }
}

const handleProjectChange = () => {
  selectedVersionId.value = null
  selectedRequirementIds.value = []
  loadRequirements()
  loadVersions()
}

const handleSelectAll = () => {
  if (selectedRequirementIds.value.length === requirements.value.length) {
    selectedRequirementIds.value = []
  } else {
    selectedRequirementIds.value = requirements.value.map(r => r.id)
  }
}

const startGeneration = async () => {
  if (!selectedProjectId.value) {
    ElMessage.warning('请选择项目')
    return
  }
  
  if (selectedRequirementIds.value.length === 0) {
    ElMessage.warning('请选择至少一个功能点')
    return
  }
  
  isGenerating.value = true
  generationComplete.value = false
  savedTestcaseIds.value = []
  
  taskId.value = `task-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  
  try {
    const result = await testcaseApi.generate({
      project_id: selectedProjectId.value,
      requirement_ids: selectedRequirementIds.value,
      version_id: selectedVersionId.value || undefined,
    })
    taskId.value = result.task_id
    
    // 启动轮询查询任务状态
    startPolling(result.task_id)
    
  } catch (error: any) {
    ElMessage.error(error.message || '启动生成失败')
    isGenerating.value = false
  }
}

// 轮询查询任务状态
const startPolling = (currentTaskId: string) => {
  stopPolling()
  pollInterval.value = window.setInterval(async () => {
    try {
      const result = await aiTasksApi.getTestcaseTask(currentTaskId)
      
      if (result.status === 'completed') {
        stopPolling()
        handleGenerationComplete({ saved_ids: result.saved_ids })
      } else if (result.status === 'failed') {
        stopPolling()
        handleGenerationError(result.error_message || '测试用例生成失败')
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

const handleGenerationComplete = (data: any) => {
  isGenerating.value = false
  generationComplete.value = true
  
  if (data?.saved_ids) {
    savedTestcaseIds.value = data.saved_ids
    ElMessage.success(`测试用例生成完成！创建了 ${data.saved_ids.length} 个用例`)
  }
}

const handleGenerationError = (message: string) => {
  isGenerating.value = false
  ElMessage.error(`生成失败: ${message}`)
}

const resetForm = () => {
  selectedRequirementIds.value = []
  generationComplete.value = false
  savedTestcaseIds.value = []
  stopPolling()
}

const getPriorityColor = (priority: string) => {
  const colors: Record<string, string> = {
    '高': 'bg-red-100 text-red-700',
    '中': 'bg-yellow-100 text-yellow-700',
    '低': 'bg-green-100 text-green-700',
  }
  return colors[priority] || 'bg-gray-100 text-gray-700'
}

// ==================== Tab2 方法 ====================
async function fetchTestcaseList() {
  await testcaseStore.fetchTestcases({
    page: currentPage.value,
    page_size: pageSize.value,
    project_id: listSelectedProject.value,
    priority: listSelectedPriority.value,
    status: listSelectedStatus.value,
    keyword: searchKeyword.value || undefined,
  })
}

function handleSearch() {
  currentPage.value = 1
  fetchTestcaseList()
}

function handleFilterChange() {
  currentPage.value = 1
  fetchTestcaseList()
}

function handlePageChange(page: number) {
  currentPage.value = page
  fetchTestcaseList()
}

async function viewDetail(id: number) {
  const testcase = await testcaseApi.get(id)
  detailTestcase.value = testcase
  showDetail.value = true
}

async function deleteTestcase(id: number) {
  if (confirm('确定要删除这个测试用例吗？')) {
    await testcaseStore.deleteTestcase(id)
    fetchTestcaseList()
  }
}

async function handleExport() {
  if (!listSelectedProject.value) {
    ElMessage.warning('请先选择项目')
    return
  }
  
  exporting.value = true
  try {
    const result = await testcaseApi.export(listSelectedProject.value, exportFormat.value)
    
    if (exportFormat.value === 'markdown') {
      const blob = new Blob([result.content!], { type: 'text/markdown' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `testcases_${listSelectedProject.value}.md`
      a.click()
      URL.revokeObjectURL(url)
    } else {
      const blob = new Blob([result.content!], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `testcases_${listSelectedProject.value}.xlsx`
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

function getProjectName(projectId: number): string {
  const project = projectStore.projects.find(p => p.id === projectId)
  return project?.name || '-'
}
</script>

<template>
  <div class="testcase-generate-page min-h-full flex flex-col">
    <!-- 页面标题 -->
    <div class="mb-6 flex-shrink-0">
      <h1 class="text-2xl font-semibold text-text-primary">AI用例生成</h1>
      <p class="text-text-secondary text-sm mt-1">
        选择功能点自动生成测试用例，管理项目用例
      </p>
    </div>

    <!-- Tab 切换 -->
    <div class="card mb-6 flex-shrink-0 w-full">
      <div class="flex gap-6 border-b border-gray-200">
        <button
          @click="activeTab = 'generate'"
          :class="[
            'pb-3 border-b-2 transition-colors',
            activeTab === 'generate'
              ? 'border-primary text-primary font-medium'
              : 'border-transparent text-text-secondary hover:text-text-primary'
          ]"
        >
          <div class="flex items-center gap-2">
            <TestTube class="w-4 h-4" />
            用例生成
          </div>
        </button>
        <button
          @click="activeTab = 'list'"
          :class="[
            'pb-3 border-b-2 transition-colors',
            activeTab === 'list'
              ? 'border-primary text-primary font-medium'
              : 'border-transparent text-text-secondary hover:text-text-primary'
          ]"
        >
          <div class="flex items-center gap-2">
            <ListChecks class="w-4 h-4" />
            用例管理
          </div>
        </button>
      </div>
    </div>

    <!-- ==================== Tab1: 用例生成 ==================== -->
    <div v-if="activeTab === 'generate'" class="flex flex-col h-full">
      <!-- 左侧：功能点选择 -->
      <div class="space-y-4 flex-shrink-0">
          <!-- 项目和版本选择 -->
          <div class="card w-full">
            <h3 class="text-lg font-medium text-text-primary mb-4">项目信息</h3>
            
            <div class="space-y-4">
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

          <!-- 功能点选择 -->
          <div class="card w-full">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-lg font-medium text-text-primary">选择功能点</h3>
              <button 
                @click="handleSelectAll"
                class="text-sm text-primary hover:text-primary-light"
              >
                {{ selectedRequirementIds.length === requirements.length ? '取消全选' : '全选' }}
              </button>
            </div>
            
            <div v-if="!selectedProjectId" class="text-center py-8 text-text-placeholder">
              请先选择项目
            </div>
            
            <div v-else-if="requirementStore.loading" class="text-center py-8 text-text-secondary">
              加载中...
            </div>
            
            <div v-else-if="requirements.length === 0" class="text-center py-8 text-text-placeholder">
              该项目暂无功能点，请先进行需求分析
            </div>
            
            <div v-else class="space-y-2 max-h-96 overflow-y-auto">
              <label
                v-for="req in requirements"
                :key="req.id"
                class="flex items-start gap-3 p-3 rounded-lg border border-gray-100 hover:border-primary cursor-pointer transition-colors"
                :class="{ 'border-primary bg-blue-50': selectedRequirementIds.includes(req.id) }"
              >
                <input
                  type="checkbox"
                  :value="req.id"
                  v-model="selectedRequirementIds"
                  class="mt-1"
                />
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2">
                    <span class="font-medium text-text-primary">{{ req.name }}</span>
                    <span :class="['px-1.5 py-0.5 rounded text-xs', getPriorityColor(req.priority)]">
                      {{ req.priority }}
                    </span>
                  </div>
                  <p class="text-sm text-text-secondary mt-1 line-clamp-1">
                    {{ req.description || '暂无描述' }}
                  </p>
                </div>
              </label>
            </div>
            
            <div v-if="requirements.length > 0" class="mt-4 pt-4 border-t border-gray-100 text-sm text-text-secondary">
              已选择 {{ selectedRequirementIds.length }} / {{ requirements.length }} 个功能点
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="flex gap-3">
            <button 
              @click="startGeneration"
              :disabled="isGenerating || selectedRequirementIds.length === 0"
              class="btn-primary flex items-center gap-2 flex-1"
            >
              <Loader v-if="isGenerating" class="w-4 h-4 animate-spin" />
              <Send v-else class="w-4 h-4" />
              {{ isGenerating ? '生成中...' : '开始生成' }}
            </button>
            
            <button 
              v-if="generationComplete"
              @click="activeTab = 'list'"
              class="btn-secondary flex items-center gap-2"
            >
              <ListChecks class="w-4 h-4" />
              查看用例
            </button>
            
            <button 
              v-if="generationComplete"
              @click="resetForm"
              class="btn-secondary"
            >
              重新生成
            </button>
          </div>
        </div>

        <!-- 生成结果提示 -->
        <div v-if="generationComplete && savedTestcaseIds.length > 0" class="card mt-4 bg-green-50 border-green-200 flex-shrink-0 w-full">
          <div class="flex items-start gap-3">
            <CheckCircle class="w-5 h-5 text-green-500 mt-0.5" />
            <div>
              <h4 class="text-green-700 font-medium">生成完成</h4>
              <p class="text-green-600 text-sm mt-1">
                成功生成了 {{ savedTestcaseIds.length }} 个测试用例
              </p>
              <p class="text-green-500 text-xs mt-2">
                点击「查看用例」切换到用例管理Tab查看详情
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ==================== Tab2: 用例管理 ==================== -->
    <div v-if="activeTab === 'list'">
      <!-- 筛选区域 -->
      <div class="card mb-4 w-full">
        <div class="flex flex-wrap items-center gap-4">
          <div class="flex items-center gap-2">
            <label class="text-sm text-text-secondary whitespace-nowrap">项目：</label>
            <select v-model="listSelectedProject" @change="handleFilterChange" class="input-field w-48">
              <option :value="undefined">全部项目</option>
              <option v-for="project in projects" :key="project.id" :value="project.id">
                {{ project.name }}
              </option>
            </select>
          </div>
          
          <div class="flex items-center gap-2">
            <label class="text-sm text-text-secondary whitespace-nowrap">优先级：</label>
            <select v-model="listSelectedPriority" @change="handleFilterChange" class="input-field w-24">
              <option :value="undefined">全部</option>
              <option v-for="p in priorities" :key="p" :value="p">{{ p }}</option>
            </select>
          </div>
          
          <div class="flex items-center gap-2">
            <label class="text-sm text-text-secondary whitespace-nowrap">状态：</label>
            <select v-model="listSelectedStatus" @change="handleFilterChange" class="input-field w-28">
              <option :value="undefined">全部</option>
              <option v-for="s in statuses" :key="s" :value="s">{{ s }}</option>
            </select>
          </div>
          
          <div class="flex-1 min-w-[200px]">
            <div class="relative">
              <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-placeholder" />
              <input 
                v-model="searchKeyword"
                type="text"
                placeholder="搜索用例..."
                class="input-field pl-10 w-full"
                @keyup.enter="handleSearch"
              />
            </div>
          </div>
          
          <button @click="handleSearch" class="btn-primary">搜索</button>
          
          <button 
            @click="showExportDialog = true"
            :disabled="!listSelectedProject"
            class="btn-secondary flex items-center gap-2"
          >
            <Download class="w-4 h-4" />
            导出
          </button>
        </div>
      </div>

      <!-- 用例列表 -->
      <div class="card w-full">
        <div v-if="testcaseStore.loading" class="text-center py-10">
          加载中...
        </div>
        <div v-else-if="testcaseStore.testcases.length === 0" class="text-center py-10 text-text-secondary">
          暂无用例数据
        </div>
        <div v-else>
          <table class="w-full">
            <thead>
              <tr class="border-b border-gray-200">
                <th class="text-left py-3 px-4 text-sm font-medium text-text-secondary">用例名称</th>
                <th class="text-left py-3 px-4 text-sm font-medium text-text-secondary">项目</th>
                <th class="text-left py-3 px-4 text-sm font-medium text-text-secondary">优先级</th>
                <th class="text-left py-3 px-4 text-sm font-medium text-text-secondary">状态</th>
                <th class="text-right py-3 px-4 text-sm font-medium text-text-secondary">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr 
                v-for="tc in testcaseStore.testcases" 
                :key="tc.id"
                class="border-b border-gray-100 hover:bg-gray-50 transition-colors"
              >
                <td class="py-3 px-4">
                  <span class="text-primary cursor-pointer hover:underline" @click="viewDetail(tc.id)">
                    {{ tc.name }}
                  </span>
                </td>
                <td class="py-3 px-4 text-sm text-text-secondary">
                  {{ getProjectName(tc.project_id) }}
                </td>
                <td class="py-3 px-4">
                  <span :class="['px-2 py-0.5 rounded text-xs', getPriorityColor(tc.priority)]">
                    {{ tc.priority }}
                  </span>
                </td>
                <td class="py-3 px-4">
                  <span class="px-2 py-0.5 bg-gray-100 text-gray-700 rounded text-xs">
                    {{ tc.status || '未开始' }}
                  </span>
                </td>
                <td class="py-3 px-4">
                  <div class="flex items-center justify-end gap-2">
                    <button 
                      class="p-1.5 text-text-secondary hover:text-primary hover:bg-primary/10 rounded transition-colors"
                      @click="viewDetail(tc.id)"
                      title="查看详情"
                    >
                      <Eye class="w-4 h-4" />
                    </button>
                    <button 
                      class="p-1.5 text-text-secondary hover:text-red-500 hover:bg-red-50 rounded transition-colors"
                      @click="deleteTestcase(tc.id)"
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
            <div class="flex items-center gap-2">
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

      <!-- 详情弹窗 -->
      <div v-if="showDetail" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="showDetail = false">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] overflow-auto">
          <div class="p-6 border-b border-gray-200 flex items-center justify-between">
            <h2 class="text-lg font-semibold">{{ detailTestcase?.name }}</h2>
            <button @click="showDetail = false" class="text-gray-400 hover:text-gray-600">&times;</button>
          </div>
          <div class="p-6 space-y-4">
            <div>
              <label class="text-sm font-medium text-text-secondary">前置条件</label>
              <p class="mt-1 text-text-primary">{{ detailTestcase?.preconditions || '无' }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-text-secondary">测试步骤</label>
              <div class="mt-1 space-y-2">
                <div v-for="(step, index) in detailTestcase?.steps" :key="index" class="flex gap-2">
                  <span class="font-medium text-text-secondary">{{ index + 1 }}.</span>
                  <span class="text-text-primary">{{ step.description }}</span>
                </div>
              </div>
            </div>
            <div>
              <label class="text-sm font-medium text-text-secondary">预期结果</label>
              <p class="mt-1 text-text-primary">{{ detailTestcase?.expected_result || '无' }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 导出弹窗 -->
      <div v-if="showExportDialog" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="showExportDialog = false">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
          <h2 class="text-lg font-semibold mb-4">导出测试用例</h2>
          <div class="space-y-4">
            <div class="flex items-center gap-4">
              <label class="flex items-center gap-2 cursor-pointer">
                <input type="radio" value="excel" v-model="exportFormat" />
                <FileSpreadsheet class="w-5 h-5 text-green-600" />
                <span>Excel格式</span>
              </label>
              <label class="flex items-center gap-2 cursor-pointer">
                <input type="radio" value="markdown" v-model="exportFormat" />
                <FileText class="w-5 h-5 text-blue-600" />
                <span>Markdown格式</span>
              </label>
            </div>
          </div>
          <div class="mt-6 flex justify-end gap-3">
            <button @click="showExportDialog = false" class="btn-secondary">取消</button>
            <button @click="handleExport" :disabled="exporting" class="btn-primary">
              {{ exporting ? '导出中...' : '导出' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.testcase-generate-page {
  width: 100%;
  height: 100%;
}

.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
