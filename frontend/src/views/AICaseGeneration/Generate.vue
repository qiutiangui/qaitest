<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, type Ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  Upload, FileText, Send, Loader, CheckCircle, XCircle,
  Download, Sparkles, Zap, ListChecks, TestTube, Link2, Copy, ArrowRight,
  BookOpen, MessageSquare, Database, Wand2, ShieldCheck, Settings, Eye,
  BarChart3, ClipboardCheck, Save
} from 'lucide-vue-next'
import { ElMessage, ElDrawer } from 'element-plus'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import useProjectStore from '@/stores/project'
import useRequirementStore from '@/stores/requirement'
import useTestcaseStore from '@/stores/testcase'
import { requirementApi } from '@/api/requirement'
import { testcaseApi } from '@/api/testcase'
import ragApi from '@/api/rag'
import { modelConfigApi } from '@/api/modelConfig'
import { connectWebSocket, disconnectWebSocket, WebSocketMessage } from '@/api/websocket'

const router = useRouter()
const projectStore = useProjectStore()
const requirementStore = useRequirementStore()
const testcaseStore = useTestcaseStore()

// Markdown渲染函数
const renderMarkdown = (content: string): string => {
  if (!content) return ''
  const html = marked.parse(content, { async: false }) as string
  return DOMPurify.sanitize(html)
}

// Tab切换：手动输入 | 文档上传 | 飞书文档
const inputMode = ref<'manual' | 'document' | 'feishu'>('document')

// 控制输入面板显示（生成时隐藏）
const showInputPanel = ref(true)

// 输入数据
const requirementName = ref('')
const requirementDescription = ref('')
const selectedProjectId = ref<number | null>(null)
const uploadedFiles = ref<File[]>([])
const fileNames = ref<string[]>([])
const feishuDocUrl = ref('')
const isFeishuConfigured = ref(false)

// 模型配置
const selectedRequirementAnalyzeModel = ref('')
const selectedTestcaseGenerateModel = ref('')
const selectedTestcaseReviewModel = ref('')

// ========== 新架构：统一日志系统 ==========

// 日志条目类型
interface LogEntry {
  id: string
  timestamp: Date
  agent: string      // Agent中文名
  agentCode: string  // Agent原始代码
  type: 'info' | 'success' | 'error' | 'thinking' | 'stream'
  content: string
  color: string       // 边框颜色
  icon: any          // 图标组件
}

// 生成状态
const isGenerating = ref(false)
const taskId = ref('')
const generationComplete = ref(false)

// 日志列表
const logs = ref<LogEntry[]>([])
const logContainerRef = ref<HTMLElement | null>(null)

// 日志过滤器
const showStreamLogs = ref(true)  // 显示流式日志
const showThinkingLogs = ref(true)  // 显示思考日志

// 过滤后的日志
const filteredLogs = computed(() => {
  return logs.value.filter(log => {
    if (log.type === 'stream' && !showStreamLogs.value) return false
    if (log.type === 'thinking' && !showThinkingLogs.value) return false
    return true
  })
})

// 当前活跃的Agent
const activeAgent = ref<string | null>(null)

// 后端推送的进度
const backendProgress = ref(0)

// 统计数据
const statsInfo = ref({
  chunkCount: 0,
  functionCount: 0,
  testcaseCount: 0,
  requirementAnalysisTime: '',
  requirementReviewTime: '',
  testcaseGenerationTime: '',
  testcaseReviewTime: '',
  totalTime: '',
  requirementReviewConclusion: '',
  testcaseReviewConclusion: '',
  requirementAnalysisModel: '',
  requirementReviewModel: '',
  testcaseGenerationModel: '',
  testcaseReviewModel: '',
  // 新增字段
  saved_ids: [] as number[],  // 测试用例ID列表
  functionIds: [] as number[],  // 功能点ID列表
  stageTimings: {  // 各阶段耗时统计
    requirement_analysis: 0,
    testcase_generation: 0,
    total: 0,
  },
  reviewConclusion: {  // 评审结论
    approved: true,
    summary: '',
    total_testcases: 0,
    coverage_rate: 0,
    issues: [] as string[],
    suggestions: [] as string[],
  },
  modelInfo: {  // AI模型信息
    testcase_generate_model: '',
    testcase_review_model: '',
  },
})

// 阶段结果
const streamedFunctionPoints = ref<any[]>([])
const streamedTestCases = ref<any[]>([])

// 评审结论（用于渲染美观卡片）
interface ReviewConclusion {
  approved: boolean
  summary: string
  total_testcases: number
  coverage_rate: string
  issues: Array<{ severity: string; testcase_index: number; issue: string; suggestion: string }>
  suggestions: string[]
}
const reviewConclusion = ref<ReviewConclusion | null>(null)

// 解析消息内容（豆包风格 - 处理进度和Agent标签）
const parseMessageContent = (content: string): { type: 'progress' | 'normal'; progress?: number; text: string } => {
  // 检测 [AGENT]...[/AGENT] 标签（优先处理）
  const agentMatch = content.match(/\[AGENT\](\w+)\[\/AGENT\](.*)/)
  if (agentMatch) {
    const agentCode = agentMatch[1]
    const remainingText = agentMatch[2] || ''
    activeAgent.value = agentCode
    return { type: 'progress', progress: backendProgress.value, text: remainingText }
  }

  // 检测 [PROGRESS]...[/PROGRESS] 标签（兼容旧逻辑）
  const progressMatch = content.match(/\[PROGRESS\](\d+)\[\/PROGRESS\]/)
  if (progressMatch) {
    const progress = parseInt(progressMatch[1], 10)
    backendProgress.value = progress

    // 从进度消息中提取 agent 信息并更新 activeAgent
    const oldAgentMatch = content.match(/阶段更新:\s*(\w+)/)
    if (oldAgentMatch && oldAgentMatch[1]) {
      activeAgent.value = oldAgentMatch[1]
    }

    return { type: 'progress', progress, text: content }
  }
  return { type: 'normal', text: content }
}

// Agent配置映射（7个核心智能体）
const agentConfig: Record<string, {
  name: string
  color: string
  icon: any
  phase: 'requirement' | 'testcase'
  step: number  // 步骤序号
  stepName: string  // 步骤名称
}> = {
  // 需求分析阶段 - 3个智能体
  'RequirementAcquireAgent': { 
    name: '需求获取', 
    color: 'blue', 
    icon: BookOpen, 
    phase: 'requirement',
    step: 1,
    stepName: '需求摘要生成'
  },
  'RequirementAnalysisAgent': { 
    name: 'AI分析', 
    color: 'purple', 
    icon: Wand2, 
    phase: 'requirement',
    step: 2,
    stepName: '需求分析报告生成'
  },
  'RequirementOutputAgent': { 
    name: '需求输出', 
    color: 'green', 
    icon: FileText, 
    phase: 'requirement',
    step: 3,
    stepName: '功能点JSON生成'
  },
  // 用例生成阶段 - 4个智能体
  'TestCaseGenerateAgent': { 
    name: '用例生成', 
    color: 'orange', 
    icon: TestTube, 
    phase: 'testcase',
    step: 4,
    stepName: '测试用例生成'
  },
  'TestCaseReviewAgent': { 
    name: '用例评审', 
    color: 'indigo', 
    icon: ShieldCheck, 
    phase: 'testcase',
    step: 5,
    stepName: '用例评审优化'
  },
  'TestCaseFinalizeAgent': { 
    name: '用例定稿', 
    color: 'pink', 
    icon: CheckCircle, 
    phase: 'testcase',
    step: 6,
    stepName: '用例定稿入库'
  },
  'TestCaseInDatabaseAgent': { 
    name: '数据保存', 
    color: 'teal', 
    icon: Save, 
    phase: 'testcase',
    step: 7,
    stepName: '数据持久化'
  },
  // ========== 中文名称映射（兼容后端旧代码）==========
  '需求获取': { 
    name: '需求获取', 
    color: 'blue', 
    icon: BookOpen, 
    phase: 'requirement',
    step: 1,
    stepName: '需求摘要生成'
  },
  'AI分析': { 
    name: 'AI分析', 
    color: 'purple', 
    icon: Wand2, 
    phase: 'requirement',
    step: 2,
    stepName: '需求分析报告生成'
  },
  '需求输出': { 
    name: '需求输出', 
    color: 'green', 
    icon: FileText, 
    phase: 'requirement',
    step: 3,
    stepName: '功能点JSON生成'
  },
  '用例生成': { 
    name: '用例生成', 
    color: 'orange', 
    icon: TestTube, 
    phase: 'testcase',
    step: 4,
    stepName: '测试用例生成'
  },
  '用例评审': { 
    name: '用例评审', 
    color: 'indigo', 
    icon: ShieldCheck, 
    phase: 'testcase',
    step: 5,
    stepName: '用例评审优化'
  },
  '格式优化': { 
    name: '用例定稿', 
    color: 'pink', 
    icon: CheckCircle, 
    phase: 'testcase',
    step: 6,
    stepName: '用例定稿入库'
  },
  '数据保存': { 
    name: '数据保存', 
    color: 'teal', 
    icon: Save, 
    phase: 'testcase',
    step: 7,
    stepName: '数据持久化'
  },
  // 系统消息
  'System': { 
    name: '系统', 
    color: 'gray', 
    icon: Settings, 
    phase: 'requirement',
    step: 0,
    stepName: ''
  },
}

