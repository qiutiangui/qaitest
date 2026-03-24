<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  status: string
  type?: 'default' | 'priority' | 'execution' | 'plan'
}

const props = withDefaults(defineProps<Props>(), {
  type: 'default'
})

const badgeStyle = computed(() => {
  const statusStyles: Record<string, Record<string, { bg: string; text: string }>> = {
    default: {
      '未开始': { bg: 'bg-gray-100', text: 'text-gray-700' },
      '进行中': { bg: 'bg-blue-100', text: 'text-blue-700' },
      '已完成': { bg: 'bg-green-100', text: 'text-green-700' },
      '已阻塞': { bg: 'bg-red-100', text: 'text-red-700' },
      '已归档': { bg: 'bg-gray-100', text: 'text-gray-500' },
      '草稿': { bg: 'bg-gray-100', text: 'text-gray-700' },
      '已发布': { bg: 'bg-green-100', text: 'text-green-700' },
    },
    priority: {
      '高': { bg: 'bg-red-100', text: 'text-red-700' },
      '中': { bg: 'bg-orange-100', text: 'text-orange-700' },
      '低': { bg: 'bg-green-100', text: 'text-green-700' },
    },
    execution: {
      '未执行': { bg: 'bg-gray-100', text: 'text-gray-600' },
      '通过': { bg: 'bg-green-100', text: 'text-green-700' },
      '失败': { bg: 'bg-red-100', text: 'text-red-700' },
      '阻塞': { bg: 'bg-orange-100', text: 'text-orange-700' },
    },
    plan: {
      '未开始': { bg: 'bg-gray-100', text: 'text-gray-700' },
      '进行中': { bg: 'bg-blue-100', text: 'text-blue-700' },
      '已完成': { bg: 'bg-green-100', text: 'text-green-700' },
      '已归档': { bg: 'bg-gray-100', text: 'text-gray-500' },
    }
  }

  const typeStyles = statusStyles[props.type] || statusStyles.default
  return typeStyles[props.status] || { bg: 'bg-gray-100', text: 'text-gray-700' }
})
</script>

<template>
  <span 
    :class="[
      'inline-flex items-center px-3 py-1 rounded-full text-sm font-medium transition-all',
      badgeStyle.bg,
      badgeStyle.text
    ]"
  >
    {{ status }}
  </span>
</template>
