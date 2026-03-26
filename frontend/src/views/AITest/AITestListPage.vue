<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { 
  History, Search, RefreshCw, CheckCircle, XCircle, Loader2, 
  Clock, Eye, Trash2, Filter, X, ArrowRight, FileText, TestTube,
  Sparkles, Square, Play, Wifi, WifiOff
} from 'lucide-vue-next'
import { ElMessage, ElMessageBox } from 'element-plus'
import aiTestApi from '@/api/aiTest'
import useProjectStore from '@/stores/project'
import { formatDateTime } from '@/utils/date'

const router = useRouter()
const projectStore = useProjectStore()

// 任务状态
type TaskStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'

// 阶段摘要
interface PhaseSummary {
  code: string
  name: string
  status: string
  progress: number
}

// 任务记录接口
interface TaskRecord {
  id: number
  task_id: string
  project_id: number | null
  project_name: string
  task_name: string | null
  status: TaskStatus
  progress: number
  
  // 需求分析阶段
  requirement_phase_status: string
  requirement_phase_progress: number
  total_requirements: number
  saved_requirements: number
  
  // 用例生成阶段
  testcase_phase_status: string
  testcase_phase_progress: number
  total_testcases: number
  saved_testcases: number
  
  current_phase: string | null
  phases_summary: PhaseSummary[]
  error_message: string | null
  created_at: string
  started_at: string | null
  completed_at: string | null
}

// 统计数据
interface Stats {
  total: number
  running: number
  pending: number
  completed: number
  failed: number
}

// 状态
const tasks = ref<TaskRecord[]>([])
const stats = ref<Stats>({ total: 0, running: 0, pending: 0, completed: 0, failed: 0 })
const loading = ref(false)
const deletingId = ref<string | null>(null)
const cancellingId = ref<string | null>(null)

// 搜索和筛选
const searchKeyword = ref('')
const filterStatus = ref<TaskStatus | 'all'>('all')
const showFilters = ref(false)

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 自动刷新
const autoRefresh = ref(false)
const refreshInterval = ref(10)
const refreshTimer = ref<ReturnType<typeof setInterval> | null>(null)

// 状态配置
const statusConfig = {
  completed: { 
    class: 'bg-green-100 text-green-700 border-green-200', 
    icon: CheckCircle, 
    text: '已完成',
    bgIcon: 'bg-green-500'
  },
  failed: { 
    class: 'bg-red-100 text-red-700 border-red-200', 
    icon: XCircle, 
    text: '失败',
    bgIcon: 'bg-red-500'
  },
  running: { 
    class: 'bg-blue-100 text-blue-700 border-blue-200', 
    icon: Loader2, 
    text: '进行中',
    bgIcon: 'bg-blue-500'
  },
  pending: { 
    class: 'bg-yellow-100 text-yellow-700 border-yellow-200', 
    icon: Clock, 
    text: '排队中',
    bgIcon: 'bg-yellow-500'
  },
  cancelled: { 
    class: 'bg-gray-100 text-gray-600 border-gray-200', 
    icon: XCircle, 
    text: '已取消',
    bgIcon: 'bg-gray-500'
  }
}

// 计算属性
const filteredTasks = computed(() => {
  let result = tasks.value
  
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(t => 
      t.project_name?.toLowerCase().includes(keyword) ||
      t.task_name?.toLowerCase().includes(keyword) ||
      t.task_id.toLowerCase().includes(keyword)
    )
  }
  
  if (filterStatus.value !== 'all') {
    result = result.filter(t => t.status === filterStatus.value)
  }
  
  return result
})

const paginatedTasks = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredTasks.value.slice(start, end)
})

const totalPages = computed(() => Math.ceil(filteredTasks.value.length / pageSize.value))

// 格式化时间
const formatTime = (dateStr: string | undefined) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  if (diff < 60 * 1000) return '刚刚'
  if (diff < 60 * 60 * 1000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 24 * 60 * 60 * 1000) return `${Math.floor(diff / 3600000)}小时前`
  
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

