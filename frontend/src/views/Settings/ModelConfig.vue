<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { Database, Sparkles } from 'lucide-vue-next'
import { ElMessage, ElDialog, ElForm, ElFormItem, ElInput, ElButton, ElMessageBox, ElSwitch, ElSelect, ElOption, ElTag, ElInputNumber, ElTable, ElTableColumn, ElRow, ElCol, ElAlert } from 'element-plus'
import { modelConfigApi, type LLMModel, type EmbeddingModel, type ModelStatus } from '@/api/modelConfig'

// 状态
const loading = ref(true)
const modelStatus = ref<ModelStatus | null>(null)

// LLM 模型相关
const llmModels = ref<LLMModel[]>([])
const llmDefaults = ref<Array<{ purpose: string; model_name: string }>>([])
const showLLMDialog = ref(false)
const editingLLMId = ref<number | null>(null)
const llmForm = ref({
  name: '',
  display_name: '',
  provider: 'deepseek',
  base_url: '',
  api_key: '',
  default_model: '',
  description: '',
  enabled: true,
})
const llmLoading = ref(false)
const testingLLMId = ref<number | null>(null)

// 嵌入模型相关
const embeddingModels = ref<EmbeddingModel[]>([])
const showEmbeddingDialog = ref(false)
const editingEmbeddingId = ref<number | null>(null)
const embeddingForm = ref({
  name: '',
  display_name: '',
  provider: 'dashscope',
  api_base: '',
  api_key: '',
  model_name: '',
  dimension: 1024,
  description: '',
  enabled: true,
})
const embeddingLoading = ref(false)
const testingEmbeddingId = ref<number | null>(null)
const testingDialogLLM = ref(false)
const dialogTestResult = ref<{ success: boolean; message: string } | null>(null)

