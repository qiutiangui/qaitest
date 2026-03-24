<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowLeft, RefreshCw, CheckCircle, XCircle, Loader2, Clock,
  Play, Trash2, Copy, Check, Download, Maximize2,
  FileText, TestTube, AlertCircle, Info, Terminal, Zap,
  ChevronRight, Circle, Wifi, WifiOff, Square, LayoutGrid
} from 'lucide-vue-next'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'
import { connectWebSocket, disconnectWebSocket } from '@/api/websocket'
import RequirementList from '@/components/ai-tasks/RequirementList.vue'
import TestCaseList from '@/components/ai-tasks/TestCaseList.vue'

const route = useRoute()
const router = useRouter()

// 任务类型
type TaskType = 'requirement' | 'testcase'
type TaskStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
type LogType = 'info' | 'thinking' | 'stream' | 'response' | 'error' | 'complete' | 'warning'

// 阶段接口
interface Phase {
  code: string
  name: string
  status: string
  progress: number
  started_at?: string
  completed_at?: string
  logs?: any[]
}

// 日志条目接口
interface LogEntry {
  id: string
  agent_name: string
  content: string
  type: LogType
  timestamp: string
  extra_data?: any
}

// 任务详情接口
interface TaskDetail {
  id: number
  task_id: string
  task_type: TaskType
  task_type_name: string
  project_id: number | null
  requirement_name?: string
  function_ids?: number[]
  function_names?: string[]
  version_id: number | null
  status: TaskStatus
  progress: number
  current_phase?: string
  current_phase_code?: string
  phases: Phase[]
  total_requirements?: number
  total_functions?: number
  total_testcases?: number
  saved_count: number
  saved_ids?: number[]
  result?: any
  error_message?: string
  error_details?: any
  logs: any[]
  duration?: number
  created_at: string
  started_at?: string
  completed_at?: string
  // 新增：关联数据
  requirements?: Requirement[]
  testcases?: TestCase[]
  stats?: {
    duration_seconds?: number
  }
}

// 功能点接口
interface Requirement {
  id: number
  name: string
  category?: string
  module?: string
  priority?: string
  created_at?: string
}

// 测试用例接口
interface TestCase {
  id: number
  title: string
  priority?: string
  status?: string
  test_type?: string
  created_at?: string
}

// Agent 代码到中文名称的映射
const agentCodeMap: Record<string, string> = {
  'RequirementAcquireAgent': '需求获取',
  'RequirementAnalyzeAgent': '需求分析',
  'RequirementOutputAgent': '需求输出',
  'TestCaseGenerateAgent': '用例生成',
  'TestCaseReviewAgent': '用例评审',
  'DataSaveAgent': '数据保存',
  'ErrorAgent': '错误',
}

// Agent 配置
const agentConfig: Record<string, { color: string; bgColor: string; borderColor: string }> = {
  '系统': { color: 'text-gray-600', bgColor: 'bg-gray-50', borderColor: 'border-gray-300' },
  '需求获取': { color: 'text-purple-600', bgColor: 'bg-purple-50', borderColor: 'border-purple-300' },
  '需求分析': { color: 'text-blue-600', bgColor: 'bg-blue-50', borderColor: 'border-blue-300' },
  '需求输出': { color: 'text-green-600', bgColor: 'bg-green-50', borderColor: 'border-green-300' },
  '用例生成': { color: 'text-teal-600', bgColor: 'bg-teal-50', borderColor: 'border-teal-300' },
  '用例评审': { color: 'text-orange-600', bgColor: 'bg-orange-50', borderColor: 'border-orange-300' },
  '数据保存': { color: 'text-indigo-600', bgColor: 'bg-indigo-50', borderColor: 'border-indigo-300' },
  '错误': { color: 'text-red-600', bgColor: 'bg-red-50', borderColor: 'border-red-300' },
}

// 阶段配置
const phaseOrder = ['acquire', 'analyze', 'output', 'generate', 'review', 'save']

// 状态
const taskType = computed(() => route.params.type as TaskType)
const taskId = computed(() => route.params.taskId as string)

