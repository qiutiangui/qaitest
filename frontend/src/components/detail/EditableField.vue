<template>
  <div :class="['field-container', spanClass]">
    <!-- 查看模式 -->
    <div v-if="!editable" class="field-view">
      <label class="field-label">
        {{ label }}
        <span v-if="required && editable" class="text-red-500 ml-1">*</span>
      </label>
      <div class="field-value">
        <!-- 状态类型 -->
        <StatusBadge 
          v-if="type === 'status'" 
          :status="modelValue" 
          :type="statusType"
        />
        <!-- 日期类型 -->
        <span v-else-if="type === 'date' && modelValue" class="text-text-primary">
          {{ formatDate(modelValue) }}
        </span>
        <!-- 文本域类型 -->
        <p v-else-if="type === 'textarea'" class="text-text-primary whitespace-pre-wrap leading-relaxed">
          {{ modelValue || placeholder || '-' }}
        </p>
        <!-- 默认文本类型 -->
        <span v-else class="text-text-primary">
          {{ modelValue || placeholder || '-' }}
        </span>
      </div>
    </div>

    <!-- 编辑模式 -->
    <div v-else class="field-edit">
      <label class="field-label">
        {{ label }}
        <span v-if="required" class="text-red-500 ml-1">*</span>
      </label>
      
      <!-- 文本输入 -->
      <input
        v-if="type === 'text' || type === 'number'"
        :type="type"
        :value="modelValue"
        :placeholder="placeholder"
        :required="required"
        class="input-field"
        @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
      />
      
      <!-- 文本域 -->
      <textarea
        v-else-if="type === 'textarea'"
        :value="modelValue"
        :placeholder="placeholder"
        :rows="rows"
        :required="required"
        class="input-field resize-none"
        @input="$emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)"
      />
      
      <!-- 选择框 -->
      <select
        v-else-if="type === 'select'"
        :value="modelValue"
        :required="required"
        class="input-field"
        @change="$emit('update:modelValue', ($event.target as HTMLSelectElement).value)"
      >
        <option value="">{{ placeholder || '请选择' }}</option>
        <option v-for="option in options" :key="option.value" :value="option.value">
          {{ option.label }}
        </option>
      </select>
      
      <!-- 日期选择 -->
      <input
        v-else-if="type === 'date'"
        type="date"
        :value="modelValue"
        :required="required"
        class="input-field"
        @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
      />
      
      <!-- 默认文本 -->
      <input
        v-else
        type="text"
        :value="modelValue"
        :placeholder="placeholder"
        :required="required"
        class="input-field"
        @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import StatusBadge from './StatusBadge.vue'

interface Option {
  label: string
  value: string | number
}

interface Props {
  label: string
  modelValue?: string | number | null
  editable?: boolean
  type?: 'text' | 'textarea' | 'select' | 'number' | 'date' | 'status'
  span?: number
  required?: boolean
  placeholder?: string
  options?: Option[]
  rows?: number
  statusType?: string
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  editable: false,
  type: 'text',
  span: 1,
  required: false,
  placeholder: '',
  options: () => [],
  rows: 3,
  statusType: 'default'
})

defineEmits<{
  'update:modelValue': [value: string | number]
}>()

const spanClass = computed(() => {
  if (props.span === 2) return 'col-span-2'
  if (props.span === 3) return 'col-span-3'
  if (props.span === 4) return 'col-span-4'
  return ''
})

function formatDate(date: string | number | Date) {
  if (!date) return '-'
  const d = new Date(date)
  return d.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
.field-container {
  @apply flex flex-col gap-2;
}

/* 查看模式样式 - 详情页 */
.field-view {
  @apply flex flex-col gap-1;
}

.field-view .field-label {
  @apply text-xs font-medium text-gray-400 uppercase tracking-wide;
}

.field-view .field-value {
  @apply text-gray-600 min-h-[24px] flex items-center px-3 py-1.5 bg-gray-50 rounded text-sm;
}

.field-view .field-value p {
  @apply text-gray-600;
}

.field-view .field-value span {
  @apply text-gray-600;
}

/* 编辑模式样式 - 编辑页 */
.field-edit {
  @apply flex flex-col gap-2;
}

.field-edit .field-label {
  @apply text-sm font-medium text-text-secondary;
}

.input-field {
  @apply w-full px-3 py-2 border border-gray-200 rounded-lg text-text-primary
         focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary
         transition-all duration-200;
}

.input-field::placeholder {
  @apply text-text-placeholder;
}

textarea.input-field {
  @apply leading-relaxed;
}
</style>