// 提供商选项
const llmProviders = [
  { value: 'deepseek', label: 'DeepSeek', baseUrl: 'https://api.deepseek.com/v1', models: ['deepseek-chat', 'deepseek-reasoner'] },
  { value: 'moonshot', label: 'Moonshot (Kimi)', baseUrl: 'https://api.moonshot.cn/v1', models: ['moonshot-v1-8k', 'moonshot-v1-32k', 'moonshot-v1-128k'] },
  { value: 'qwen', label: '通义千问', baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1', models: ['qwen-turbo', 'qwen-plus', 'qwen-max'] },
  { value: 'openai', label: 'OpenAI', baseUrl: 'https://api.openai.com/v1', models: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo'] },
  { value: 'anthropic', label: 'Anthropic', baseUrl: 'https://api.anthropic.com/v1', models: ['claude-3-5-sonnet-20241022', 'claude-3-opus-20240229'] },
  { value: 'ollama', label: 'Ollama (本地)', baseUrl: 'http://localhost:11434/v1', models: ['llama3.2', 'qwen2.5', 'mistral', 'phi3'] },
  { value: 'custom', label: '自定义', baseUrl: '', models: [] },
]

const embeddingProviders = [
  { value: 'dashscope', label: '阿里云 DashScope', baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1', models: ['text-embedding-v3', 'text-embedding-v2'], dimensions: [1024, 1536] },
  { value: 'openai', label: 'OpenAI', baseUrl: 'https://api.openai.com/v1', models: ['text-embedding-3-small', 'text-embedding-3-large'], dimensions: [1536, 3072] },
  { value: 'ollama', label: 'Ollama (本地)', baseUrl: 'http://localhost:11434', models: ['nomic-embed-text', 'mxbai-embed-large'], dimensions: [768, 1024] },
]

// 用途选项
const purposeOptions = [
  { value: 'requirement_analyze', label: '需求分析模型', type: 'llm' },
  { value: 'testcase_generate', label: '用例生成模型', type: 'llm' },
  { value: 'testcase_review', label: '用例评审模型', type: 'llm' },
]

// 获取当前选中的模型列表
const enabledLLMModels = computed(() => llmModels.value.filter(m => m.enabled))
const enabledEmbeddingModels = computed(() => embeddingModels.value.filter(m => m.enabled))

// 加载模型状态
const loadModelStatus = async () => {
  try {
    modelStatus.value = await modelConfigApi.getModelStatus()
  } catch (error) {
    console.error('加载模型状态失败:', error)
  }
}

// 加载 LLM 模型列表
const loadLLMModels = async () => {
  try {
    llmModels.value = await modelConfigApi.getLLMModels()
    llmDefaults.value = await modelConfigApi.getLLMModelDefaults()
  } catch (error) {
    console.error('加载LLM模型失败:', error)
  }
}

// 加载嵌入模型列表
const loadEmbeddingModels = async () => {
  try {
    embeddingModels.value = await modelConfigApi.getEmbeddingModels()
  } catch (error) {
    console.error('加载嵌入模型失败:', error)
  }
}

// 初始化加载
const loadData = async () => {
  loading.value = true
  try {
    await Promise.all([
      loadModelStatus(),
      loadLLMModels(),
      loadEmbeddingModels(),
    ])
  } finally {
    loading.value = false
  }
}

// 获取指定用途的默认模型
const getDefaultForPurpose = (purpose: string) => {
  const defaultModel = llmDefaults.value.find(d => d.purpose === purpose)
  if (!defaultModel) return null
  return llmModels.value.find(m => m.name === defaultModel.model_name)
}

// 获取嵌入模型默认配置
const getDefaultEmbeddingForPurpose = () => {
  const defaultModel = llmDefaults.value.find(d => d.purpose === 'embedding')
  if (!defaultModel) return null
  return embeddingModels.value.find(m => m.name === defaultModel.model_name)
}

// 设置嵌入模型默认
const setDefaultEmbedding = async (modelName: string) => {
  try {
    await modelConfigApi.setDefaultModel('embedding', modelName)
    ElMessage.success('设置成功')
    await loadLLMModels()
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '设置失败')
  }
}

// 判断模型是否为某用途的默认
const isDefaultForPurpose = (modelName: string, purpose: string) => {
  const defaultModel = llmDefaults.value.find(d => d.purpose === purpose)
  return defaultModel?.model_name === modelName
}

// 判断嵌入模型是否为默认
const isDefaultEmbedding = (modelName: string) => {
  const defaultModel = llmDefaults.value.find(d => d.purpose === 'embedding')
  return defaultModel?.model_name === modelName
}

// 对话框内测试 LLM 连接
const testLLMInDialog = async () => {
  dialogTestResult.value = null
  testingDialogLLM.value = true
  try {
    const res = await modelConfigApi.testLLMConnection({
      base_url: llmForm.value.base_url,
      api_key: llmForm.value.api_key || '',
      model: llmForm.value.default_model,
      provider: llmForm.value.provider,
    })
    dialogTestResult.value = {
      success: res.success,
      message: res.success ? '连接成功！' : `连接失败: ${res.message}`
    }
  } catch (error: any) {
    dialogTestResult.value = {
      success: false,
      message: `测试失败: ${error?.response?.data?.detail || error.message || '未知错误'}`
    }
  } finally {
    testingDialogLLM.value = false
  }
}

// 打开 LLM 模型对话框
const openLLMDialog = (model?: LLMModel) => {
  dialogTestResult.value = null
  if (model) {
    editingLLMId.value = model.id
    llmForm.value = {
      display_name: model.display_name,
      provider: model.provider,
      base_url: model.base_url,
      api_key: '',
      default_model: model.default_model,
      description: model.description || '',
      enabled: model.enabled,
    }
  } else {
    editingLLMId.value = null
    llmForm.value = {
      display_name: '',
      provider: 'deepseek',
      base_url: 'https://api.deepseek.com/v1',
      api_key: '',
      default_model: '',
      description: '',
      enabled: true,
    }
  }
  showLLMDialog.value = true
}

// 提交 LLM 模型
const submitLLM = async () => {
  if (!llmForm.value.display_name || !llmForm.value.default_model || !llmForm.value.base_url) {
    ElMessage.warning('请填写所有必填项')
    return
  }
  if (llmForm.value.provider !== 'ollama' && !llmForm.value.api_key && !editingLLMId.value) {
    ElMessage.warning('请输入 API Key')
    return
  }
  try {
    llmLoading.value = true
    const name = llmForm.value.default_model.toLowerCase().replace(/\s+/g, '-')
    const data: any = {
      name: name,
      display_name: llmForm.value.display_name,
      provider: llmForm.value.provider,
      base_url: llmForm.value.base_url,
      default_model: llmForm.value.default_model,
      description: llmForm.value.description,
      enabled: llmForm.value.enabled,
    }
    if (llmForm.value.api_key) {
      data.api_key = llmForm.value.api_key
    }
    if (editingLLMId.value) {
      await modelConfigApi.updateLLMModel(editingLLMId.value, data)
      ElMessage.success('更新成功')
    } else {
      await modelConfigApi.createLLMModel(data)
      ElMessage.success('添加成功')
    }
    showLLMDialog.value = false
    await loadLLMModels()
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '操作失败')
  } finally {
    llmLoading.value = false
  }
}

// 删除 LLM 模型
const deleteLLM = async (model: LLMModel) => {
  try {
    await ElMessageBox.confirm(`确定要删除模型 "${model.display_name}" 吗？`, '删除确认', { type: 'warning' })
    await modelConfigApi.deleteLLMModel(model.id)
    ElMessage.success('删除成功')
    await loadLLMModels()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error?.response?.data?.detail || '删除失败')
    }
  }
}

