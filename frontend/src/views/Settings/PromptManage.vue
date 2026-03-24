<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Code, Save, RotateCcw, RefreshCw, Pencil, Edit, View } from 'lucide-vue-next'
import { ElMessage, ElDialog, ElButton, ElTag, ElInput, ElTabs, ElTabPane, ElCard, ElEmpty, ElScrollbar, ElDivider, ElAlert } from 'element-plus'
import { agentPromptApi, type AgentPrompt, type PromptCategory } from '@/api/agentPrompt'

// 状态
const loading = ref(true)
const categories = ref<PromptCategory[]>([])
const activeTab = ref('all')
const saving = ref(false)

// 模态框
const showModal = ref(false)
const modalMode = ref<'view' | 'edit'>('view')
const selectedPrompt = ref<AgentPrompt | null>(null)
const editContent = ref('')
const editName = ref('')
const editDescription = ref('')

// 加载提示词分类
const loadCategories = async () => {
  try {
    loading.value = true
    const res = await agentPromptApi.listTypes()
    categories.value = res.categories || []
  } catch (error) {
    console.error('加载提示词分类失败:', error)
    ElMessage.error('加载提示词分类失败')
  } finally {
    loading.value = false
  }
}

// 获取所有提示词扁平列表
const allPrompts = computed(() => {
  const items: Array<{ agent_type: string; name: string; description: string; is_active: boolean; is_editable: boolean }> = []
  for (const cat of categories.value) {
    items.push(...cat.items)
  }
  return items
})

// 过滤后的提示词列表
const filteredPrompts = computed(() => {
  if (activeTab.value === 'all') {
    return allPrompts.value
  }
  const cat = categories.value.find(c => c.category === activeTab.value)
  return cat ? cat.items : []
})

// 分类名称映射
const getCategoryName = (category: string) => {
  const names: Record<string, string> = {
    '需求分析': '需求分析',
    '用例生成': '用例生成',
  }
  return names[category] || category
}

// 打开详情
const openPrompt = async (item: { agent_type: string; name: string }) => {
  try {
    const prompt = await agentPromptApi.getByType(item.agent_type)
    selectedPrompt.value = prompt
    editName.value = prompt.name
    editDescription.value = prompt.description || ''
    editContent.value = prompt.system_prompt
    modalMode.value = 'view'
    showModal.value = true
  } catch (error) {
    console.error('加载提示词详情失败:', error)
    ElMessage.error('加载提示词详情失败')
  }
}

// 进入编辑模式
const startEdit = () => {
  if (selectedPrompt.value) {
    editContent.value = selectedPrompt.value.system_prompt
    modalMode.value = 'edit'
  }
}

// 取消编辑
const cancelEdit = () => {
  if (selectedPrompt.value) {
    editContent.value = selectedPrompt.value.system_prompt
  }
  modalMode.value = 'view'
}

// 保存提示词
const savePrompt = async () => {
  if (!selectedPrompt.value) return

  try {
    saving.value = true
    await agentPromptApi.update(selectedPrompt.value.id, {
      system_prompt: editContent.value,
      name: editName.value,
      description: editDescription.value,
    })
    ElMessage.success('提示词保存成功')

    await loadCategories()
    const updated = await agentPromptApi.getByType(selectedPrompt.value!.agent_type)
    selectedPrompt.value = updated
    editContent.value = updated.system_prompt
    modalMode.value = 'view'
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

// 重置提示词
const resetPrompt = async () => {
  if (!selectedPrompt.value) return

  try {
    await agentPromptApi.reset(selectedPrompt.value.id)
    ElMessage.success('提示词已重置为默认值')

    await loadCategories()
    const updated = await agentPromptApi.getByType(selectedPrompt.value!.agent_type)
    selectedPrompt.value = updated
    editContent.value = updated.system_prompt
    editName.value = updated.name
    editDescription.value = updated.description || ''
    modalMode.value = 'view'
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '重置失败')
  }
}

// 初始化默认提示词
const initDefaultPrompts = async () => {
  try {
    await agentPromptApi.init()
    ElMessage.success('默认提示词初始化成功')
    await loadCategories()
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '初始化失败')
  }
}