// 加载统计数据
const loadStats = async () => {
  try {
    const res = await aiTestApi.getStats()
    stats.value = res.data || res
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

// 加载任务列表
const loadTasks = async () => {
  loading.value = true
  try {
    const res = await aiTestApi.listTasks({ page_size: 100 })
    const data = res.data || res
    tasks.value = (data.items || []).map((task: any) => ({
      ...task,
      progress: Number(task.progress) || 0
    }))
    total.value = data.total || 0
  } catch (error) {
    console.error('加载任务列表失败:', error)
    ElMessage.error('加载任务列表失败')
  } finally {
    loading.value = false
  }
}

// 刷新
const handleRefresh = async () => {
  await Promise.all([loadTasks(), loadStats()])
}

// 搜索
const handleSearch = () => {
  currentPage.value = 1
}

// 重置
const handleReset = () => {
  searchKeyword.value = ''
  filterStatus.value = 'all'
  currentPage.value = 1
}

// 查看详情
const viewDetail = (task: TaskRecord) => {
  router.push(`/ai-cases/task-records/${task.task_id}`)
}

// 删除任务
const handleDelete = async (task: TaskRecord, e: Event) => {
  e.stopPropagation()
  
  const isForce = task.status === 'running'
  const message = isForce 
    ? '此任务正在运行，强制删除可能会导致后台进程继续运行。确定要删除吗？'
    : '确定删除此任务记录吗？删除后将无法恢复。'
  
  try {
    await ElMessageBox.confirm(message, '确认删除', {
      confirmButtonText: isForce ? '强制删除' : '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })

    deletingId.value = task.task_id
    await aiTestApi.deleteTask(task.task_id, isForce)
    
    tasks.value = tasks.value.filter(t => t.task_id !== task.task_id)
    await loadStats()
    ElMessage.success('删除成功')
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  } finally {
    deletingId.value = null
  }
}

// 取消任务
const handleCancel = async (task: TaskRecord, e: Event) => {
  e.stopPropagation()
  
  try {
    await ElMessageBox.confirm(
      '确定取消此任务吗？取消后任务将停止执行。',
      '确认取消',
      { confirmButtonText: '取消任务', cancelButtonText: '不取消', type: 'warning' }
    )

    cancellingId.value = task.task_id
    await aiTestApi.cancelTask(task.task_id)
    
    // 更新任务状态
    const idx = tasks.value.findIndex(t => t.task_id === task.task_id)
    if (idx !== -1) {
      tasks.value[idx] = { ...tasks.value[idx], status: 'cancelled' as const }
    }
    await loadStats()
    ElMessage.success('任务已取消')
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error('取消失败')
    }
  } finally {
    cancellingId.value = null
  }
}

// 自动刷新
const toggleAutoRefresh = () => {
  autoRefresh.value = !autoRefresh.value
  if (autoRefresh.value) {
    startAutoRefresh()
    ElMessage.success(`已开启自动刷新 (${refreshInterval.value}秒)`)
  } else {
    stopAutoRefresh()
  }
}

const startAutoRefresh = () => {
  stopAutoRefresh()
  refreshTimer.value = setInterval(() => {
    handleRefresh()
  }, refreshInterval.value * 1000)
}

const stopAutoRefresh = () => {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value)
    refreshTimer.value = null
  }
}

// 获取阶段状态图标
const getPhaseIcon = (phase: PhaseSummary) => {
  if (phase.status === 'completed') return CheckCircle
  if (phase.status === 'running') return Loader2
  if (phase.status === 'failed') return XCircle
  return Clock
}

const getPhaseStatusColor = (phase: PhaseSummary) => {
  if (phase.status === 'completed') return 'text-green-500'
  if (phase.status === 'running') return 'text-blue-500 animate-spin'
  if (phase.status === 'failed') return 'text-red-500'
  return 'text-gray-300'
}

// 获取阶段进度文本
const getPhaseProgressText = (task: TaskRecord, phase: 'requirement' | 'testcase') => {
  if (phase === 'requirement') {
    const status = task.requirement_phase_status
    if (status === 'completed') return `${task.saved_requirements}个`
    if (status === 'running') return `${task.requirement_phase_progress}%`
    return '-'
  } else {
    const status = task.testcase_phase_status
    if (status === 'completed') return `${task.saved_testcases}个`
    if (status === 'running') return `${task.testcase_phase_progress}%`
    return '-'
  }
}

// 生命周期
onMounted(async () => {
  await projectStore.fetchProjects({ page_size: 100 })
  await handleRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})

// 监听筛选变化，重置页码
watch([filterStatus], () => {
  currentPage.value = 1
})
</script>

<template>
  <div class="task-list-page p-6 max-w-7xl mx-auto">
    <!-- 页面标题 -->
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center gap-3">
        <div class="p-2 bg-primary/10 rounded-xl">
          <Sparkles class="w-6 h-6 text-primary" />
        </div>
        <div>
          <h1 class="text-2xl font-bold text-gray-900">任务记录</h1>
          <p class="text-sm text-gray-500 mt-0.5">统一的需求分析 + 用例生成任务</p>
        </div>
      </div>
      
      <!-- 操作按钮 -->
      <div class="flex items-center gap-3">
        <button
          @click="handleRefresh"
          :disabled="loading"
          class="btn-secondary flex items-center gap-2"
        >
          <RefreshCw :class="['w-4 h-4', loading && 'animate-spin']" />
          刷新
        </button>
        
        <button
          @click="toggleAutoRefresh"
          :class="[
            'flex items-center gap-2 px-4 py-2 rounded-lg border font-medium transition-all',
            autoRefresh 
              ? 'bg-primary text-white border-primary' 
              : 'border-gray-300 text-gray-600 hover:bg-gray-50'
          ]"
        >
          <Loader2 v-if="autoRefresh" :class="['w-4 h-4 animate-spin']" />
          {{ autoRefresh ? `${refreshInterval}s` : '自动刷新' }}
        </button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-4 gap-4 mb-6">
      <div class="bg-white rounded-xl border border-gray-200 p-4 flex items-center gap-4">
        <div class="p-3 bg-blue-100 rounded-xl">
          <Play class="w-6 h-6 text-blue-600" />
        </div>
        <div>
          <p class="text-sm text-gray-500">进行中</p>
          <p class="text-2xl font-bold text-gray-900">{{ stats.running }}</p>
        </div>
      </div>
      
      <div class="bg-white rounded-xl border border-gray-200 p-4 flex items-center gap-4">
        <div class="p-3 bg-green-100 rounded-xl">
          <CheckCircle class="w-6 h-6 text-green-600" />
        </div>
        <div>
          <p class="text-sm text-gray-500">已完成</p>
          <p class="text-2xl font-bold text-gray-900">{{ stats.completed }}</p>
        </div>
      </div>
      
      <div class="bg-white rounded-xl border border-gray-200 p-4 flex items-center gap-4">
        <div class="p-3 bg-red-100 rounded-xl">
          <XCircle class="w-6 h-6 text-red-600" />
        </div>
        <div>
          <p class="text-sm text-gray-500">失败</p>
          <p class="text-2xl font-bold text-gray-900">{{ stats.failed }}</p>
        </div>
      </div>

      <div class="bg-white rounded-xl border border-gray-200 p-4 flex items-center gap-4">
        <div class="p-3 bg-purple-100 rounded-xl">
          <FileText class="w-6 h-6 text-purple-600" />
        </div>
        <div>
          <p class="text-sm text-gray-500">总任务</p>
          <p class="text-2xl font-bold text-gray-900">{{ stats.total }}</p>
        </div>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <div class="bg-white rounded-xl border border-gray-200 p-4 mb-6">
      <div class="flex items-center gap-4">
        <!-- 搜索框 -->
        <div class="flex-1 relative">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            v-model="searchKeyword"
            type="text"
            placeholder="搜索任务名称、项目..."
            class="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
            @keyup.enter="handleSearch"
          />
        </div>
        
        <!-- 状态筛选 -->
        <div class="flex items-center gap-2">
          <span class="text-sm text-gray-500">状态:</span>
          <div class="flex gap-1">
            <button
              v-for="status in ['all', 'running', 'completed', 'failed']"
              :key="status"
              @click="filterStatus = status as any"
              :class="[
                'px-3 py-1.5 rounded-lg text-sm font-medium transition-all',
                filterStatus === status
                  ? 'bg-primary text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              ]"
            >
              {{ status === 'all' ? '全部' : statusConfig[status as TaskStatus]?.text }}
            </button>
          </div>
        </div>
        
        <button v-if="filterStatus !== 'all' || searchKeyword" @click="handleReset" class="text-sm text-gray-500 hover:text-gray-700">
          重置
        </button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading && tasks.length === 0" class="bg-white rounded-xl border border-gray-200 p-16 text-center">
      <Loader2 class="w-8 h-8 animate-spin mx-auto text-primary mb-3" />
      <p class="text-gray-500">加载中...</p>
    </div>

    <!-- 空状态 -->
    <div v-else-if="filteredTasks.length === 0" class="bg-white rounded-xl border border-gray-200 p-16 text-center">
      <History class="w-12 h-12 mx-auto text-gray-300 mb-3" />
      <p class="text-gray-500 mb-1">暂无任务记录</p>
      <p class="text-sm text-gray-400">开始一个新任务吧</p>
    </div>

    <!-- 任务列表 -->
    <div v-else class="space-y-3">
      <div 
        v-for="task in paginatedTasks" 
        :key="task.id"
        @click="viewDetail(task)"
        class="bg-white rounded-xl border border-gray-200 p-5 hover:border-primary/30 hover:shadow-md transition-all cursor-pointer group"
      >
        <!-- 第一行：状态图标 + 任务信息 + 操作按钮 -->
        <div class="flex items-center gap-4">
          <!-- 状态指示器 -->
          <div class="shrink-0">
            <div :class="['w-12 h-12 rounded-xl flex items-center justify-center', statusConfig[task.status].class]">
              <component 
                :is="statusConfig[task.status].icon" 
                :class="['w-6 h-6', task.status === 'running' && 'animate-spin']" 
              />
            </div>
          </div>
          
          <!-- 任务信息 -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-3 flex-wrap">
              <!-- 任务类型标签 -->
              <span class="px-2.5 py-1 rounded-lg text-xs font-medium bg-gradient-to-r from-purple-100 to-indigo-100 text-purple-700">
                AI测试
              </span>
              
              <!-- 任务名称 -->
              <span class="font-semibold text-gray-900 truncate">{{ task.task_name || '未命名任务' }}</span>
              
              <!-- 项目 -->
              <span v-if="task.project_name" class="text-gray-500 truncate">
                {{ task.project_name }}
              </span>
            </div>
            
            <!-- 底部信息 -->
            <div class="flex items-center gap-4 text-sm text-gray-400 mt-1">
              <span>{{ formatDateTime(task.created_at) }}</span>
              <span v-if="task.status === 'failed' && task.error_message" class="text-red-500 truncate max-w-xs">
                {{ task.error_message }}
              </span>
            </div>
          </div>
          
          <!-- 非进行中状态 -->
          <div v-if="task.status !== 'running' && task.status !== 'completed'" 
               :class="['shrink-0 text-sm font-medium px-3 py-1.5 rounded-lg', statusConfig[task.status].class]">
            {{ statusConfig[task.status].text }}
          </div>
          
          <!-- 操作按钮（始终显示，不再 hover 显示） -->
          <div class="flex items-center gap-1 shrink-0">
            <button
              @click="viewDetail(task)"
              class="p-2 text-gray-400 hover:text-primary hover:bg-primary/10 rounded-lg transition-colors"
              title="查看详情"
            >
              <Eye class="w-5 h-5" />
            </button>
            <!-- 取消按钮 -->
            <button
              v-if="task.status === 'running' || task.status === 'pending'"
              @click="(e) => handleCancel(task, e)"
              :disabled="cancellingId === task.task_id"
              class="p-2 text-gray-400 hover:text-orange-600 hover:bg-orange-50 rounded-lg transition-colors"
              title="取消任务"
            >
              <Square :class="['w-5 h-5', cancellingId === task.task_id && 'animate-pulse']" />
            </button>
            <!-- 删除按钮 -->
            <button
              @click="(e) => handleDelete(task, e)"
              :disabled="deletingId === task.task_id"
              class="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
              :title="task.status === 'running' ? '强制删除' : '删除'"
            >
              <Trash2 :class="['w-5 h-5', deletingId === task.task_id && 'animate-pulse']" />
            </button>
          </div>
        </div>
        
        <!-- 进度条（仅 running/completed 显示） -->
        <div v-if="task.status === 'running' || task.status === 'completed'" class="mt-4 pt-4 border-t border-gray-100">
          <div class="flex items-center gap-3">
            <!-- 百分比进度条 -->
            <div class="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
              <div 
                :class="[
                  'h-full rounded-full transition-all duration-500',
                  task.status === 'completed' ? 'bg-green-500' : 'bg-gradient-to-r from-primary to-purple-500'
                ]"
                :style="{ width: `${task.progress}%` }"
              ></div>
            </div>
            
            <!-- 进度信息 -->
            <div class="shrink-0">
              <span :class="['text-sm font-medium', task.status === 'completed' ? 'text-green-500' : 'text-blue-500']">
                {{ task.progress }}%
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div v-if="totalPages > 1" class="mt-6 flex items-center justify-between">
      <p class="text-sm text-gray-500">
        显示 {{ (currentPage - 1) * pageSize + 1 }}-{{ Math.min(currentPage * pageSize, filteredTasks.length) }} 条，共 {{ filteredTasks.length }} 条
      </p>
      
      <div class="flex items-center gap-2">
        <button
          @click="currentPage--"
          :disabled="currentPage === 1"
          class="px-3 py-1.5 border border-gray-200 rounded-lg text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 transition-colors"
        >
          上一页
        </button>
        
        <span class="px-3 py-1.5 text-sm text-gray-600">
          {{ currentPage }} / {{ totalPages }}
        </span>
        
        <button
          @click="currentPage++"
          :disabled="currentPage >= totalPages"
          class="px-3 py-1.5 border border-gray-200 rounded-lg text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 transition-colors"
        >
          下一页
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.task-list-page {
  min-height: calc(100vh - 100px);
}
</style>