// 测试 LLM 连接
const testLLM = async (model: LLMModel) => {
  testingLLMId.value = model.id
  try {
    const res = await modelConfigApi.testLLMModelById(model.id)
    if (res.success) {
      ElMessage.success('连接成功！')
    } else {
      ElMessage.error(`连接失败: ${res.message}`)
    }
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '测试失败')
  } finally {
    testingLLMId.value = null
  }
}

// 设置默认模型
const setDefaultModel = async (purpose: string, modelName: string) => {
  try {
    await modelConfigApi.setDefaultModel(purpose, modelName)
    ElMessage.success('设置成功')
    await loadLLMModels()
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '设置失败')
  }
}

// 打开嵌入模型对话框
const openEmbeddingDialog = (model?: EmbeddingModel) => {
  if (model) {
    editingEmbeddingId.value = model.id
    embeddingForm.value = {
      display_name: model.display_name,
      provider: model.provider,
      api_base: model.api_base,
      api_key: '',
      model_name: model.model_name,
      dimension: model.dimension,
      description: model.description || '',
      enabled: model.enabled,
    }
  } else {
    editingEmbeddingId.value = null
    embeddingForm.value = {
      display_name: '',
      provider: 'dashscope',
      api_base: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
      api_key: '',
      model_name: '',
      dimension: 1024,
      description: '',
      enabled: true,
    }
  }
  showEmbeddingDialog.value = true
}

// 提交嵌入模型
const submitEmbedding = async () => {
  if (!embeddingForm.value.display_name || !embeddingForm.value.model_name || !embeddingForm.value.api_base) {
    ElMessage.warning('请填写所有必填项')
    return
  }
  if (embeddingForm.value.provider !== 'ollama' && !embeddingForm.value.api_key && !editingEmbeddingId.value) {
    ElMessage.warning('请输入 API Key')
    return
  }
  try {
    embeddingLoading.value = true
    const name = embeddingForm.value.model_name.toLowerCase().replace(/\s+/g, '-')
    const data: any = {
      name: name,
      display_name: embeddingForm.value.display_name,
      provider: embeddingForm.value.provider,
      api_base: embeddingForm.value.api_base,
      model_name: embeddingForm.value.model_name,
      dimension: embeddingForm.value.dimension,
      description: embeddingForm.value.description,
      enabled: embeddingForm.value.enabled,
    }
    if (embeddingForm.value.api_key) {
      data.api_key = embeddingForm.value.api_key
    }
    if (editingEmbeddingId.value) {
      await modelConfigApi.updateEmbeddingModel(editingEmbeddingId.value, data)
      ElMessage.success('更新成功')
    } else {
      await modelConfigApi.createEmbeddingModel(data)
      ElMessage.success('添加成功')
    }
    showEmbeddingDialog.value = false
    await loadEmbeddingModels()
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '操作失败')
  } finally {
    embeddingLoading.value = false
  }
}

// 删除嵌入模型
const deleteEmbedding = async (model: EmbeddingModel) => {
  try {
    await ElMessageBox.confirm(`确定要删除嵌入模型 "${model.display_name}" 吗？`, '删除确认', { type: 'warning' })
    await modelConfigApi.deleteEmbeddingModel(model.id)
    ElMessage.success('删除成功')
    await loadEmbeddingModels()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error?.response?.data?.detail || '删除失败')
    }
  }
}