const taskDetail = ref<TaskDetail | null>(null)
const logs = ref<LogEntry[]>([])
const loading = ref(true)
const wsConnected = ref(false)
const wsConnecting = ref(false)
const autoScroll = ref(true)
const showFullscreen = ref(false)
const copiedId = ref<string | null>(null)
const deleting = ref(false)
const cancelling = ref(false)
const lastLogIndex = ref(0)
const activeTab = ref('overview')

// 计算属性
const statusConfig = {
  completed: { class: 'bg-green-100 text-green-700', icon: CheckCircle, text: '已完成' },
  failed: { class: 'bg-red-100 text-red-700', icon: XCircle, text: '失败' },
  running: { class: 'bg-blue-100 text-blue-700', icon: Loader2, text: '进行中' },
  pending: { class: 'bg-yellow-100 text-yellow-700', icon: Clock, text: '排队中' },
  cancelled: { class: 'bg-gray-100 text-gray-600', icon: XCircle, text: '已取消' }
}

const isTaskRunning = computed(() => taskDetail.value?.status === 'running' || taskDetail.value?.status === 'pending')
const isTaskFinished = computed(() => ['completed', 'failed', 'cancelled'].includes(taskDetail.value?.status || ''))

// Tab配置
const tabs = computed(() => {
  const baseTabs = [
    { key: 'overview', label: '概览', icon: LayoutGrid }
  ]

  // 需求分析任务：显示功能点
  if (taskType.value === 'requirement') {
    baseTabs.push({ key: 'requirements', label: '功能点', icon: FileText })
  }

  // 用例生成任务：显示测试用例
  if (taskType.value === 'testcase') {
    baseTabs.push({ key: 'testcases', label: '测试用例', icon: TestTube })
  }

  return baseTabs
})

// 当前Tab的badge数量
const getTabBadge = (key: string) => {
  if (key === 'requirements') return taskDetail.value?.requirements?.length || 0
  if (key === 'testcases') return taskDetail.value?.testcases?.length || 0
  return 0
}

// 加载任务详情
const loadTaskDetail = async () => {
  loading.value = true
  try {
    const res = await api.get(`/tasks/${taskType.value}/${taskId.value}`)
    const data = res.data || res
    
    // 确保 progress 是数字类型
    taskDetail.value = {
      ...data,
      progress: Number(data.progress) || 0
    }
    
    // 如果有历史日志，加载显示
    if (data.logs && data.logs.length > 0) {
      logs.value = data.logs.map((log: any, idx: number) => ({
        id: `hist-${idx}`,
        agent_name: getAgentDisplayName(log.agent_name || log.agent || '系统'),
        content: log.content,
        type: mapLogType(log.type || log.level || 'info'),
        timestamp: log.timestamp || log.created_at || new Date().toISOString(),
        extra_data: log.extra_data
      }))
      lastLogIndex.value = data.logs.length
    }
  } catch (error) {
    console.error('加载任务详情失败:', error)
    ElMessage.error('加载任务详情失败')
  } finally {
    loading.value = false
  }
}

// 映射日志类型
const mapLogType = (type: string): LogType => {
  const typeMap: Record<string, LogType> = {
    'info': 'info',
    'thinking': 'thinking',
    'stream': 'stream',
    'response': 'response',
    'error': 'error',
    'complete': 'complete',
    'warning': 'warning',
    'stream_start': 'info',
    'stream_end': 'info',
  }
  return typeMap[type] || 'info'
}

// 获取Agent样式
const getAgentClass = (agentName: string) => {
  const config = agentConfig[agentName]
  if (config) {
    return `${config.color} ${config.bgColor} ${config.borderColor}`
  }
  return 'text-gray-600 bg-gray-50 border-gray-300'
}

// 获取Agent显示名称（英文代码转中文）
const getAgentDisplayName = (agentCode: string) => {
  return agentCodeMap[agentCode] || agentCode || '系统'
}

// 获取阶段样式
const getPhaseClass = (phase: Phase) => {
  if (phase.status === 'completed') return 'bg-green-100 text-green-700 border-green-300'
  if (phase.status === 'running') return 'bg-blue-100 text-blue-700 border-blue-300'
  if (phase.status === 'failed') return 'bg-red-100 text-red-700 border-red-300'
  return 'bg-gray-100 text-gray-500 border-gray-200'
}