// 颜色映射
const colorClasses: Record<string, { border: string, bg: string, text: string, badge: string }> = {
  blue: { border: 'border-l-blue-500', bg: 'bg-blue-50', text: 'text-blue-600', badge: 'bg-blue-100 text-blue-700' },
  purple: { border: 'border-l-purple-500', bg: 'bg-purple-50', text: 'text-purple-600', badge: 'bg-purple-100 text-purple-700' },
  green: { border: 'border-l-green-500', bg: 'bg-green-50', text: 'text-green-600', badge: 'bg-green-100 text-green-700' },
  orange: { border: 'border-l-orange-500', bg: 'bg-orange-50', text: 'text-orange-600', badge: 'bg-orange-100 text-orange-700' },
  indigo: { border: 'border-l-indigo-500', bg: 'bg-indigo-50', text: 'text-indigo-600', badge: 'bg-indigo-100 text-indigo-700' },
  pink: { border: 'border-l-pink-500', bg: 'bg-pink-50', text: 'text-pink-600', badge: 'bg-pink-100 text-pink-700' },
  teal: { border: 'border-l-teal-500', bg: 'bg-teal-50', text: 'text-teal-600', badge: 'bg-teal-100 text-teal-700' },
  cyan: { border: 'border-l-cyan-500', bg: 'bg-cyan-50', text: 'text-cyan-600', badge: 'bg-cyan-100 text-cyan-700' },
  amber: { border: 'border-l-amber-500', bg: 'bg-amber-50', text: 'text-amber-600', badge: 'bg-amber-100 text-amber-700' },
  gray: { border: 'border-l-gray-500', bg: 'bg-gray-50', text: 'text-gray-600', badge: 'bg-gray-100 text-gray-700' },
}

// 添加日志
const addLog = (agentCode: string, type: 'info' | 'success' | 'error' | 'thinking' | 'stream', content: string) => {
  const config = agentConfig[agentCode] || { name: agentCode, color: 'gray', icon: Settings, phase: 'requirement' }
  
  const entry: LogEntry = {
    id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    timestamp: new Date(),
    agent: config.name,
    agentCode,
    type,
    content,
    color: config.color,
    icon: config.icon,
  }
  
  logs.value.push(entry)
  
  // 根据 agent 名称映射到正确的配置，更新 activeAgent
  // 这确保进度指示器能正确反映当前步骤
  const agentMapping: Record<string, string> = {
    'System': agentCode,  // 保持原值
    // 英文Agent名称
    'TestCaseGenerateAgent': 'TestCaseGenerateAgent',
    'TestCaseReviewAgent': 'TestCaseReviewAgent',
    'TestCaseFinalizeAgent': 'TestCaseFinalizeAgent',
    'TestCaseInDatabaseAgent': 'TestCaseInDatabaseAgent',
    'RequirementAcquireAgent': 'RequirementAcquireAgent',
    'RequirementAnalysisAgent': 'RequirementAnalysisAgent',
    'RequirementOutputAgent': 'RequirementOutputAgent',
    // 中文名称映射（对应7大智能体）
    '需求获取': 'RequirementAcquireAgent',
    'AI分析': 'RequirementAnalysisAgent',
    '需求输出': 'RequirementOutputAgent',
    '用例生成': 'TestCaseGenerateAgent',
    '用例评审': 'TestCaseReviewAgent',
    '格式优化': 'TestCaseFinalizeAgent',
    '数据保存': 'TestCaseInDatabaseAgent',
  }
  
  // 在测试用例生成阶段，更新 activeAgent
  if (isInTestcasePhase.value) {
    const mappedAgent = agentMapping[agentCode]
    if (mappedAgent && mappedAgent !== 'System') {
      activeAgent.value = mappedAgent
    }
  } else {
    const mappedAgent = agentMapping[agentCode]
    if (mappedAgent) {
      activeAgent.value = mappedAgent
    }
  }
  
  // 自动滚动
  nextTick(() => {
    if (logContainerRef.value) {
      logContainerRef.value.scrollTop = logContainerRef.value.scrollHeight
    }
  })
}

// 获取Agent配置
const getAgentConfig = (agentCode: string) => {
  return agentConfig[agentCode] || { name: agentCode, color: 'gray', icon: Settings }
}

// 计算当前阶段（根据进度条百分比判断）
const currentPhase = computed(() => {
  const progress = backendProgress.value
  if (progress === 0 && !isGenerating.value) return null
  if (progress <= 50) return 'requirement'
  return 'testcase'
})

// 计算当前阶段进度百分比
const phaseProgress = computed(() => {
  const progress = backendProgress.value
  
  if (progress > 0) {
    return {
      requirement: Math.min(progress, 50),
      testcase: Math.max(0, progress - 50),
      overall: progress
    }
  }
  
  return { requirement: 0, testcase: 0, overall: 0 }
})

// 流程开始时间（用于计算整体耗时）
const pipelineStartTime = ref<number>(0)

// 是否已切换到测试用例生成阶段（防止日志覆盖进度指示器）
const isInTestcasePhase = ref(false)

// 项目列表
const projects = computed(() => projectStore.projects)

onMounted(async () => {
  await projectStore.fetchProjects({ page_size: 100 })
  // 检查飞书配置
  checkFeishuConfig()
  // 从后端API获取模型配置
  await loadModelConfig()
})

// 从后端API加载模型配置
const loadModelConfig = async () => {
  try {
    // 从后端API获取默认模型配置
    const response = await modelConfigApi.getModelStatus()

    // 需求分析模型
    if (response.requirement_analyze?.configured && response.requirement_analyze.provider) {
      if (response.requirement_analyze.is_custom) {
        // 自定义模型格式: custom:custom_id:model_name
        selectedRequirementAnalyzeModel.value = `custom:${response.requirement_analyze.id}:${response.requirement_analyze.model_name}`
      } else {
        // 内置模型格式: provider:model_name
        selectedRequirementAnalyzeModel.value = `${response.requirement_analyze.provider}:${response.requirement_analyze.model_name}`
      }
    }

    // 用例生成模型
    if (response.testcase_generate?.configured && response.testcase_generate.provider) {
      if (response.testcase_generate.is_custom) {
        selectedTestcaseGenerateModel.value = `custom:${response.testcase_generate.id}:${response.testcase_generate.model_name}`
      } else {
        selectedTestcaseGenerateModel.value = `${response.testcase_generate.provider}:${response.testcase_generate.model_name}`
      }
    }

    // 用例评审模型
    if (response.testcase_review?.configured && response.testcase_review.provider) {
      if (response.testcase_review.is_custom) {
        selectedTestcaseReviewModel.value = `custom:${response.testcase_review.id}:${response.testcase_review.model_name}`
      } else {
        selectedTestcaseReviewModel.value = `${response.testcase_review.provider}:${response.testcase_review.model_name}`
      }
    }

    console.log('模型配置已加载:', {
      requirement_analyze: selectedRequirementAnalyzeModel.value,
      testcase_generate: selectedTestcaseGenerateModel.value,
      testcase_review: selectedTestcaseReviewModel.value
    })
  } catch (error) {
    console.error('加载模型配置失败:', error)
  }
}

// 检查飞书配置状态
const checkFeishuConfig = async () => {
  try {
    const res = await ragApi.getFeishuConfig()
    isFeishuConfigured.value = res.configured
  } catch {
    isFeishuConfigured.value = false
  }
}

onUnmounted(() => {
  disconnectWebSocket()
})

// 文件上传处理（支持多文件）
const handleFileUpload = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    const validTypes = ['.txt', '.md', '.pdf', '.docx']
    const newFiles: File[] = []
    const invalidFiles: string[] = []

    // 遍历所有选中的文件
    Array.from(target.files).forEach(file => {
      const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase()

      if (validTypes.includes(ext)) {
        newFiles.push(file)
      } else {
        invalidFiles.push(file.name)
      }
    })

    if (invalidFiles.length > 0) {
      ElMessage.warning(`以下文件格式不支持: ${invalidFiles.join(', ')}`)
    }

    if (newFiles.length > 0) {
      uploadedFiles.value = newFiles
      fileNames.value = newFiles.map(f => f.name)
      ElMessage.success(`已选择 ${newFiles.length} 个文件`)
    }
  }
}