// 测试嵌入连接
const testEmbedding = async (model: EmbeddingModel) => {
  testingEmbeddingId.value = model.id
  try {
    const res = await modelConfigApi.testEmbeddingConnection({
      api_base: model.api_base,
      api_key: model.api_key || '',
      model_name: model.model_name,
      provider: model.provider,
      dimension: model.dimension,
    })
    if (res.success) {
      ElMessage.success('连接成功！')
    } else {
      ElMessage.error(`连接失败: ${res.message}`)
    }
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '测试失败')
  } finally {
    testingEmbeddingId.value = null
  }
}

// 初始化默认配置
const initializeModels = async () => {
  try {
    const res = await modelConfigApi.initializeModels()
    if (res.success) {
      ElMessage.success('初始化成功')
      await loadData()
    } else {
      ElMessage.error(res.message || '初始化失败')
    }
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '初始化失败')
  }
}

// 选择提供商时自动填充
const onProviderChange = (type: 'llm' | 'embedding') => {
  if (type === 'llm') {
    const provider = llmProviders.find(p => p.value === llmForm.value.provider)
    if (provider) {
      llmForm.value.base_url = provider.baseUrl
    }
  } else {
    const provider = embeddingProviders.find(p => p.value === embeddingForm.value.provider)
    if (provider) {
      embeddingForm.value.api_base = provider.baseUrl
    }
  }
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="model-config p-6">
    <!-- 加载状态 -->
    <div v-if="loading" class="flex items-center justify-center h-64">
      <span class="text-text-secondary">加载模型配置...</span>
    </div>

    <template v-else>
      <!-- 页面标题 -->
      <div class="flex items-center justify-between mb-5">
        <h1 class="text-lg font-semibold text-text-primary">模型配置</h1>
        <ElButton type="primary" size="small" @click="initializeModels">
          <Sparkles class="w-3.5 h-3.5 mr-1" />
          初始化默认
        </ElButton>
      </div>

      <!-- 说明提示 -->
      <ElAlert
        title="AI 模型配置"
        description="添加你的 LLM 模型和嵌入模型来启用 AI 测试功能。支持 DeepSeek、通义千问、Moonshot、OpenAI 等主流大模型。"
        type="info"
        :closable="false"
        show-icon
        class="mb-5"
      />

      <ElRow :gutter="20" class="model-sections">
        <!-- ===================== LLM 模型 ===================== -->
        <ElCol :span="24">
          <ElCard class="model-card" shadow="never">
            <template #header>
              <div class="card-header">
                <div class="card-header-left">
                  <div class="section-icon llm-icon">
                    <Database class="w-4 h-4" />
                  </div>
                  <div>
                    <span class="section-title">LLM 模型</span>
                    <span class="section-desc">配置用于需求分析、用例生成和评审的大语言模型</span>
                  </div>
                </div>
                <ElButton type="primary" size="small" @click="openLLMDialog()">
                  <span class="w-3.5 h-3.5 inline-flex items-center justify-center mr-1">+</span>
                  添加模型
                </ElButton>
              </div>
            </template>

            <!-- 用途映射区 -->
            <div class="purpose-area">
              <div class="purpose-grid">
                <div v-for="purpose in purposeOptions" :key="purpose.value" class="purpose-item">
                  <span class="purpose-label">{{ purpose.label }}</span>
                  <ElSelect
                    :model-value="getDefaultForPurpose(purpose.value)?.name || ''"
                    placeholder="选择模型"
                    size="default"
                    clearable
                    @change="(val: string) => val && setDefaultModel(purpose.value, val)"
                    class="w-full"
                  >
                    <ElOption
                      v-for="model in enabledLLMModels"
                      :key="model.name"
                      :label="model.display_name"
                      :value="model.name"
                    />
                  </ElSelect>
                </div>
              </div>
            </div>

            <!-- 模型列表 -->
            <div class="model-table-wrap">
              <ElTable
                :data="llmModels"
                stripe
                style="width: 100%"
                :header-cell-style="{ background: 'var(--el-fill-color-lighter)', color: 'var(--el-text-color-regular)', fontSize: '13px', fontWeight: '500' }"
                :cell-style="{ fontSize: '13px' }"
              >
                <ElTableColumn label="模型名称" min-width="180">
                  <template #default="{ row }">
                    <div class="flex items-center gap-2">
                      <span class="model-name-text">{{ row.display_name }}</span>
                      <ElTag v-if="isDefaultForPurpose(row.name, 'testcase_generate')" size="small" type="warning" effect="light" class="compact-tag">用例生成</ElTag>
                      <ElTag v-if="isDefaultForPurpose(row.name, 'requirement_analyze')" size="small" type="success" effect="light" class="compact-tag">需求分析</ElTag>
                      <ElTag v-if="isDefaultForPurpose(row.name, 'testcase_review')" size="small" type="info" effect="light" class="compact-tag">用例评审</ElTag>
                    </div>
                  </template>
                </ElTableColumn>

                <ElTableColumn label="提供商" width="120">
                  <template #default="{ row }">
                    <span class="meta-tag">{{ row.provider }}</span>
                  </template>
                </ElTableColumn>

                <ElTableColumn label="API 模型" min-width="160">
                  <template #default="{ row }">
                    <span class="meta-tag font-mono">{{ row.default_model }}</span>
                  </template>
                </ElTableColumn>

                <ElTableColumn label="状态" width="90" align="center">
                  <template #default="{ row }">
                    <ElTag size="small" :type="row.enabled ? 'success' : 'info'" effect="light">
                      {{ row.enabled ? '已启用' : '已禁用' }}
                    </ElTag>
                  </template>
                </ElTableColumn>

                <ElTableColumn label="操作" width="230" align="center">
                  <template #default="{ row }">
                    <div class="table-actions">
                      <ElButton
                        size="small"
                        :loading="testingLLMId === row.id"
                        @click="testLLM(row)"
                        title="测试连接"
                      >
                        {{ testingLLMId === row.id ? '测试中' : '测试' }}
                      </ElButton>
                      <ElButton size="small" @click="openLLMDialog(row)" title="编辑">编辑</ElButton>
                      <ElButton size="small" type="danger" plain @click="deleteLLM(row)" title="删除">删除</ElButton>
                    </div>
                  </template>
                </ElTableColumn>

                <template #empty>
                  <div class="empty-tip">
                    <span class="text-text-placeholder">还没有配置任何 LLM 模型</span>
                    <ElButton type="primary" size="small" class="ml-4" @click="openLLMDialog()">
                      添加第一个模型
                    </ElButton>
                  </div>
                </template>
              </ElTable>
            </div>
          </ElCard>
        </ElCol>

        <!-- ===================== 嵌入模型 ===================== -->
        <ElCol :span="24" class="mt-5">
          <ElCard class="model-card" shadow="never">
            <template #header>
              <div class="card-header">
                <div class="card-header-left">
                  <div class="section-icon embed-icon">
                    <Database class="w-4 h-4" />
                  </div>
                  <div>
                    <span class="section-title">嵌入模型 (RAG)</span>
                    <span class="section-desc">配置用于知识库向量化的嵌入模型</span>
                  </div>
                </div>
                <ElButton type="primary" size="small" @click="openEmbeddingDialog()">
                  <span class="w-3.5 h-3.5 inline-flex items-center justify-center mr-1">+</span>
                  添加模型
                </ElButton>
              </div>
            </template>

            <!-- 用途映射 -->
            <div class="purpose-area">
              <div class="purpose-grid single">
                <div class="purpose-item">
                  <span class="purpose-label">选择嵌入模型</span>
                  <ElSelect
                    :model-value="getDefaultEmbeddingForPurpose()?.name || ''"
                    placeholder="选择模型"
                    clearable
                    @change="(val: string) => val && setDefaultEmbedding(val)"
                    class="w-full"
                  >
                    <ElOption
                      v-for="model in enabledEmbeddingModels"
                      :key="model.name"
                      :label="model.display_name"
                      :value="model.name"
                    />
                  </ElSelect>
                </div>
              </div>
            </div>

            <!-- 模型列表 -->
            <div class="model-table-wrap">
              <ElTable
                :data="embeddingModels"
                stripe
                style="width: 100%"
                :header-cell-style="{ background: 'var(--el-fill-color-lighter)', color: 'var(--el-text-color-regular)', fontSize: '13px', fontWeight: '500' }"
                :cell-style="{ fontSize: '13px' }"
              >
                <ElTableColumn label="模型名称" min-width="180">
                  <template #default="{ row }">
                    <div class="flex items-center gap-2">
                      <span class="model-name-text">{{ row.display_name }}</span>
                      <ElTag v-if="isDefaultEmbedding(row.name)" size="small" type="warning" effect="light">默认</ElTag>
                    </div>
                  </template>
                </ElTableColumn>

                <ElTableColumn label="提供商" width="120">
                  <template #default="{ row }">
                    <span class="meta-tag">{{ row.provider }}</span>
                  </template>
                </ElTableColumn>

                <ElTableColumn label="API 模型" min-width="160">
                  <template #default="{ row }">
                    <span class="meta-tag font-mono">{{ row.model_name }}</span>
                  </template>
                </ElTableColumn>

                <ElTableColumn label="向量维度" width="100" align="center">
                  <template #default="{ row }">
                    <span class="meta-tag">{{ row.dimension }}维</span>
                  </template>
                </ElTableColumn>

                <ElTableColumn label="状态" width="90" align="center">
                  <template #default="{ row }">
                    <ElTag size="small" :type="row.enabled ? 'success' : 'info'" effect="light">
                      {{ row.enabled ? '已启用' : '已禁用' }}
                    </ElTag>
                  </template>
                </ElTableColumn>

                <ElTableColumn label="操作" width="230" align="center">
                  <template #default="{ row }">
                    <div class="table-actions">
                      <ElButton
                        size="small"
                        :loading="testingEmbeddingId === row.id"
                        @click="testEmbedding(row)"
                      >
                        {{ testingEmbeddingId === row.id ? '测试中' : '测试' }}
                      </ElButton>
                      <ElButton size="small" @click="openEmbeddingDialog(row)">编辑</ElButton>
                      <ElButton size="small" type="danger" plain @click="deleteEmbedding(row)">删除</ElButton>
                    </div>
                  </template>
                </ElTableColumn>

                <template #empty>
                  <div class="empty-tip">
                    <span class="text-text-placeholder">还没有配置任何嵌入模型</span>
                    <ElButton type="primary" size="small" class="ml-4" @click="openEmbeddingDialog()">
                      添加嵌入模型
                    </ElButton>
                  </div>
                </template>
              </ElTable>
            </div>
          </ElCard>
        </ElCol>
      </ElRow>
    </template>

    <!-- LLM 模型对话框 -->
    <ElDialog
      v-model="showLLMDialog"
      :title="editingLLMId ? '编辑 LLM 模型' : '添加 LLM 模型'"
      width="520px"
      :close-on-click-modal="false"
    >
      <ElForm :model="llmForm" label-position="top">
        <ElFormItem label="显示名称" required>
          <ElInput v-model="llmForm.display_name" placeholder="如: DeepSeek Chat" />
        </ElFormItem>

        <ElFormItem label="API 模型名称" required>
          <ElInput v-model="llmForm.default_model" placeholder="如: deepseek-chat" />
        </ElFormItem>

        <ElFormItem label="提供商" required>
          <ElSelect v-model="llmForm.provider" @change="onProviderChange('llm')" class="w-full">
            <ElOption v-for="p in llmProviders" :key="p.value" :label="p.label" :value="p.value" />
          </ElSelect>
        </ElFormItem>

        <ElFormItem label="API 地址" required>
          <ElInput v-model="llmForm.base_url" placeholder="如: https://api.deepseek.com/v1" />
        </ElFormItem>

        <ElFormItem :label="editingLLMId ? 'API Key（留空保持不变）' : 'API Key'" :required="!editingLLMId && llmForm.provider !== 'ollama'">
          <ElInput v-model="llmForm.api_key" type="password" show-password placeholder="请输入 API Key" />
        </ElFormItem>

        <ElFormItem label="描述">
          <ElInput v-model="llmForm.description" type="textarea" :rows="2" placeholder="可选描述" />
        </ElFormItem>

        <ElFormItem label="启用状态">
          <ElSwitch v-model="llmForm.enabled" />
        </ElFormItem>

        <div v-if="dialogTestResult" class="mt-3">
          <ElAlert
            :title="dialogTestResult.message"
            :type="dialogTestResult.success ? 'success' : 'error'"
            :closable="false"
            show-icon
          />
        </div>
      </ElForm>

      <template #footer>
        <ElButton @click="testLLMInDialog" :loading="testingDialogLLM" :disabled="!llmForm.base_url || !llmForm.default_model">
          测试连接
        </ElButton>
        <ElButton @click="showLLMDialog = false">取消</ElButton>
        <ElButton type="primary" @click="submitLLM" :loading="llmLoading">确定</ElButton>
      </template>
    </ElDialog>

    <!-- 嵌入模型对话框 -->
    <ElDialog
      v-model="showEmbeddingDialog"
      :title="editingEmbeddingId ? '编辑嵌入模型' : '添加嵌入模型'"
      width="520px"
      :close-on-click-modal="false"
    >
      <ElForm :model="embeddingForm" label-position="top">
        <ElFormItem label="显示名称" required>
          <ElInput v-model="embeddingForm.display_name" placeholder="如: Qwen Embedding V3" />
        </ElFormItem>

        <ElFormItem label="API 模型名称" required>
          <ElInput v-model="embeddingForm.model_name" placeholder="如: text-embedding-v3" />
        </ElFormItem>

        <ElFormItem label="提供商" required>
          <ElSelect v-model="embeddingForm.provider" @change="onProviderChange('embedding')" class="w-full">
            <ElOption v-for="p in embeddingProviders" :key="p.value" :label="p.label" :value="p.value" />
          </ElSelect>
        </ElFormItem>

        <ElFormItem label="API 地址" required>
          <ElInput v-model="embeddingForm.api_base" placeholder="如: https://dashscope.aliyuncs.com/compatible-mode/v1" />
        </ElFormItem>

        <ElFormItem :label="editingEmbeddingId ? 'API Key（留空保持不变）' : 'API Key'" :required="!editingEmbeddingId && embeddingForm.provider !== 'ollama'">
          <ElInput v-model="embeddingForm.api_key" type="password" show-password placeholder="请输入 API Key" />
        </ElFormItem>

        <ElFormItem label="向量维度">
          <ElInputNumber v-model="embeddingForm.dimension" :min="128" :max="4096" :step="128" />
        </ElFormItem>

        <ElFormItem label="描述">
          <ElInput v-model="embeddingForm.description" type="textarea" :rows="2" placeholder="可选描述" />
        </ElFormItem>

        <ElFormItem label="启用状态">
          <ElSwitch v-model="embeddingForm.enabled" />
        </ElFormItem>
      </ElForm>

      <template #footer>
        <ElButton @click="showEmbeddingDialog = false">取消</ElButton>
        <ElButton type="primary" @click="submitEmbedding" :loading="embeddingLoading">确定</ElButton>
      </template>
    </ElDialog>
  </div>
</template>

<style scoped>
.model-config {
  height: 100%;
  box-sizing: border-box;
}

/* ====== Card 通用样式 ====== */
.model-card {
  border-radius: 10px;
  border: 1px solid var(--el-border-color-light);
}

:deep(.model-card .el-card__header) {
  padding: 14px 20px;
  background: var(--el-fill-color-lightest);
  border-bottom: 1px solid var(--el-border-color-light);
}

:deep(.model-card .el-card__body) {
  padding: 0;
}

/* ====== 卡片头部 ====== */
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.section-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  flex-shrink: 0;
}