// 高亮内容
const highlightedContent = computed(() => {
  let content = editContent.value
  content = content.replace(/\[\[([^\]]+)\]\]/g, '<span class="hl-var">[[$1]]</span>')
  content = content.replace(/^(#{1,6})\s+(.+)$/gm, '<span class="hl-heading">$1 $2</span>')
  content = content.replace(/\*\*([^*]+)\*\*/g, '<span class="hl-bold">**$1**</span>')
  content = content.replace(/^-\s+(.+)$/gm, '<span class="hl-list">- $1</span>')
  return content
})

// 格式化内容
const formatContent = () => {
  const lines = editContent.value.split('\n').map(line => line.trimEnd())
  editContent.value = lines.join('\n')
}

// 统计
const charCount = computed(() => editContent.value.length)
const lineCount = computed(() => editContent.value.split('\n').length)

onMounted(() => {
  loadCategories()
})
</script>

<template>
  <div class="prompt-manage p-6">
    <!-- 加载状态 -->
    <div v-if="loading" class="flex items-center justify-center h-64">
      <span class="text-text-secondary">加载提示词配置...</span>
    </div>

    <template v-else>
      <!-- 顶部操作栏 -->
      <div class="flex items-center justify-between mb-5">
        <h1 class="text-lg font-semibold text-text-primary">提示词管理</h1>
        <ElButton type="primary" size="small" @click="initDefaultPrompts">
          <RefreshCw class="w-3.5 h-3.5 mr-1" />
          初始化默认
        </ElButton>
      </div>

      <!-- 分类标签页 -->
      <ElTabs v-model="activeTab" class="prompt-tabs">
        <ElTabPane name="all">
          <template #label>
            <span class="tab-label">
              全部
              <span class="tab-count">{{ allPrompts.length }}</span>
            </span>
          </template>
        </ElTabPane>
        <ElTabPane
          v-for="cat in categories"
          :key="cat.category"
          :name="cat.category"
        >
          <template #label>
            <span class="tab-label">
              {{ getCategoryName(cat.category) }}
              <span class="tab-count">{{ cat.items.length }}</span>
            </span>
          </template>
        </ElTabPane>
      </ElTabs>

      <!-- 卡片网格 -->
      <div v-if="filteredPrompts.length > 0" class="cards-grid">
        <ElCard
          v-for="item in filteredPrompts"
          :key="item.agent_type"
          class="prompt-card"
          shadow="hover"
          @click="openPrompt(item)"
        >
          <template #header>
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <div class="card-icon-wrap">
                  <Code class="w-4 h-4 text-primary" />
                </div>
                <span class="card-name">{{ item.name }}</span>
              </div>
              <ElTag
                size="small"
                :type="item.is_active ? 'success' : 'info'"
                effect="light"
              >
                {{ item.is_active ? '已启用' : '未启用' }}
              </ElTag>
            </div>
          </template>

          <div class="card-body">
            <p class="card-desc">{{ item.description || '暂无描述' }}</p>
          </div>

          <template #footer>
            <div class="flex items-center justify-between">
              <span class="card-type">{{ item.agent_type }}</span>
              <ElButton size="small" text type="primary" @click.stop="openPrompt(item)">
                <View class="w-3.5 h-3.5 mr-1" />
                查看
              </ElButton>
            </div>
          </template>
        </ElCard>
      </div>

      <ElEmpty
        v-else
        description="暂无提示词"
        :image-size="80"
        class="mt-16"
      />
    </template>

    <!-- 详情/编辑模态框 -->
    <ElDialog
      v-model="showModal"
      :title="selectedPrompt?.name"
      width="900px"
      :close-on-click-modal="modalMode === 'view'"
      class="prompt-dialog"
      destroy-on-close
    >
      <div v-if="selectedPrompt" class="dialog-body">
        <!-- 左侧：提示词内容 -->
        <div class="dialog-left">
          <!-- 内容工具栏 -->
          <div class="dialog-toolbar">
            <span class="toolbar-title">系统提示词</span>
            <div class="toolbar-actions">
              <ElButton
                v-if="modalMode === 'edit'"
                size="small"
                @click="formatContent"
              >
                格式化
              </ElButton>
              <ElButton
                size="small"
                :type="modalMode === 'edit' ? 'default' : 'primary'"
                @click="modalMode === 'edit' ? cancelEdit() : startEdit()"
              >
                <component
                  :is="modalMode === 'edit' ? 'span' : Pencil"
                  :class="modalMode === 'edit' ? '' : 'w-3.5 h-3.5 mr-1'"
                />
                {{ modalMode === 'edit' ? '取消' : '编辑' }}
              </ElButton>
            </div>
          </div>

          <!-- 内容区域 -->
          <div class="dialog-content-wrap">
            <ElInput
              v-if="modalMode === 'edit'"
              v-model="editContent"
              type="textarea"
              :rows="18"
              placeholder="输入提示词模板..."
              class="prompt-textarea"
            />
            <div
              v-else
              class="prompt-preview"
              v-html="highlightedContent"
            />
          </div>

          <!-- 状态栏 -->
          <div class="dialog-statusbar">
            <span>{{ charCount }} 字符</span>
            <span class="ml-4">{{ lineCount }} 行</span>
          </div>
        </div>

        <!-- 右侧：元信息 -->
        <div class="dialog-right">
          <!-- 基本信息 -->
          <div class="right-section">
            <h4 class="section-title">基本信息</h4>
            <div class="info-row">
              <span class="info-label">名称</span>
              <ElInput
                v-if="modalMode === 'edit'"
                v-model="editName"
                size="small"
                class="flex-1"
              />
              <span v-else class="info-value">{{ selectedPrompt.name }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">类型</span>
              <span class="info-value font-mono text-xs">{{ selectedPrompt.agent_type }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">版本</span>
              <span class="info-value">v{{ selectedPrompt.version }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">状态</span>
              <ElTag
                size="small"
                :type="selectedPrompt.is_active ? 'success' : 'info'"
                effect="light"
              >
                {{ selectedPrompt.is_active ? '已启用' : '未启用' }}
              </ElTag>
            </div>
            <div class="info-row flex-start">
              <span class="info-label">描述</span>
              <ElInput
                v-if="modalMode === 'edit'"
                v-model="editDescription"
                type="textarea"
                size="small"
                :rows="3"
                placeholder="描述..."
                class="flex-1"
              />
              <span v-else class="info-value">{{ selectedPrompt.description || '暂无' }}</span>
            </div>
          </div>

          <!-- 变量列表 -->
          <div
            v-if="selectedPrompt.variables && selectedPrompt.variables.length > 0"
            class="right-section"
          >
            <h4 class="section-title">支持的变量</h4>
            <div class="var-tags">
              <ElTag
                v-for="v in selectedPrompt.variables"
                :key="v.name"
                size="small"
                effect="light"
                type="primary"
                class="var-tag"
                :title="v.description"
              >
                [[{{ v.name }}]]
              </ElTag>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="right-actions">
            <ElButton
              v-if="modalMode === 'edit'"
              @click="cancelEdit"
              size="default"
            >
              取消
            </ElButton>
            <ElButton
              v-if="modalMode === 'edit'"
              type="primary"
              :loading="saving"
              size="default"
              @click="savePrompt"
            >
              <Save class="w-3.5 h-3.5 mr-1" />
              {{ saving ? '保存中...' : '保存修改' }}
            </ElButton>
            <ElButton
              v-if="modalMode === 'view' && selectedPrompt.is_editable"
              type="warning"
              plain
              size="default"
              @click="resetPrompt"
            >
              <RotateCcw class="w-3.5 h-3.5 mr-1" />
              重置
            </ElButton>
          </div>
        </div>
      </div>
    </ElDialog>
  </div>
</template>

<style scoped>
/* ========== 整体 ========== */
.prompt-manage {
  height: 100%;
  box-sizing: border-box;
}

/* ========== 分类标签页 ========== */
:deep(.prompt-tabs) {
  margin-bottom: 20px;
}

:deep(.prompt-tabs .el-tabs__header) {
  margin-bottom: 0;
}

:deep(.prompt-tabs .el-tabs__nav) {
  border-radius: 8px;
}

:deep(.prompt-tabs .el-tabs__item) {
  font-size: 14px;
  height: 38px;
  line-height: 38px;
  padding: 0 16px;
}

:deep(.prompt-tabs .el-tabs__item.is-active) {
  color: var(--el-color-primary);
  font-weight: 500;
}

:deep(.prompt-tabs .el-tabs__active-bar) {
  height: 2px;
  border-radius: 1px;
}

:deep(.prompt-tabs .el-tabs__content) {
  display: none;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 6px;
}

.tab-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  font-size: 11px;
  font-weight: 500;
  background: var(--el-fill-color-light);
  color: var(--el-text-color-regular);
  border-radius: 9px;
}

:deep(.prompt-tabs .el-tabs__item.is-active .tab-count) {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}

/* ========== 卡片网格 ========== */
.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.prompt-card {
  cursor: pointer;
  border-radius: 10px !important;
  transition: all 0.2s;
}

.prompt-card:hover {
  transform: translateY(-2px);
}

:deep(.prompt-card .el-card__header) {
  padding: 12px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

:deep(.prompt-card .el-card__body) {
  padding: 12px 16px;
}

:deep(.prompt-card .el-card__footer) {
  padding: 8px 16px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.card-icon-wrap {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--el-color-primary-light-9);
  border-radius: 8px;
  flex-shrink: 0;
}

.card-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  line-height: 1.3;
}

.card-body {
  min-height: 48px;
}

.card-desc {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin: 0;
}

.card-type {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  font-family: 'Monaco', 'Menlo', monospace;
}

/* ========== 模态框 ========== */
.dialog-body {
  display: flex;
  gap: 20px;
  height: 580px;
}

.dialog-left {
  flex: 3;
  min-width: 0;
  display: flex;
  flex-direction: column;
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  overflow: hidden;
}

.dialog-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: var(--el-fill-color-lighter);
  border-bottom: 1px solid var(--el-border-color-light);
  flex-shrink: 0;
}

.toolbar-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--el-text-color-regular);
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.dialog-content-wrap {
  flex: 1;
  overflow: hidden;
}

:deep(.prompt-textarea) {
  height: 100%;
}

:deep(.prompt-textarea .el-textarea__inner) {
  height: 100% !important;
  resize: none;
  font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.7;
  border: none;
  border-radius: 0;
  padding: 14px;
}

.prompt-preview {
  padding: 14px;
  font-size: 13px;
  font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
  height: 100%;
  overflow-y: auto;
  color: var(--el-text-color-primary);
  box-sizing: border-box;
}

.prompt-preview :deep(.hl-var) {
  color: var(--el-color-primary);
  font-weight: 600;
  background: var(--el-color-primary-light-9);
  padding: 0 3px;
  border-radius: 3px;
}

.prompt-preview :deep(.hl-heading) {
  color: var(--el-text-color-primary);
  font-weight: 600;
}

.prompt-preview :deep(.hl-bold) {
  font-weight: 600;
}

.prompt-preview :deep(.hl-list) {
  color: var(--el-text-color-secondary);
}

.dialog-statusbar {
  display: flex;
  align-items: center;
  padding: 6px 14px;
  font-size: 12px;
  color: var(--el-text-color-placeholder);
  background: var(--el-fill-color-lighter);
  border-top: 1px solid var(--el-border-color-light);
  flex-shrink: 0;
}

/* ========== 右侧面板 ========== */
.dialog-right {
  flex: 2;
  min-width: 200px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
}

.right-section {
  background: var(--el-fill-color-lightest);
  border-radius: 10px;
  padding: 14px;
}

.section-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  margin: 0 0 12px 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 10px;
}

.info-row.flex-start {
  align-items: flex-start;
}

.info-row:last-child {
  margin-bottom: 0;
}

.info-label {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
  font-weight: 500;
  flex-shrink: 0;
  min-width: 42px;
}

.info-value {
  font-size: 13px;
  color: var(--el-text-color-primary);
  line-height: 1.5;
  text-align: right;
}

.var-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.var-tag {
  font-family: 'Monaco', 'Menlo', monospace;
  cursor: help;
}

.right-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: auto;
  padding-top: 4px;
}

/* ========== Dialog 自定义 ========== */
:deep(.prompt-dialog .el-dialog__header) {
  padding: 16px 20px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  margin-right: 0;
}

:deep(.prompt-dialog .el-dialog__title) {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

:deep(.prompt-dialog .el-dialog__body) {
  padding: 20px;
}

:deep(.prompt-dialog .el-dialog__footer) {
  padding: 12px 20px;
  border-top: 1px solid var(--el-border-color-lighter);
}
</style>