const getPhaseIcon = (phase: Phase) => {
  if (phase.status === 'completed') return CheckCircle
  if (phase.status === 'running') return Loader2
  if (phase.status === 'failed') return XCircle
  return Circle
}

// 格式化时间戳
const formatTimestamp = (timestamp: string) => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit', 
    second: '2-digit',
    hour12: false 
  })
}

// 格式化日期
const formatDate = (dateStr: string | undefined) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

// 格式化时长
const formatDuration = (seconds: number | undefined) => {
  if (!seconds) return '-'
  if (seconds < 60) return `${Math.round(seconds)}秒`
  const mins = Math.floor(seconds / 60)
  const secs = Math.round(seconds % 60)
  if (mins < 60) return `${mins}分${secs}秒`
  const hours = Math.floor(mins / 60)
  return `${hours}时${mins % 60}分`
}

// 复制日志内容
const copyLog = async (log: LogEntry) => {
  try {
    await navigator.clipboard.writeText(log.content)
    copiedId.value = log.id
    setTimeout(() => { copiedId.value = null }, 2000)
  } catch (e) {
    ElMessage.error('复制失败')
  }
}

// 下载日志
const downloadLogs = () => {
  const content = logs.value.map(log => 
    `[${log.timestamp}] [${log.agent_name}] ${log.content}`
  ).join('\n')
  
  const blob = new Blob([content], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `task-${taskId.value}-logs-${Date.now()}.txt`
  a.click()
  URL.revokeObjectURL(url)
}

// 连接WebSocket获取实时日志
const connectToWebSocket = () => {
  // 如果已经连接或正在连接中，不再重复连接
  if (wsConnected.value || wsConnecting.value) return
  
  wsConnecting.value = true
  
  connectWebSocket(taskId.value, {
    onOpen: () => {
      wsConnected.value = true
      wsConnecting.value = false
    },
    onMessage: (message: any) => {
      handleWebSocketMessage(message)
    },
    onError: (error: any) => {
      wsConnected.value = false
      wsConnecting.value = false
    },
    onClose: () => {
      wsConnected.value = false
      wsConnecting.value = false
    }
  })
}

// 处理WebSocket消息
const handleWebSocketMessage = (message: any) => {
  const { agent_name, content, type, extra_data } = message
  
  // 更新任务状态
  if (message.status) {
    taskDetail.value = {
      ...taskDetail.value!,
      status: message.status,
      progress: Number(message.progress) ?? taskDetail.value?.progress ?? 0,
      current_phase: message.current_phase ?? taskDetail.value?.current_phase
    }
  }
  
  // 更新进度
  if (message.progress !== undefined) {
    taskDetail.value!.progress = Number(message.progress)
  }
  
  // 获取 agent 显示名称（英文代码转中文）
  const displayAgent = getAgentDisplayName(agent_name)
  
  // 流式内容 - 合并到当前 agent 的日志
  if (type === 'stream') {
    const lastLog = logs.value[logs.value.length - 1]
    // 如果最后一个日志是同 agent 的流式日志，继续追加内容
    if (lastLog && lastLog.agent_name === displayAgent && lastLog.type === 'stream') {
      lastLog.content += content
      if (autoScroll.value) {
        nextTick(() => scrollToBottom())
      }
      return
    }
    // 否则创建新的流式日志
    logs.value.push({
      id: `ws-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      agent_name: displayAgent,
      content: content || '',
      type: 'stream',
      timestamp: new Date().toISOString(),
      extra_data
    })
    lastLogIndex.value++
    if (autoScroll.value) {
      nextTick(() => scrollToBottom())
    }
    return
  }
  
  // 流式结束或完成 - 标记最后一个流式日志为完成
  if (type === 'stream_end' || type === 'complete') {
    const lastLog = logs.value[logs.value.length - 1]
    if (lastLog && lastLog.agent_name === displayAgent && lastLog.type === 'stream') {
      // 将流式日志标记为完成
      lastLog.type = 'info'
    }
    return
  }
  
  // 非流式消息 - 添加新日志
  logs.value.push({
    id: `ws-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    agent_name: displayAgent,
    content: content || '',
    type: mapLogType(type || 'info'),
    timestamp: new Date().toISOString(),
    extra_data
  })
  lastLogIndex.value++
  
  // 自动滚动
  if (autoScroll.value) {
    nextTick(() => scrollToBottom())
  }
}

// 滚动到底部
const scrollToBottom = () => {
  const container = document.querySelector('.log-container')
  if (container) {
    container.scrollTop = container.scrollHeight
  }
}

// 滚动事件处理
const handleScroll = (e: Event) => {
  const target = e.target as HTMLElement
  const isAtBottom = target.scrollHeight - target.scrollTop <= target.clientHeight + 100
  autoScroll.value = isAtBottom
}

// 删除任务
const handleDelete = async () => {
  const isForce = taskDetail.value?.status === 'running'
  const message = isForce 
    ? '此任务正在运行，强制删除可能会导致后台进程继续运行。确定要删除吗？'
    : '确定删除此任务记录吗？删除后将无法恢复。'
  
  try {
    await ElMessageBox.confirm(message, '确认删除', {
      confirmButtonText: isForce ? '强制删除' : '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    deleting.value = true
    await api.delete(`/tasks/${taskType.value}/${taskId.value}?force=${isForce}`)
    ElMessage.success('删除成功')
    router.push('/tasks')
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  } finally {
    deleting.value = false
  }
}

// 取消任务
const handleCancel = async () => {
  try {
    await ElMessageBox.confirm(
      '确定取消此任务吗？取消后任务将停止执行。',
      '确认取消',
      { confirmButtonText: '取消任务', cancelButtonText: '不取消', type: 'warning' }
    )
    
    cancelling.value = true
    await api.post(`/tasks/${taskType.value}/${taskId.value}/cancel`)
    
    // 更新本地状态
    if (taskDetail.value) {
      taskDetail.value.status = 'cancelled'
    }
    disconnectWebSocket()
    
    ElMessage.success('任务已取消')
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error('取消失败')
    }
  } finally {
    cancelling.value = false
  }
}

// 返回列表
const goBack = () => {
  router.push('/tasks')
}

// 生命周期
onMounted(async () => {
  await loadTaskDetail()
  
  // 如果任务还在运行，连接WebSocket
  if (isTaskRunning.value) {
    connectToWebSocket()
  }
})

onUnmounted(() => {
  disconnectWebSocket()
})

// 监听任务状态变化
watch(() => taskDetail.value?.status, (newStatus) => {
  if ((newStatus === 'running' || newStatus === 'pending') && !wsConnected.value && !wsConnecting.value) {
    connectToWebSocket()
  } else if (isTaskFinished.value) {
    disconnectWebSocket()
  }
})
</script>

<template>
  <div :class="['task-detail-page', showFullscreen && 'fullscreen-mode']">
    <!-- 顶部导航 -->
    <div class="sticky top-0 bg-white border-b border-gray-200 z-10">
      <div class="flex items-center justify-between px-6 py-4">
        <div class="flex items-center gap-4">
          <button 
            @click="goBack"
            class="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft class="w-5 h-5 text-gray-600" />
          </button>
          
          <div>
            <div class="flex items-center gap-3">
              <h1 class="text-xl font-semibold text-gray-900">任务详情</h1>
              
              <!-- 任务类型标签 -->
              <span :class="[
                'px-2.5 py-1 rounded-lg text-xs font-medium',
                taskType === 'requirement' 
                  ? 'bg-purple-100 text-purple-700' 
                  : 'bg-teal-100 text-teal-700'
              ]">
                {{ taskType === 'requirement' ? '需求分析' : '用例生成' }}
              </span>
              
              <!-- 状态标签 -->
              <span v-if="taskDetail" :class="[
                'px-3 py-1 rounded-lg text-sm font-medium flex items-center gap-1.5',
                statusConfig[taskDetail.status].class
              ]">
                <component 
                  :is="statusConfig[taskDetail.status].icon" 
                  :class="['w-4 h-4', taskDetail.status === 'running' && 'animate-spin']" 
                />
                {{ statusConfig[taskDetail.status].text }}
              </span>
              
              <!-- WebSocket连接状态 -->
              <span v-if="isTaskRunning" :class="[
                'px-2 py-0.5 rounded text-xs flex items-center gap-1',
                wsConnected ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
              ]">
                <component :is="wsConnected ? Wifi : WifiOff" class="w-3 h-3" />
                {{ wsConnected ? '实时同步' : '重连中' }}
              </span>
            </div>
            
            <!-- 任务ID -->
            <p class="text-sm text-gray-500 mt-0.5">
              {{ taskId }}
            </p>
          </div>
        </div>
        
        <!-- 操作按钮 -->
        <div class="flex items-center gap-2">
          <!-- 取消按钮 -->
          <button 
            v-if="isTaskRunning && !cancelling"
            @click="handleCancel"
            class="px-4 py-2 text-orange-600 hover:bg-orange-50 rounded-lg transition-colors text-sm font-medium flex items-center gap-1.5"
          >
            <Square class="w-4 h-4" />
            取消任务
          </button>
          <!-- 删除按钮 -->
          <button 
            v-if="isTaskFinished && !deleting"
            @click="handleDelete"
            class="px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors text-sm font-medium flex items-center gap-1.5"
          >
            <Trash2 class="w-4 h-4" />
            删除
          </button>
          
          <button 
            v-if="logs.length > 0"
            @click="downloadLogs"
            class="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors text-sm font-medium flex items-center gap-1.5"
          >
            <Download class="w-4 h-4" />
            下载日志
          </button>
          
          <button 
            @click="showFullscreen = !showFullscreen"
            class="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            :title="showFullscreen ? '退出全屏' : '全屏'"
          >
            <Maximize2 :class="['w-5 h-5 text-gray-600', showFullscreen && 'rotate-180']" />
          </button>
        </div>
      </div>
    </div>

    <!-- Tab导航 -->
    <div v-if="taskDetail" class="bg-white border-b border-gray-200">
      <div class="flex px-6">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          @click="activeTab = tab.key"
          :class="[
            'px-4 py-3 text-sm font-medium border-b-2 transition-all flex items-center gap-2',
            activeTab === tab.key
              ? 'border-primary text-primary'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          ]"
        >
          <component :is="tab.icon" class="w-4 h-4" />
          {{ tab.label }}
          <span
            v-if="getTabBadge(tab.key) > 0"
            class="px-1.5 py-0.5 rounded-full text-xs bg-gray-100 text-gray-600"
          >
            {{ getTabBadge(tab.key) }}
          </span>
        </button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <Loader2 class="w-8 h-8 animate-spin text-primary" />
      <span class="ml-3 text-gray-500">加载中...</span>
    </div>

    <!-- 内容区域 -->
    <div v-else-if="taskDetail" class="flex-1 overflow-auto p-6">
      <!-- 概览Tab -->
      <div v-if="activeTab === 'overview'" class="space-y-6">
        <!-- 统计卡片 -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="bg-white rounded-xl border border-gray-200 p-4">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center">
                <FileText class="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <p class="text-sm text-gray-500">功能点</p>
                <p class="text-xl font-bold text-gray-900">{{ taskDetail.requirements?.length || taskDetail.saved_count || 0 }}</p>
              </div>
            </div>
          </div>

          <div class="bg-white rounded-xl border border-gray-200 p-4">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg bg-teal-50 flex items-center justify-center">
                <TestTube class="w-5 h-5 text-teal-600" />
              </div>
              <div>
                <p class="text-sm text-gray-500">测试用例</p>
                <p class="text-xl font-bold text-gray-900">{{ taskDetail.testcases?.length || taskDetail.saved_count || 0 }}</p>
              </div>
            </div>
          </div>

          <div class="bg-white rounded-xl border border-gray-200 p-4">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg bg-purple-50 flex items-center justify-center">
                <Clock class="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <p class="text-sm text-gray-500">执行耗时</p>
                <p class="text-xl font-bold text-gray-900">{{ formatDuration(taskDetail.stats?.duration_seconds) }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- 执行进度 -->
        <div class="bg-white rounded-xl border border-gray-200 p-6">
          <h3 class="text-sm font-medium text-gray-700 mb-4 flex items-center gap-2">
            <Zap class="w-4 h-4" />
            执行阶段
          </h3>
          <div class="flex items-center gap-2 flex-wrap">
            <div
              v-for="phase in taskDetail.phases"
              :key="phase.code"
              :class="[
                'px-3 py-2 rounded-lg border text-sm flex items-center gap-2',
                getPhaseClass(phase)
              ]"
            >
              <component
                :is="getPhaseIcon(phase)"
                :class="['w-4 h-4', phase.status === 'running' && 'animate-spin']"
              />
              {{ phase.name }}
              <span class="text-xs opacity-70">{{ phase.progress }}%</span>
            </div>
          </div>
        </div>

        <!-- 基本信息和执行日志 -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- 基本信息 -->
          <div class="bg-white rounded-xl border border-gray-200 p-6">
            <h3 class="text-sm font-medium text-gray-700 mb-4 flex items-center gap-2">
              <Info class="w-4 h-4" />
              基本信息
            </h3>
            <div class="space-y-4">
              <div class="flex justify-between">
                <span class="text-sm text-gray-500">项目</span>
                <span class="text-sm font-medium text-gray-900">{{ taskDetail.project_id ? `项目${taskDetail.project_id}` : '未关联' }}</span>
              </div>
              <div v-if="taskDetail.requirement_name" class="flex justify-between">
                <span class="text-sm text-gray-500">需求名称</span>
                <span class="text-sm font-medium text-gray-900">{{ taskDetail.requirement_name }}</span>
              </div>
              <div v-if="taskDetail.function_names?.length" class="flex justify-between">
                <span class="text-sm text-gray-500">功能点</span>
                <span class="text-sm font-medium text-gray-900">{{ taskDetail.function_names.length }} 个</span>
              </div>
              <div class="flex justify-between">
                <span class="text-sm text-gray-500">开始时间</span>
                <span class="text-sm text-gray-900">{{ taskDetail.started_at ? formatDate(taskDetail.started_at) : '-' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-sm text-gray-500">完成时间</span>
                <span class="text-sm text-gray-900">{{ taskDetail.completed_at ? formatDate(taskDetail.completed_at) : '-' }}</span>
              </div>
              <div v-if="taskDetail.error_message" class="p-3 bg-red-50 rounded-lg">
                <p class="text-xs text-red-500 mb-1">错误信息</p>
                <p class="text-sm text-red-600">{{ taskDetail.error_message }}</p>
              </div>
            </div>
          </div>

          <!-- 执行日志（仅运行时显示） -->
          <div v-if="isTaskRunning" class="bg-white rounded-xl border border-gray-200 p-6">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-sm font-medium text-gray-700 flex items-center gap-2">
                <Terminal class="w-4 h-4" />
                实时日志
                <span :class="[
                  'px-2 py-0.5 rounded text-xs flex items-center gap-1',
                  wsConnected ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                ]">
                  <component :is="wsConnected ? Wifi : WifiOff" class="w-3 h-3" />
                  {{ wsConnected ? '已连接' : '连接中' }}
                </span>
              </h3>
              <button
                @click="autoScroll = !autoScroll"
                :class="[
                  'px-2 py-1 rounded text-xs',
                  autoScroll ? 'bg-primary/10 text-primary' : 'bg-gray-100 text-gray-500'
                ]"
              >
                {{ autoScroll ? '自动滚动' : '暂停' }}
              </button>
            </div>
            <div class="h-48 overflow-auto bg-gray-50 rounded-lg p-3 space-y-2">
              <div
                v-for="log in logs.slice(-10)"
                :key="log.id"
                :class="[
                  'text-xs p-2 rounded',
                  getAgentClass(log.agent_name)
                ]"
              >
                <span class="font-medium">[{{ log.agent_name }}]</span>
                <span class="ml-2">{{ log.content }}</span>
              </div>
              <div v-if="logs.length === 0" class="text-center text-gray-400 py-4">
                等待日志...
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 功能点Tab -->
      <div v-if="activeTab === 'requirements'">
        <RequirementList :requirements="taskDetail.requirements || []" />
      </div>

      <!-- 测试用例Tab -->
      <div v-if="activeTab === 'testcases'">
        <TestCaseList :testcases="taskDetail.testcases || []" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.task-detail-page {
  height: calc(100vh - 64px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.task-detail-page.fullscreen-mode {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 100;
  height: 100vh;
}
</style>
