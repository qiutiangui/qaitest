<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { FileText, ArrowRight, Tag, Layers, Zap } from 'lucide-vue-next'

interface Requirement {
  id: number
  name: string
  category?: string
  module?: string
  priority?: string
  created_at?: string
}

const props = defineProps<{
  requirements: Requirement[]
  loading?: boolean
}>()

const router = useRouter()

// 优先级配置
const priorityConfig: Record<string, { color: string; bg: string }> = {
  '高': { color: 'text-red-600', bg: 'bg-red-50' },
  '中': { color: 'text-yellow-600', bg: 'bg-yellow-50' },
  '低': { color: 'text-green-600', bg: 'bg-green-50' },
}

// 获取优先级样式
const getPriorityClass = (priority?: string) => {
  if (!priority) return 'text-gray-500 bg-gray-50'
  return priorityConfig[priority] || 'text-gray-500 bg-gray-50'
}

// 跳转功能点详情
const goToDetail = (id: number) => {
  router.push(`/requirement/${id}`)
}

// 格式化日期
const formatDate = (dateStr?: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}
</script>

<template>
  <div class="requirement-list">
    <!-- 空状态 -->
    <div v-if="!loading && requirements.length === 0" class="text-center py-12">
      <FileText class="w-12 h-12 mx-auto text-gray-300 mb-3" />
      <p class="text-gray-500">暂无功能点</p>
    </div>

    <!-- 功能点列表 -->
    <div v-else class="space-y-3">
      <div
        v-for="req in requirements"
        :key="req.id"
        @click="goToDetail(req.id)"
        class="bg-white rounded-xl border border-gray-200 p-4 hover:border-primary/50 hover:shadow-sm transition-all cursor-pointer group"
      >
        <div class="flex items-start gap-4">
          <!-- 图标 -->
          <div class="w-10 h-10 rounded-lg bg-purple-50 flex items-center justify-center shrink-0">
            <FileText class="w-5 h-5 text-purple-600" />
          </div>

          <!-- 内容 -->
          <div class="flex-1 min-w-0">
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0">
                <h4 class="font-medium text-gray-900 group-hover:text-primary transition-colors line-clamp-1">
                  {{ req.name }}
                </h4>
                <div class="flex items-center gap-3 mt-1.5 flex-wrap">
                  <!-- 优先级 -->
                  <span
                    v-if="req.priority"
                    :class="['px-2 py-0.5 rounded text-xs font-medium', getPriorityClass(req.priority)]"
                  >
                    {{ req.priority }}
                  </span>
                  <!-- 模块 -->
                  <span v-if="req.module" class="flex items-center gap-1 text-xs text-gray-500">
                    <Layers class="w-3 h-3" />
                    {{ req.module }}
                  </span>
                  <!-- 类别 -->
                  <span v-if="req.category" class="flex items-center gap-1 text-xs text-gray-500">
                    <Tag class="w-3 h-3" />
                    {{ req.category }}
                  </span>
                </div>
              </div>

              <!-- 箭头 -->
              <ArrowRight class="w-5 h-5 text-gray-400 group-hover:text-primary group-hover:translate-x-0.5 transition-all shrink-0" />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
