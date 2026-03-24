<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Code, Save, RotateCcw, Eye, EyeOff } from 'lucide-vue-next'

interface Variable {
  name: string
  description: string
  example?: string
}

interface Props {
  modelValue: string
  variables?: Variable[]
  readonly?: boolean
}

interface Emits {
  (e: 'update:modelValue', value: string): void
  (e: 'save'): void
}

const props = withDefaults(defineProps<Props>(), {
  variables: () => [],
  readonly: false,
})

const emit = defineEmits<Emits>()

const localValue = ref(props.modelValue)
const showPreview = ref(false)
const previewContent = ref('')

watch(() => props.modelValue, (val) => {
  localValue.value = val
})

watch(localValue, (val) => {
  emit('update:modelValue', val)
})

const highlightedContent = computed(() => {
  let content = localValue.value
  
  // 高亮变量 [[variable]]
  content = content.replace(/\[\[([^\]]+)\]\]/g, '<span class="variable">[[$1]]</span>')
  
  // 高亮标题 ## xxx
  content = content.replace(/^(#{1,6})\s+(.+)$/gm, '<span class="heading">$1 $2</span>')
  
  // 高亮粗体 **xxx**
  content = content.replace(/\*\*([^*]+)\*\*/g, '<span class="bold">**$1**</span>')
  
  // 高亮列表 - xxx
  content = content.replace(/^-\s+(.+)$/gm, '<span class="list">- $1</span>')
  
  return content
})

const handleSave = () => {
  emit('save')
}

const handleReset = () => {
  emit('update:modelValue', '')
}

const formatContent = () => {
  // 简单的格式化：统一缩进
  let lines = localValue.value.split('\n')
  lines = lines.map(line => line.trimEnd())
  localValue.value = lines.join('\n')
}
</script>

<template>
  <div class="prompt-editor">
    <!-- 工具栏 -->
    <div class="editor-toolbar">
      <div class="toolbar-left">
        <Code class="w-4 h-4 text-text-secondary" />
        <span class="toolbar-title">提示词编辑</span>
      </div>
      <div class="toolbar-right">
        <button 
          class="toolbar-btn"
          @click="formatContent"
          :disabled="readonly"
          title="格式化"
        >
          格式化
        </button>
        <button 
          class="toolbar-btn"
          @click="showPreview = !showPreview"
          :class="{ active: showPreview }"
        >
          <Eye v-if="!showPreview" class="w-4 h-4" />
          <EyeOff v-else class="w-4 h-4" />
          {{ showPreview ? '编辑' : '预览' }}
        </button>
        <button 
          v-if="!readonly"
          class="toolbar-btn primary"
          @click="handleSave"
        >
          <Save class="w-4 h-4" />
          保存
        </button>
      </div>
    </div>

    <!-- 变量说明 -->
    <div v-if="variables.length > 0" class="variables-panel">
      <div class="variables-title">支持的变量</div>
      <div class="variables-list">
        <span 
          v-for="v in variables" 
          :key="v.name" 
          class="variable-tag"
          :title="v.description"
        >
          [[{{ v.name }}]]
        </span>
      </div>
    </div>

    <!-- 编辑器区域 -->
    <div class="editor-content">
      <textarea
        v-if="!showPreview"
        v-model="localValue"
        class="editor-textarea"
        :readonly="readonly"
        :placeholder="readonly ? '暂无提示词' : '输入提示词模板...'"
      />
      <div 
        v-else 
        class="editor-preview"
        v-html="highlightedContent"
      />
    </div>

    <!-- 状态栏 -->
    <div class="editor-statusbar">
      <span class="char-count">{{ localValue.length }} 字符</span>
      <span class="line-count">{{ localValue.split('\n').length }} 行</span>
      <span v-if="readonly" class="readonly-badge">只读</span>
    </div>
  </div>
</template>

<style scoped>
.prompt-editor {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  overflow: hidden;
  background: var(--color-bg-primary);
}

.editor-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border);
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toolbar-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toolbar-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  font-size: 13px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  background: var(--color-bg-primary);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.toolbar-btn:hover:not(:disabled) {
  background: var(--color-bg-hover);
  border-color: var(--color-border-hover);
}

.toolbar-btn.primary {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

.toolbar-btn.primary:hover {
  opacity: 0.9;
}

.toolbar-btn.active {
  background: var(--color-primary-light);
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.toolbar-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.variables-panel {
  padding: 8px 12px;
  background: var(--color-bg-tertiary);
  border-bottom: 1px solid var(--color-border);
}

.variables-title {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-secondary);
  margin-bottom: 6px;
}

.variables-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.variable-tag {
  display: inline-block;
  padding: 2px 8px;
  font-size: 12px;
  font-family: monospace;
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  color: var(--color-primary);
}

.editor-content {
  flex: 1;
  min-height: 300px;
}

.editor-textarea {
  width: 100%;
  height: 100%;
  min-height: 300px;
  padding: 12px;
  font-size: 14px;
  font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
  line-height: 1.6;
  border: none;
  outline: none;
  resize: vertical;
  background: var(--color-bg-primary);
  color: var(--color-text-primary);
}

.editor-textarea:readonly {
  background: var(--color-bg-tertiary);
  cursor: not-allowed;
}

.editor-preview {
  padding: 12px;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  overflow-y: auto;
  height: 100%;
  min-height: 300px;
}

.editor-preview :deep(.variable) {
  color: var(--color-primary);
  font-weight: 600;
  background: var(--color-primary-light);
  padding: 0 2px;
  border-radius: 2px;
}

.editor-preview :deep(.heading) {
  color: var(--color-text-primary);
  font-weight: 600;
}

.editor-preview :deep(.bold) {
  font-weight: 600;
}

.editor-preview :deep(.list) {
  color: var(--color-text-secondary);
}

.editor-statusbar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 12px;
  font-size: 12px;
  color: var(--color-text-placeholder);
  background: var(--color-bg-secondary);
  border-top: 1px solid var(--color-border);
}

.char-count,
.line-count {
  display: flex;
  align-items: center;
}

.readonly-badge {
  margin-left: auto;
  padding: 2px 8px;
  font-size: 11px;
  background: var(--color-bg-tertiary);
  border-radius: 4px;
  color: var(--color-text-secondary);
}
</style>