.llm-icon {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}

.embed-icon {
  background: #f0fdf4;
  color: #16a34a;
}

.section-title {
  display: block;
  font-size: 15px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  line-height: 1.3;
}

.section-desc {
  display: block;
  font-size: 12px;
  color: var(--el-text-color-placeholder);
  margin-top: 2px;
}

/* ====== 用途映射区 ====== */
.purpose-area {
  padding: 14px 20px;
  background: var(--el-fill-color-lighter);
  border-bottom: 1px solid var(--el-border-color-light);
}

.purpose-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px 24px;
}

.purpose-grid.single {
  grid-template-columns: 1fr;
  max-width: 360px;
}

.purpose-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.purpose-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--el-text-color-regular);
}

/* ====== 表格区 ====== */
.model-table-wrap {
  padding: 0;
}

:deep(.el-table) {
  border-spacing: 0 1px;
}

:deep(.el-table .el-table__header th) {
  padding: 12px 16px;
}

:deep(.el-table .el-table__body td) {
  padding: 12px 16px;
}

:deep(.el-table .el-table__row:hover > td) {
  background-color: var(--el-fill-color-lightest) !important;
}

.model-name-text {
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.meta-tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  font-size: 12px;
  background: var(--el-fill-color-light);
  color: var(--el-text-color-secondary);
  border-radius: 4px;
}

.table-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding-right: 4px;
}

.empty-tip {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px 0;
}

.compact-tag {
  font-size: 11px !important;
  padding: 0 5px !important;
}

/* ====== 响应式 ====== */
@media (max-width: 768px) {
  .purpose-grid {
    grid-template-columns: 1fr;
  }
}
</style>