// 清除所有文件
const clearAllFiles = () => {
  uploadedFiles.value = []
  fileNames.value = []
}

// 移除单个文件
const removeFile = (index: number) => {
  uploadedFiles.value.splice(index, 1)
  fileNames.value.splice(index, 1)
}

// 开始生成测试用例
const startGeneration = async () => {
  // 验证输入
  if (inputMode.value === 'manual') {
    if (!requirementName.value) {
      ElMessage.warning('请输入需求名称')
      return
    }
    if (!requirementDescription.value) {
      ElMessage.warning('请输入需求描述')
      return
    }
  } else if (inputMode.value === 'document') {
    if (!requirementName.value) {
      ElMessage.warning('请输入需求名称')
      return
    }
    if (uploadedFiles.value.length === 0) {
      ElMessage.warning('请上传至少一个需求文档')
      return
    }
  } else if (inputMode.value === 'feishu') {
    if (!requirementName.value) {
      ElMessage.warning('请输入需求名称')
      return
    }
    if (!feishuDocUrl.value) {
      ElMessage.warning('请输入飞书文档URL')
      return
    }
  }

  // ✅ 新增：项目选择必填验证（所有模式都需要）
  if (!selectedProjectId.value) {
    ElMessage.warning('请选择项目（RAG检索需要项目标识）')
    return
  }

  // 重置状态
  isGenerating.value = true
  showInputPanel.value = false  // 隐藏输入面板
  pipelineStartTime.value = Date.now()
  generationComplete.value = false
  isInTestcasePhase.value = false  // 重置阶段标记
  activeAgent.value = null
  backendProgress.value = 0
  logs.value = []
  streamedFunctionPoints.value = []
  streamedTestCases.value = []
  statsInfo.value = {
    chunkCount: 0, functionCount: 0, testcaseCount: 0,
    requirementAnalysisTime: '', requirementReviewTime: '',
    testcaseGenerationTime: '', testcaseReviewTime: '',
    totalTime: '', requirementReviewConclusion: '',
    testcaseReviewConclusion: '', requirementAnalysisModel: '',
    requirementReviewModel: '', testcaseGenerationModel: '',
    testcaseReviewModel: '',
  }
  
  taskId.value = `task-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  
  addLog('System', 'info', `🚀 开始AI用例生成流程...`)

  try {
    let result: { task_id: string; message?: string; total_files?: number }

    // 构建需求分析模型配置
    let modelConfig: { requirement_analyze_model?: { provider: string; custom_id?: number; model?: string } } = {}
    if (selectedRequirementAnalyzeModel.value) {
      const parts = selectedRequirementAnalyzeModel.value.split(':')
      if (parts[0] === 'custom') {
        modelConfig.requirement_analyze_model = {
          provider: 'custom',
          custom_id: parseInt(parts[1]),
          model: parts.slice(2).join(':')
        }
      } else {
        modelConfig.requirement_analyze_model = {
          provider: parts[0],
          model: parts[1]
        }
      }
    }
    console.log('需求分析模型配置:', selectedRequirementAnalyzeModel.value, '->', modelConfig)

    if (inputMode.value === 'manual') {
      const formData = new FormData()
      formData.append('requirement_name', requirementName.value)
      formData.append('description', requirementDescription.value)
      if (selectedProjectId.value) {
        formData.append('project_id', String(selectedProjectId.value))
      }
      result = await requirementApi.analyze(formData, modelConfig)
    } else if (inputMode.value === 'feishu') {
      ElMessage.info('正在从飞书文档加载内容...')
      const indexResult = await ragApi.indexFeishu({
        project_id: selectedProjectId.value || 0,
        doc_url: feishuDocUrl.value,
        requirement_name: requirementName.value
      })
      if (!indexResult.success) {
        throw new Error(indexResult.error || '飞书文档索引失败')
      }
      ElMessage.success('已从飞书文档加载内容，正在分析...')
      const formData = new FormData()
      formData.append('requirement_name', requirementName.value)
      formData.append('source', 'feishu')
      formData.append('feishu_url', feishuDocUrl.value)
      if (selectedProjectId.value) {
        formData.append('project_id', String(selectedProjectId.value))
      }
      result = await requirementApi.analyze(formData, modelConfig)
    } else {
      result = await requirementApi.analyzeMultiple(
        uploadedFiles.value,
        requirementName.value,
        selectedProjectId.value || undefined,
        undefined, // versionId
        modelConfig // 添加模型配置
      )
      ElMessage.info(`开始并行分析 ${uploadedFiles.value.length} 个文档...`)
    }

    taskId.value = result.task_id

    // 建立WebSocket连接
    connectWebSocket(taskId.value, {
      onMessage: handleWebSocketMessage,
      onError: (error) => {
        console.error('[WebSocket] 错误:', error)
        addLog('System', 'error', 'WebSocket连接错误')
      },
      onClose: () => {
        console.log('[WebSocket] 连接已关闭')
      },
      onOpen: () => {
        console.log('[WebSocket] 连接成功')
        addLog('System', 'success', 'WebSocket连接成功')
      }
    })

  } catch (error: any) {
    ElMessage.error(error.message || '启动生成失败')
    addLog('System', 'error', `启动失败: ${error.message}`)
    isGenerating.value = false
  }
}

// WebSocket消息处理 - 统一日志系统
const handleWebSocketMessage = (message: WebSocketMessage) => {
  const { agent, type, content, data } = message
  
  // 调试日志（减少输出）
  if (type !== 'stream' && type !== 'pong') {
    console.log('[WebSocket] 收到消息:', type, agent, content?.substring(0, 50))
    // 如果是 complete 类型且有 data，打印 data
    if (type === 'complete' && data) {
      console.log('[WebSocket] complete消息的data:', JSON.stringify(data).substring(0, 200))
    }
  }
  
  // 处理错误消息
  if (type === 'error') {
    addLog(agent, 'error', content)
    handleError(content)
    return
  }
  
  // 处理流式内容 - 合并更新，减少 DOM 操作
  if (type === 'stream') {
    const lastLog = logs.value[logs.value.length - 1]
    if (lastLog && lastLog.agentCode === agent && lastLog.type === 'stream') {
      lastLog.content += content
    } else {
      addLog(agent, 'stream', content)
    }
    // 节流滚动 - 只在必要时滚动
    throttleScroll()
    return
  }
  
  // 处理流式开始
  if (type === 'stream_start') {
    addLog(agent, 'stream', content)
    return
  }
  
  // 处理流式结束
  if (type === 'stream_end') {
    const lastLog = logs.value[logs.value.length - 1]
    if (lastLog && lastLog.agentCode === agent) {
      lastLog.content += content
      if (lastLog.type === 'stream') {
        lastLog.type = 'info'
      }
    } else {
      addLog(agent, 'info', content)
    }
    return
  }
  
  // 处理进度消息（包含 [PROGRESS] 或 [AGENT] 标签）
  if (type === 'progress') {
    if (content && (content.includes('[PROGRESS]') || content.includes('[AGENT]'))) {
      parseMessageContent(content)
    }
    return
  }
  
  // 处理thinking类型（实时思考）
  if (type === 'thinking') {
    // 过滤进度/Agent消息，不显示在日志中
    if (content && (content.includes('[PROGRESS]') || content.includes('[AGENT]'))) {
      parseMessageContent(content)
      return
    }
    const lastLog = logs.value[logs.value.length - 1]
    if (lastLog && lastLog.agentCode === agent && lastLog.type === 'thinking') {
      lastLog.content += content
    } else {
      addLog(agent, 'thinking', content)
    }
    return
  }
  
  // 处理response类型
  if (type === 'response') {
    addLog(agent, 'info', content)
    return
  }
  
  // 处理complete类型
  if (type === 'complete') {
    handleStepComplete(agent, data)
    return
  }
  
  // 处理其他未知类型
  if (content) {
    addLog(agent, 'info', content)
  }
}

// 节流滚动函数
let scrollTimer: number | null = null
const throttleScroll = () => {
  if (scrollTimer) return
  scrollTimer = window.setTimeout(() => {
    scrollTimer = null
    nextTick(() => {
      if (logContainerRef.value) {
        logContainerRef.value.scrollTop = logContainerRef.value.scrollHeight
      }
    })
  }, 100)
}

// 步骤完成消息处理
const handleStepComplete = (agent: string, data: any) => {
  switch (agent) {
    case 'RequirementOutputAgent':
      // 需求输出完成
      addLog('RequirementOutputAgent', 'success', '需求功能点保存完成')
      console.log('[handleStepComplete] RequirementOutputAgent data:', data)
      if (data) {
        statsInfo.value.chunkCount = data.chunkCount || 0  // 添加文档分块数量
        statsInfo.value.functionCount = data.functionCount || data.saved_ids?.length || data.count || 0
        console.log('[handleStepComplete] saved_ids:', data.saved_ids, 'isGenerating:', isGenerating.value)
        if (data.saved_ids?.length > 0) {
          addLog('System', 'success', `✅ 成功提取 ${data.saved_ids.length} 个功能点`)
          // 需求分析完成，重置 isGenerating，准备启动测试用例生成
          // 只在第一次收到 saved_ids 时启动测试用例生成
          if (isGenerating.value && !generationComplete.value) {
            isGenerating.value = false
            console.log('[handleStepComplete] 准备调用 generateTestCases（首次）')
            generateTestCases(data.saved_ids)
          } else {
            console.log('[handleStepComplete] 跳过重复调用')
          }
        }
      }
      break
    case 'step2_analysis':
      addLog('step2_analysis', 'success', '需求分析完成')
      break
    case 'step3_review':
      addLog('step3_review', 'success', '需求提取完成')
      if (data) {
        statsInfo.value.chunkCount = data.chunkCount || 0
        statsInfo.value.functionCount = data.functionCount || data.count || 0
        statsInfo.value.requirementAnalysisTime = data.requirementAnalysisTime || ''
        statsInfo.value.requirementReviewTime = data.requirementReviewTime || ''
        statsInfo.value.requirementReviewConclusion = data.requirementReviewConclusion || ''
        statsInfo.value.requirementAnalysisModel = data.requirementAnalysisModel || ''
        statsInfo.value.requirementReviewModel = data.requirementReviewModel || ''
        if (data.saved_ids?.length > 0) {
          addLog('System', 'success', `✅ 成功提取 ${data.saved_ids.length} 个功能点，开始生成测试用例...`)
          generateTestCases(data.saved_ids)
        }
      }
      break
    case 'step4_generate':
      addLog('step4_generate', 'success', '用例生成完成')
      handleTestcaseGenerationComplete(data)
      break
    case 'step5_review':
      // 更新进度条：标记数据保存阶段完成（最后一步）
      activeAgent.value = 'TestCaseInDatabaseAgent'
      generationComplete.value = true
      addLog('step5_review', 'success', '用例评审完成')
      if (pipelineStartTime.value > 0) {
        const totalMs = Date.now() - pipelineStartTime.value
        const totalSecs = totalMs / 1000
        statsInfo.value.totalTime = totalSecs < 60 
          ? `${totalSecs.toFixed(1)}s` 
          : `${Math.floor(totalSecs / 60)}m ${(totalSecs % 60).toFixed(1)}s`
      }
      if (data) {
        Object.assign(statsInfo.value, data)
        // 保存功能点ID
        if (data.function_ids) {
          statsInfo.value.functionIds = data.function_ids
        }
        // 保存耗时统计
        if (data.stage_timings) {
          statsInfo.value.stageTimings = data.stage_timings
        }
        // 保存评审结论
        if (data.review_conclusion) {
          statsInfo.value.reviewConclusion = data.review_conclusion
        }
        // 保存AI模型信息
        if (data.model_info) {
          statsInfo.value.modelInfo = data.model_info
        }
      }
      break
    case 'requirement_analysis':
      addLog('System', 'success', `🎉 需求分析完成！共提取 ${data?.saved_ids?.length || 0} 个功能点`)
      break
    case 'testcase_generation':
      addLog('System', 'success', `🎉 测试用例生成完成！共 ${data?.saved_ids?.length || 0} 个用例`)
      break
    // ========== 测试用例保存阶段处理 ==========
    case 'TestCaseInDatabaseAgent':
    case '数据保存':
      // 数据保存完成，标记整个生成流程结束
      isGenerating.value = false
      generationComplete.value = true
      activeAgent.value = 'TestCaseInDatabaseAgent'
      if (data) {
        // 更新测试用例数量
        statsInfo.value.testcaseCount = data.saved_ids?.length || data.count || 0
        // 兼容 count 字段（部分接口使用）
        if (data.count) {
          statsInfo.value.count = data.count
        }
        // 保存测试用例ID列表
        if (data.saved_ids) {
          statsInfo.value.saved_ids = data.saved_ids
        }
        // 保存功能点ID
        if (data.function_ids) {
          statsInfo.value.functionIds = data.function_ids
        }
        // 保存耗时统计
        if (data.stage_timings) {
          statsInfo.value.stageTimings = data.stage_timings
          // 计算总耗时
          const totalSecs = data.stage_timings.total || 0
          statsInfo.value.totalTime = totalSecs < 60
            ? `${totalSecs.toFixed(1)}s`
            : `${Math.floor(totalSecs / 60)}m ${(totalSecs % 60).toFixed(1)}s`
        }
        // 保存评审结论
        if (data.review_conclusion) {
          statsInfo.value.reviewConclusion = data.review_conclusion
        }
        // 保存AI模型信息
        if (data.model_info) {
          statsInfo.value.modelInfo = data.model_info
        }
        addLog('System', 'success', `🎉 测试用例生成完成！共保存 ${data.saved_ids?.length || data.count || 0} 个用例`)
        // 获取生成的测试用例
        if (data.saved_ids?.length > 0) {
          testcaseStore.fetchTestcases({ ids: data.saved_ids, page_size: 100 })
          streamedTestCases.value = testcaseStore.testcases
        }
      }
      break
  }
}

// 测试用例生成完成处理
const handleTestcaseGenerationComplete = async (data: any) => {
  isGenerating.value = false
  if (data?.saved_ids?.length > 0) {
    await testcaseStore.fetchTestcases({
      ids: data.saved_ids,
      page_size: 100
    })
    streamedTestCases.value = testcaseStore.testcases
    ElMessage.success(`✨ 测试用例生成完成！共 ${data.saved_ids.length} 个用例`)
  }
}

// 生成测试用例
const generateTestCases = async (requirementIds: number[]) => {
  addLog('System', 'info', `📋 开始生成测试用例（${requirementIds.length} 个功能点）...`)

  // 设置当前 Agent 为测试用例生成，开始第二阶段
  activeAgent.value = 'TestCaseGenerateAgent'
  isGenerating.value = true  // 标记测试用例生成开始
  generationComplete.value = false
  isInTestcasePhase.value = true  // 标记进入测试用例生成阶段

  // 构建模型配置
  const llmConfig: any = {}

  // 需求分析模型配置（用于用例生成过程中的需求分析）
  if (selectedRequirementAnalyzeModel.value) {
    const parts = selectedRequirementAnalyzeModel.value.split(':')
    if (parts[0] === 'custom') {
      llmConfig.requirement_analyze_model = {
        provider: 'custom',
        custom_id: parseInt(parts[1]),
        model: parts.slice(2).join(':')
      }
      console.log('使用自定义需求分析模型配置:', llmConfig.requirement_analyze_model)
    } else {
      llmConfig.requirement_analyze_model = { provider: parts[0], model: parts[1] }
      console.log('使用内置需求分析模型配置:', llmConfig.requirement_analyze_model)
    }
  }

  // 用例生成模型配置
  if (selectedTestcaseGenerateModel.value) {
    const parts = selectedTestcaseGenerateModel.value.split(':')
    if (parts[0] === 'custom') {
      // 自定义模型格式: custom:custom_id:model_name
      llmConfig.testcase_generate_model = {
        provider: 'custom',  // 后端会自动转换为枚举
        custom_id: parseInt(parts[1]),
        model: parts.slice(2).join(':')
      }
      console.log('使用自定义模型配置:', llmConfig.testcase_generate_model)
    } else {
      // 普通模型格式: provider:model_name
      llmConfig.testcase_generate_model = { provider: parts[0], model: parts[1] }
      console.log('使用内置模型配置:', llmConfig.testcase_generate_model)
    }
  } else {
    console.log('未配置用例生成模型，将使用默认模型')
  }

  // 用例评审模型配置
  if (selectedTestcaseReviewModel.value) {
    const parts = selectedTestcaseReviewModel.value.split(':')
    if (parts[0] === 'custom') {
      llmConfig.testcase_review_model = {
        provider: 'custom',
        custom_id: parseInt(parts[1]),
        model: parts.slice(2).join(':')
      }
    } else {
      llmConfig.testcase_review_model = { provider: parts[0], model: parts[1] }
    }
  }

  console.log('发送请求，llm_config:', JSON.stringify(llmConfig, null, 2))

  try {
    await testcaseApi.generate({
      requirement_ids: requirementIds,
      project_id: selectedProjectId.value || 0,
      task_id: taskId.value,
      llm_config: Object.keys(llmConfig).length > 0 ? llmConfig : undefined,
    })
  } catch (error: any) {
    addLog('System', 'error', `生成失败: ${error.message}`)
    ElMessage.error(error.message || '生成测试用例失败')
    isGenerating.value = false
    disconnectWebSocket()
  }
}

const handleError = (message: string) => {
  isGenerating.value = false
  ElMessage.error(`生成失败: ${message}`)
  disconnectWebSocket()
}

// 跳转到任务记录页面
const goToTaskRecords = () => {
  window.open('/ai-cases/task-records', '_blank')
}

// 跳转到功能点列表
const goToFunctionPoints = () => {
  const functionIds = statsInfo.value.functionIds
  if (functionIds && functionIds.length > 0) {
    window.open(`/requirements?ids=${functionIds.join(',')}`, '_blank')
  } else {
    window.open('/requirements', '_blank')
  }
}

// 跳转到测试用例列表
const goToTestCases = () => {
  const testcaseIds = statsInfo.value.saved_ids
  if (testcaseIds && testcaseIds.length > 0) {
    window.open(`/testcases?ids=${testcaseIds.join(',')}`, '_blank')
  } else {
    window.open('/testcases', '_blank')
  }
}

// 复制日志
const copyLogs = async () => {
  const logText = filteredLogs.value
    .map(log => `[${log.timestamp.toLocaleTimeString()}] ${log.agent}: ${log.content}`)
    .join('\n')
  
  try {
    await navigator.clipboard.writeText(logText)
    ElMessage.success('日志已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败')
  }
}

// 获取步骤状态（completed/active/pending）
const getStepStatus = (phase: number, stepInPhase: number): string => {
  if (!activeAgent.value) return 'pending'

  const config = agentConfig[activeAgent.value]
  if (!config) return 'pending'

  // 需求分析阶段（步骤1-3）
  if (phase === 1) {
    if (config.step > stepInPhase) return 'completed'
    if (config.step === stepInPhase) return 'active'
    return 'pending'
  }

  // 用例生成阶段（步骤4-7，对应 stepInPhase 1-4）
  if (phase === 2) {
    // 步骤4=生成, 5=评审, 6=定稿, 7=保存
    // stepInPhase 1-3 对应 config.step 4-6（已完成）
    // stepInPhase 4 对应 config.step 7（当前活跃）
    if (stepInPhase < 4 && config.step > stepInPhase + 3) return 'completed'
    if (config.step === stepInPhase + 3) return 'active'
    return 'pending'
  }

  return 'pending'
}

// 格式化时长
const formatDuration = (seconds: number) => {
  if (!seconds) return '0秒'
  if (seconds < 60) return `${Math.round(seconds)}秒`
  const minutes = Math.floor(seconds / 60)
  const secs = Math.round(seconds % 60)
  return secs > 0 ? `${minutes}分${secs}秒` : `${minutes}分钟`
}

// 跳转到任务详情页面
const resetForm = () => {
  requirementName.value = ''
  requirementDescription.value = ''
  uploadedFiles.value = []
  fileNames.value = []
  feishuDocUrl.value = ''
  generationComplete.value = false
  isGenerating.value = false
  isInTestcasePhase.value = false  // 重置阶段标记
  activeAgent.value = null
  logs.value = []
  streamedFunctionPoints.value = []
  streamedTestCases.value = []
  statsInfo.value = {
    chunkCount: 0, functionCount: 0, testcaseCount: 0,
    requirementAnalysisTime: '', requirementReviewTime: '',
    testcaseGenerationTime: '', testcaseReviewTime: '',
    totalTime: '', requirementReviewConclusion: '',
    testcaseReviewConclusion: '', requirementAnalysisModel: '',
    requirementReviewModel: '', testcaseGenerationModel: '',
    testcaseReviewModel: '',
  }
  disconnectWebSocket()
}

// 导出功能点到Excel
const exportFunctionPointsToExcel = async () => {
  if (streamedFunctionPoints.value.length === 0 && !taskId.value) {
    ElMessage.warning('暂无功能点可导出')
    return
  }

  ElMessage.loading({ message: '正在导出...', duration: 0 })

  try {
    const XLSX = await import('xlsx')

    let data: any[] = []

    // 优先从后端API根据任务ID获取完整数据
    if (taskId.value) {
      try {
        const res = await requirementApi.export(taskId.value)
        if (res.data && Array.isArray(res.data) && res.data.length > 0) {
          data = res.data
        }
      } catch (e) {
        console.log('使用流式数据导出')
      }
    }

    // 如果API没有数据，使用流式数据
    if (data.length === 0 && streamedFunctionPoints.value.length > 0) {
      data = streamedFunctionPoints.value.map((fp: any, index: number) => ({
        '序号': index + 1,
        '功能点名称': fp.name || '',
        '描述': fp.description || '',
        '类别': fp.category || '',
        '优先级': fp.priority || '',
        '所属项目': getProjectName(fp.project_id),
        '创建时间': fp.created_at ? formatDateTime(fp.created_at) : '',
      }))
    }

    if (data.length === 0) {
      ElMessage.warning('暂无功能点可导出')
      return
    }

    // 创建工作表
    const ws = XLSX.utils.json_to_sheet(data)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, '功能点')

    // 设置列宽
    ws['!cols'] = [
      { wch: 6 },   // 序号
      { wch: 25 },  // 名称
      { wch: 40 },  // 描述
      { wch: 12 },  // 类别
      { wch: 8 },   // 优先级
      { wch: 15 },  // 所属项目
      { wch: 18 },  // 创建时间
    ]

    // 导出
    const fileName = `功能点_${requirementName.value || 'export'}_${new Date().toISOString().split('T')[0]}.xlsx`
    XLSX.writeFile(wb, fileName)
    ElMessage.success(`导出成功：${data.length} 个功能点`)
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  }
}

// 导出测试用例到Excel
const exportTestCasesToExcel = async () => {
  if (streamedTestCases.value.length === 0 && !taskId.value) {
    ElMessage.warning('暂无测试用例可导出')
    return
  }

  ElMessage.loading({ message: '正在导出...', duration: 0 })

  try {
    const XLSX = await import('xlsx')

    let data: any[] = []

    // 优先从后端API根据任务ID获取完整数据
    if (taskId.value) {
      try {
        const res = await testcaseApi.export(taskId.value, 'excel')
        if (res.data && Array.isArray(res.data) && res.data.length > 0) {
          data = res.data
        }
      } catch (e) {
        console.log('使用流式数据导出')
      }
    }

    // 如果API没有数据，使用流式数据
    if (data.length === 0 && streamedTestCases.value.length > 0) {
      streamedTestCases.value.forEach((tc: any, index: number) => {
        // 处理步骤
        let stepsText = ''
        if (tc.steps && Array.isArray(tc.steps) && tc.steps.length > 0) {
          stepsText = tc.steps.map((step: any, i: number) =>
            `${i + 1}. ${step.description || ''}\n   预期: ${step.expected_result || ''}`
          ).join('\n')
        }

        data.push({
          '序号': index + 1,
          '用例标题': tc.title || '',
          '描述': tc.desc || tc.description || '',
          '前置条件': tc.preconditions || '',
          '测试数据': tc.test_data || '',
          '优先级': tc.priority || '',
          '状态': tc.status || '',
          '标签': tc.tags || '',
          '测试步骤': stepsText,
        })
      })
    }

    if (data.length === 0) {
      ElMessage.warning('暂无测试用例可导出')
      return
    }

    // 创建工作表
    const ws = XLSX.utils.json_to_sheet(data)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, '测试用例')

    // 设置列宽
    ws['!cols'] = [
      { wch: 6 },   // 序号
      { wch: 25 },  // 标题
      { wch: 30 },  // 描述
      { wch: 25 },  // 前置条件
      { wch: 20 },  // 测试数据
      { wch: 8 },   // 优先级
      { wch: 8 },   // 状态
      { wch: 12 },  // 标签
      { wch: 50 },  // 测试步骤
    ]

    // 导出
    const fileName = `测试用例_${requirementName.value || 'export'}_${new Date().toISOString().split('T')[0]}.xlsx`
    XLSX.writeFile(wb, fileName)
    ElMessage.success(`导出成功：${data.length} 个用例`)
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  }
}

// 导出全部到Excel（两个工作薄）
const exportAllToExcel = async () => {
  if (streamedFunctionPoints.value.length === 0 && streamedTestCases.value.length === 0) {
    ElMessage.warning('暂无数据可导出')
    return
  }

  ElMessage.loading({ message: '正在导出...', duration: 0 })

  try {
    const XLSX = await import('xlsx')
    const wb = XLSX.utils.book_new()

    // 功能点工作表
    if (streamedFunctionPoints.value.length > 0) {
      const fpData = streamedFunctionPoints.value.map((fp: any, index: number) => ({
        '序号': index + 1,
        '功能点名称': fp.name || '',
        '描述': fp.description || '',
        '类别': fp.category || '',
        '优先级': fp.priority || '',
        '所属项目': getProjectName(fp.project_id),
      }))
      const ws1 = XLSX.utils.json_to_sheet(fpData)
      XLSX.utils.book_append_sheet(wb, ws1, '功能点')
      ws1['!cols'] = [
        { wch: 6 }, { wch: 25 }, { wch: 40 }, { wch: 12 }, { wch: 8 }, { wch: 15 }
      ]
    }

    // 测试用例工作表
    if (streamedTestCases.value.length > 0) {
      const tcData: any[] = []
      streamedTestCases.value.forEach((tc: any, index: number) => {
        let stepsText = ''
        if (tc.steps && Array.isArray(tc.steps) && tc.steps.length > 0) {
          stepsText = tc.steps.map((step: any, i: number) =>
            `${i + 1}. ${step.description || ''} → ${step.expected_result || ''}`
          ).join('\n')
        }
        tcData.push({
          '序号': index + 1,
          '用例标题': tc.title || '',
          '描述': tc.desc || tc.description || '',
          '前置条件': tc.preconditions || '',
          '测试数据': tc.test_data || '',
          '优先级': tc.priority || '',
          '状态': tc.status || '',
          '测试步骤': stepsText,
        })
      })
      const ws2 = XLSX.utils.json_to_sheet(tcData)
      XLSX.utils.book_append_sheet(wb, ws2, '测试用例')
      ws2['!cols'] = [
        { wch: 6 }, { wch: 25 }, { wch: 30 }, { wch: 25 }, { wch: 20 }, { wch: 8 }, { wch: 8 }, { wch: 50 }
      ]
    }

    // 导出
    const fileName = `AI用例生成_${requirementName.value || 'export'}_${new Date().toISOString().split('T')[0]}.xlsx`
    XLSX.writeFile(wb, fileName)
    ElMessage.success(`导出成功`)
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  }
}

// 格式化功能点列表（用于显示）
const formatFunctionPoints = (functionPoints: any[]): string => {
  if (!functionPoints || functionPoints.length === 0) return ''

  const lines: string[] = []
  functionPoints.forEach((fp: any, index: number) => {
    if (index > 0) lines.push('') // 每个功能点之间空一行
    lines.push(`【${index + 1}】${fp.name || '未命名'}`)
    lines.push(`   描述：${fp.description || '无'}`)
    if (fp.category) lines.push(`   类别：${fp.category}`)
    if (fp.priority) lines.push(`   优先级：${fp.priority}`)
  })
  return lines.join('\n')
}

// 格式化测试用例列表（用于显示）
const formatTestCases = (testCases: any[]): string => {
  if (!testCases || testCases.length === 0) return ''

  const lines: string[] = []
  testCases.forEach((tc: any, index: number) => {
    if (index > 0) lines.push('') // 每个用例之间空一行
    lines.push(`【${index + 1}】${tc.title || '未命名'}`)
    lines.push(`   描述：${tc.desc || tc.description || '无'}`)
    lines.push(`   前置条件：${tc.preconditions || '无'}`)
    if (tc.test_data) lines.push(`   测试数据：${tc.test_data}`)
    if (tc.priority) lines.push(`   优先级：${tc.priority}`)
    if (tc.status) lines.push(`   状态：${tc.status}`)

    // 处理步骤
    if (tc.steps && Array.isArray(tc.steps) && tc.steps.length > 0) {
      lines.push('   测试步骤：')
      tc.steps.forEach((step: any, stepIndex: number) => {
        lines.push(`      ${stepIndex + 1}. ${step.description || ''}`)
        if (step.expected_result) {
          lines.push(`         预期结果：${step.expected_result}`)
        }
      })
    }
  })
  return lines.join('\n')
}

// 格式化流式测试用例内容（解析JSON并美化显示）
const formatStreamingTestcaseContent = (content: string): string => {
  if (!content) return ''

  // 尝试提取并格式化 JSON
  try {
    // 提取 markdown 中的 json 代码块
    const jsonMatch = content.match(/```json\n?([\s\S]*?)\n?```/)
    if (jsonMatch) {
      const jsonStr = jsonMatch[1]
      const data = JSON.parse(jsonStr)

      // 如果是数组格式的测试用例
      if (Array.isArray(data)) {
        const lines: string[] = []
        data.forEach((tc: any, index: number) => {
          if (index > 0) lines.push('')
          lines.push(`【${index + 1}】${tc.title || '未命名'}`)
          if (tc.desc || tc.description) lines.push(`   描述：${tc.desc || tc.description}`)
          if (tc.preconditions) lines.push(`   前置条件：${tc.preconditions}`)
          if (tc.test_data) lines.push(`   测试数据：${tc.test_data}`)
          if (tc.priority) lines.push(`   优先级：${tc.priority}`)

          // 处理步骤
          const steps = tc.steps || tc.test_steps || []
          if (Array.isArray(steps) && steps.length > 0) {
            lines.push('   测试步骤：')
            steps.forEach((step: any, stepIndex: number) => {
              lines.push(`      ${stepIndex + 1}. ${step.description || step.action || ''}`)
              if (step.expected_result) {
                lines.push(`         预期：${step.expected_result}`)
              }
            })
          }
        })
        return lines.join('\n')
      }
    }

    // 尝试直接解析整个内容
    const trimmed = content.trim()
    if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
      const parsed = JSON.parse(trimmed)
      if (Array.isArray(parsed)) {
        return formatTestCases(parsed)
      }
    }
  } catch (e) {
    // 解析失败，返回原始内容
  }

  // 如果解析失败，返回美化后的原始内容
  return content
    .replace(/```json\n?/g, '')
    .replace(/```\n?/g, '')
    .replace(/\\n/g, '\n')
    .replace(/,/g, ',\n')
}

// 复制内容到剪贴板
const copyToClipboard = async (content: string, label: string = '内容') => {
  try {
    await navigator.clipboard.writeText(content)
    ElMessage.success(`${label}已复制到剪贴板`)
  } catch {
    ElMessage.error('复制失败，请手动选择内容复制')
  }
}

// 复制功能点生成记录
const copyRequirementStream = () => {
  copyToClipboard(streamingAnalysisContent.value, 'AI分析过程')
}

// 复制需求评审结果
const copyRequirementReview = () => {
  const content = `需求评审结论：${statsInfo.value.requirementReviewConclusion || '无'}\n\n功能点列表：\n${formatFunctionPoints(streamedFunctionPoints.value)}`
  copyToClipboard(content, '需求评审结果')
}

// 复制测试用例生成记录
const copyTestcaseStream = () => {
  copyToClipboard(streamingGenerateContent.value, '用例生成过程')
}

// 复制测试用例评审结果
const copyTestcaseReview = () => {
  copyToClipboard(formatTestCases(streamedTestCases.value), '测试用例评审结果')
}

const getProjectName = (projectId: number | null): string => {
  if (!projectId) return '未关联项目'
  const project = projectStore.projects.find(p => p.id === projectId)
  return project?.name || '-'
}

// 格式化时间戳为 HH:mm:ss 格式（显示时间）
const formatTime = (timestamp: string): string => {
  if (!timestamp) return ''
  try {
    const date = new Date(timestamp)
    const hours = date.getHours().toString().padStart(2, '0')
    const minutes = date.getMinutes().toString().padStart(2, '0')
    const seconds = date.getSeconds().toString().padStart(2, '0')
    return `${hours}:${minutes}:${seconds}`
  } catch {
    return timestamp
  }
}

// 格式化时间戳为完整格式（含日期）
const formatDateTime = (timestamp: string): string => {
  if (!timestamp) return ''
  try {
    const date = new Date(timestamp)
    const month = (date.getMonth() + 1).toString().padStart(2, '0')
    const day = date.getDate().toString().padStart(2, '0')
    const hours = date.getHours().toString().padStart(2, '0')
    const minutes = date.getMinutes().toString().padStart(2, '0')
    const seconds = date.getSeconds().toString().padStart(2, '0')
    return `${month}-${day} ${hours}:${minutes}:${seconds}`
  } catch {
    return timestamp
  }
}
</script>

<template>
  <div class="generate-page p-6">
    <!-- 页面标题 -->
    <div class="mb-6">
      <h1 class="text-2xl font-semibold text-text-primary">AI用例生成</h1>
      <p class="text-text-secondary text-sm mt-1">
        输入需求或上传文档，AI自动提取功能点并生成测试用例
      </p>
    </div>

    <div class="flex flex-col">
      <!-- 左侧：输入区域 -->
      <div v-if="showInputPanel" class="space-y-4">
        <!-- 输入方式切换 + 模型配置入口 -->
        <div class="card w-full">
          <div class="flex items-center justify-between border-b border-gray-200 mb-4 pb-3">
            <!-- Tab 切换 -->
            <div class="flex gap-2">
              <button
                @click="inputMode = 'document'"
                :class="[
                  'pb-2 border-b-2 transition-colors flex items-center gap-2',
                  inputMode === 'document'
                    ? 'border-primary text-primary font-medium'
                    : 'border-transparent text-text-secondary hover:text-text-primary'
                ]"
              >
                <FileText class="w-4 h-4" />
                文档上传
              </button>
              <button
                @click="inputMode = 'feishu'"
                :class="[
                  'pb-2 border-b-2 transition-colors flex items-center gap-2',
                  inputMode === 'feishu'
                    ? 'border-primary text-primary font-medium'
                    : 'border-transparent text-text-secondary hover:text-text-primary'
                ]"
              >
                <Link2 class="w-4 h-4" />
                飞书文档
              </button>
              <button
                @click="inputMode = 'manual'"
                :class="[
                  'pb-2 border-b-2 transition-colors flex items-center gap-2',
                  inputMode === 'manual'
                    ? 'border-primary text-primary font-medium'
                    : 'border-transparent text-text-secondary hover:text-text-primary'
                ]"
              >
                <Zap class="w-4 h-4" />
                手动输入
              </button>
            </div>
          </div>

          <!-- 手动输入模式 -->
          <div v-if="inputMode === 'manual'" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-text-primary mb-1">
                需求名称 <span class="text-red-500">*</span>
              </label>
              <input
                v-model="requirementName"
                type="text"
                class="input-field"
                placeholder="例如：用户登录模块需求"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-text-primary mb-1">
                需求描述 <span class="text-red-500">*</span>
              </label>
              <textarea
                v-model="requirementDescription"
                class="input-field min-h-[200px] resize-y"
                placeholder="请详细描述需求，例如：&#10;- 用户登录功能&#10;- 支持手机号和邮箱登录&#10;- 登录失败三次后需要验证码验证..."
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-text-primary mb-1">
                选择项目 <span class="text-red-500">*</span>
              </label>
              <select v-model="selectedProjectId" class="input-field">
                <option :value="null">请选择项目（必填）</option>
                <option v-for="project in projects" :key="project.id" :value="project.id">
                  {{ project.name }}
                </option>
              </select>
            </div>
          </div>

          <!-- 飞书文档模式 -->
          <div v-else-if="inputMode === 'feishu'" class="space-y-4">
            <!-- 配置提示 -->
            <div v-if="!isFeishuConfigured" class="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p class="text-yellow-700 text-sm">
                飞书功能未配置，请联系管理员设置 FEISHU_APP_ID 和 FEISHU_APP_SECRET
              </p>
            </div>

            <div>
              <label class="block text-sm font-medium text-text-primary mb-1">
                需求名称 <span class="text-red-500">*</span>
              </label>
              <input
                v-model="requirementName"
                type="text"
                class="input-field"
                placeholder="例如：用户登录模块需求"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-text-primary mb-1">
                飞书文档链接 <span class="text-red-500">*</span>
              </label>
              <input
                v-model="feishuDocUrl"
                type="text"
                class="input-field"
                placeholder="粘贴飞书文档链接，如：https://my.feishu.cn/wiki/xxx"
              />
              <p class="text-xs text-text-placeholder mt-1">
                支持飞书云文档和知识库文档
              </p>
            </div>

            <div>
              <label class="block text-sm font-medium text-text-primary mb-1">
                选择项目 <span class="text-red-500">*</span>
              </label>
              <select v-model="selectedProjectId" class="input-field">
                <option :value="null">请选择项目（必填）</option>
                <option v-for="project in projects" :key="project.id" :value="project.id">
                  {{ project.name }}
                </option>
              </select>
            </div>
          </div>

          <!-- 文档上传模式 -->
          <div v-else class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-text-primary mb-1">
                需求名称 <span class="text-red-500">*</span>
              </label>
              <input
                v-model="requirementName"
                type="text"
                class="input-field"
                placeholder="例如：用户登录模块需求"
              />
            </div>

            <div
              class="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-primary transition-colors cursor-pointer"
              @click="$refs.fileInput?.click()"
            >
              <input
                ref="fileInput"
                type="file"
                accept=".txt,.md,.pdf,.docx"
                multiple
                class="hidden"
                @change="handleFileUpload"
              />

              <div v-if="uploadedFiles.length === 0" class="space-y-3">
                <Upload class="w-12 h-12 mx-auto text-gray-400" />
                <p class="text-text-secondary font-medium">点击或拖拽上传需求文档</p>
                <p class="text-sm text-text-placeholder">支持 txt、md、pdf、docx 格式，可多选</p>
              </div>

              <div v-else class="text-left">
                <div class="flex items-center justify-between mb-3">
                  <span class="text-sm font-medium text-text-primary">
                    已选择 {{ uploadedFiles.length }} 个文件
                  </span>
                  <button
                    @click.stop="clearAllFiles"
                    class="text-xs text-red-500 hover:text-red-600 transition-colors"
                  >
                    清空全部
                  </button>
                </div>
                <div class="space-y-2 max-h-[200px] overflow-y-auto">
                  <div
                    v-for="(file, index) in uploadedFiles"
                    :key="index"
                    class="flex items-center justify-between bg-background-secondary rounded px-3 py-2"
                  >
                    <div class="flex items-center gap-2 flex-1 min-w-0">
                      <FileText class="w-4 h-4 text-primary flex-shrink-0" />
                      <span class="text-sm text-text-primary truncate">{{ file.name }}</span>
                    </div>
                    <button
                      @click.stop="removeFile(index)"
                      class="ml-2 p-1 text-gray-400 hover:text-red-500 transition-colors flex-shrink-0"
                    >
                      <XCircle class="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <div>
              <label class="block text-sm font-medium text-text-primary mb-1">
                选择项目 <span class="text-red-500">*</span>
              </label>
              <select v-model="selectedProjectId" class="input-field">
                <option :value="null">请选择项目（必填）</option>
                <option v-for="project in projects" :key="project.id" :value="project.id">
                  {{ project.name }}
                </option>
              </select>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="flex gap-3 mt-6">
            <button
              @click="startGeneration"
              :disabled="isGenerating"
              class="btn-primary flex items-center gap-2 flex-1"
            >
              <Loader v-if="isGenerating" class="w-4 h-4 animate-spin" />
              <Send v-else class="w-4 h-4" />
              {{ isGenerating ? '生成中...' : '生成测试用例' }}
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
      </div>

      <!-- 右侧：生成结果展示 -->
      <div class="space-y-4 mt-8">
        <!-- 展开输入面板按钮 -->
        <button
          v-if="!showInputPanel"
          @click="showInputPanel = true"
          class="w-full flex items-center justify-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors text-sm text-gray-600"
        >
          <Zap class="w-4 h-4" />
          展开输入面板
        </button>
        <!-- 7步骤进度指示器 -->
        <div v-if="isGenerating || generationComplete" class="card w-full py-3">
          <!-- 标题行 -->
          <div class="flex items-center justify-between mb-3 px-1">
            <div class="flex items-center gap-2">
              <Loader v-if="isGenerating" class="w-4 h-4 text-primary animate-spin" />
              <CheckCircle v-else class="w-4 h-4 text-green-500" />
              <h3 class="text-sm font-medium text-text-primary">
                {{ generationComplete ? '生成完成' : 'AI正在工作中...' }}
              </h3>
            </div>
            <span v-if="activeAgent && isGenerating" class="text-xs text-primary">
              {{ getAgentConfig(activeAgent).stepName }}
            </span>
          </div>
          
          <!-- 步骤指示器 -->
          <div class="flex items-center gap-3 px-1">
            <!-- 阶段1：需求分析（3步） -->
            <span class="text-xs text-gray-500 whitespace-nowrap">需求分析</span>
            <div class="flex gap-1.5 flex-1">
              <div 
                v-for="step in [1, 2, 3]" 
                :key="step"
                :class="[
                  'flex-1 h-5 rounded text-center text-xs flex items-center justify-center font-medium transition-all',
                  getStepStatus(1, step) === 'completed' ? 'bg-green-500 text-white' :
                  getStepStatus(1, step) === 'active' ? 'bg-blue-500 text-white animate-pulse' :
                  'bg-gray-100 text-gray-400'
                ]"
              >
                <span v-if="getStepStatus(1, step) === 'completed'">✓</span>
                <span v-else>{{ ['摘要', '分析', '输出'][step - 1] }}</span>
              </div>
            </div>
            <!-- 分隔 -->
            <div class="w-px h-5 bg-gray-300"></div>
            <!-- 阶段2：用例生成（4步） -->
            <span class="text-xs text-gray-500 whitespace-nowrap">用例生成</span>
            <div class="flex gap-1.5 flex-1">
              <div 
                v-for="(step, idx) in [4, 5, 6, 7]" 
                :key="step"
                :class="[
                  'flex-1 h-5 rounded text-center text-xs flex items-center justify-center font-medium transition-all',
                  getStepStatus(2, idx + 1) === 'completed' ? 'bg-green-500 text-white' :
                  getStepStatus(2, idx + 1) === 'active' ? 'bg-orange-500 text-white animate-pulse' :
                  'bg-gray-100 text-gray-400'
                ]"
              >
                <span v-if="getStepStatus(2, idx + 1) === 'completed'">✓</span>
                <span v-else>{{ ['生成', '评审', '定稿', '保存'][idx] }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 统一日志区域 -->
        <div v-if="logs.length > 0" class="card w-full">
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center gap-2">
              <MessageSquare class="w-4 h-4 text-text-secondary" />
              <h3 class="text-sm font-medium text-text-primary">实时日志</h3>
              <span class="text-xs text-text-secondary">{{ filteredLogs.length }} 条</span>
            </div>
            <button
              @click="copyLogs"
              class="flex items-center gap-1 px-2 py-1 text-xs text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded transition-colors"
            >
              <Copy class="w-3.5 h-3.5" />
              复制日志
            </button>
          </div>
          
          <!-- 日志列表 -->
          <div
            ref="logContainerRef"
            class="bg-gray-50 rounded-lg p-3 max-h-[500px] overflow-y-auto space-y-2"
          >
            <div
              v-for="log in filteredLogs.filter(l => {
                const content = l.content || ''
                // 过滤掉纯进度/Agent标签的内容行
                if (content.includes('[PROGRESS]')) return false
                if (content.includes('[AGENT]')) return false
                return content.trim().length > 0
              })"
              :key="log.id"
              :class="[
                'border-l-4 rounded-r p-3 animate-fadeIn',
                colorClasses[log.color]?.border || 'border-l-gray-400',
                colorClasses[log.color]?.bg || 'bg-white'
              ]"
            >
              <div class="flex items-center gap-2 mb-1">
                <component 
                  :is="log.icon" 
                  :class="[
                    'w-3.5 h-3.5',
                    colorClasses[log.color]?.text || 'text-gray-600'
                  ]"
                />
                <span 
                  :class="[
                    'text-xs font-medium',
                    colorClasses[log.color]?.text || 'text-gray-600'
                  ]"
                >
                  {{ log.agent }}
                </span>
                <span class="text-xs text-gray-400">
                  {{ log.timestamp.toLocaleTimeString() }}
                </span>
                <span v-if="log.type === 'thinking'" class="ml-auto">
                  <span class="animate-blink text-xs text-primary">▌</span>
                </span>
              </div>
              
              <!-- 评审结论卡片（豆包风格已注释，不再显示卡片） -->
              <!-- 
              <div 
                v-if="parseMessageContent(log.content).type === 'review_json'"
                class="mt-2 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg p-3 border border-indigo-200"
              >
                ... 卡片内容 ...
              </div>
              -->

              <!-- Markdown内容（豆包风格） -->
              <div 
                v-if="log.content && !log.content.includes('```') && (log.agent === 'AI分析' || log.agent === '需求获取')"
                class="text-xs text-gray-700 prose prose-xs max-w-none"
                v-html="renderMarkdown(log.content)"
              ></div>
              
              <!-- 普通文本内容（豆包风格） -->
              <pre
                v-else-if="log.content"
                class="text-xs text-gray-700 whitespace-pre-wrap break-words font-mono"
              >{{ log.content.trim() }}</pre>
            </div>
          </div>
        </div>

        <!-- 最终完成卡片 -->
        <div v-if="generationComplete" class="card w-full bg-gradient-to-br from-green-50 to-emerald-50 border border-green-200 shadow-sm">
          <div class="flex items-center gap-3 mb-4">
            <div class="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
              <CheckCircle class="w-5 h-5 text-green-600" />
            </div>
            <div>
              <h4 class="text-green-800 font-semibold">生成完成</h4>
              <p class="text-green-600 text-xs">AI用例生成全流程已完成</p>
            </div>
          </div>
          
          <!-- 核心统计 - 与任务记录同源 -->
          <div class="grid grid-cols-4 gap-2 mb-4">
            <div class="bg-white/70 rounded-lg p-2.5 text-center">
              <div class="text-xl font-bold text-blue-600">{{ statsInfo.count || statsInfo.testcaseCount || 0 }}</div>
              <div class="text-[10px] text-gray-500">测试用例</div>
            </div>
            <div class="bg-white/70 rounded-lg p-2.5 text-center">
              <div class="text-xl font-bold text-green-600">{{ statsInfo.functionCount || statsInfo.function_ids?.length || 0 }}</div>
              <div class="text-[10px] text-gray-500">功能点</div>
            </div>
            <div class="bg-white/70 rounded-lg p-2.5 text-center">
              <div class="text-xl font-bold text-purple-600">{{ statsInfo.chunkCount || 0 }}</div>
              <div class="text-[10px] text-gray-500">文档分块</div>
            </div>
            <div class="bg-white/70 rounded-lg p-2.5 text-center">
              <div class="text-xl font-bold text-orange-600">{{ formatDuration(statsInfo.stageTimings?.total) || statsInfo.totalTime || '-' }}</div>
              <div class="text-[10px] text-gray-500">总耗时</div>
            </div>
          </div>
          
          <!-- AI模型信息 -->
          <div v-if="statsInfo.modelInfo" class="bg-white/50 rounded-lg p-2.5 mb-4">
            <div class="flex items-center gap-4 text-xs">
              <div v-if="statsInfo.modelInfo.requirement_analyze_model">
                <span class="text-gray-400">需求分析：</span>
                <span class="text-green-600 font-medium">{{ statsInfo.modelInfo.requirement_analyze_model }}</span>
              </div>
              <div v-if="statsInfo.modelInfo.testcase_generate_model">
                <span class="text-gray-400">用例生成：</span>
                <span class="text-blue-600 font-medium">{{ statsInfo.modelInfo.testcase_generate_model }}</span>
              </div>
              <div v-if="statsInfo.modelInfo.testcase_review_model">
                <span class="text-gray-400">用例评审：</span>
                <span class="text-purple-600 font-medium">{{ statsInfo.modelInfo.testcase_review_model }}</span>
              </div>
            </div>
          </div>
          
          <!-- 耗时明细 -->
          <div v-if="statsInfo.stageTimings" class="flex gap-4 text-xs text-gray-500 mb-4">
            <span v-if="statsInfo.stageTimings.requirement_analysis">
              需求分析：{{ formatDuration(statsInfo.stageTimings.requirement_analysis) }}
            </span>
            <span v-if="statsInfo.stageTimings.testcase_generation">
              用例生成：{{ formatDuration(statsInfo.stageTimings.testcase_generation) }}
            </span>
          </div>
          
          <!-- 操作按钮 -->
          <div class="flex gap-2">
            <button
              @click="goToFunctionPoints"
              class="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition text-xs"
            >
              <Eye class="w-3.5 h-3.5 text-gray-500" />
              <span class="text-gray-600">功能点</span>
            </button>
            <button
              @click="goToTestCases"
              class="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition text-xs"
            >
              <Eye class="w-3.5 h-3.5" />
              <span>测试用例</span>
            </button>
            <button
              @click="exportTestCasesToExcel"
              class="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition text-xs"
            >
              <Download class="w-3.5 h-3.5" />
              <span>导出</span>
            </button>
            <button
              @click="goToTaskRecords"
              class="flex items-center justify-center gap-1.5 px-3 py-2 bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200 transition text-xs"
            >
              <BarChart3 class="w-3.5 h-3.5" />
              <span>记录</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.generate-page {
  width: 100%;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fadeIn {
  animation: fadeIn 0.3s ease-out forwards;
}

.animate-blink {
  animation: blink 1s step-end infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
