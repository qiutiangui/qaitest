<script setup lang="ts">
interface Props {
  label: string
  value?: string | number | null
  type?: 'text' | 'textarea' | 'badge' | 'date'
  span?: 1 | 2
  badgeColor?: string
}

const props = withDefaults(defineProps<Props>(), {
  type: 'text',
  span: 1,
  badgeColor: 'bg-blue-100 text-blue-700'
})

function formatDate(date: string | number | null | undefined): string {
  if (!date) return '-'
  if (typeof date === 'number') return String(date)
  try {
    return new Date(date).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return String(date)
  }
}

function displayValue(): string {
  if (props.value === null || props.value === undefined || props.value === '') {
    return '-'
  }
  
  if (props.type === 'date') {
    return formatDate(props.value)
  }
  
  return String(props.value)
}
</script>

<template>
  <div :class="['info-field', span === 2 ? 'col-span-2' : '']">
    <label class="block text-sm font-medium text-text-secondary mb-1.5">
      {{ label }}
    </label>
    
    <!-- Text Type -->
    <p v-if="type === 'text'" class="text-text-primary">
      {{ displayValue() }}
    </p>
    
    <!-- Textarea Type -->
    <p v-else-if="type === 'textarea'" class="text-text-primary whitespace-pre-wrap leading-relaxed">
      {{ displayValue() }}
    </p>
    
    <!-- Badge Type -->
    <span 
      v-else-if="type === 'badge'" 
      :class="[
        'inline-flex items-center px-3 py-1 rounded-full text-sm font-medium',
        badgeColor
      ]"
    >
      {{ displayValue() }}
    </span>
    
    <!-- Date Type -->
    <p v-else-if="type === 'date'" class="text-text-primary text-sm">
      {{ displayValue() }}
    </p>
    
    <!-- Default -->
    <p v-else class="text-text-primary">
      {{ displayValue() }}
    </p>
  </div>
</template>

<style scoped>
.info-field {
  min-height: 60px;
}
</style>
