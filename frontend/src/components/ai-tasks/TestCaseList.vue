<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { TestTube, ArrowRight, AlertCircle } from 'lucide-vue-next'

interface TestCase {
  id: number
  title: string
  priority?: string
  status?: string
  test_type?: string
  created_at?: string
}

const props = defineProps<{
  testcases: TestCase[]
  loading?: boolean
}>()

const router = useRouter()

// 优先级配置
const priorityConfig: Record<string, { color: string; bg: string }> = {
  '高': { color: 'text-red-600', bg: 'bg-red-50' },
  '中': { color: 'text-yellow-600', bg: 'bg-yellow-50' },
  '低': { color: 'text-green-600', bg: 'bg-green-50' },
}

// 状态配置
const statusConfig: Record<string, { color: string; bg: string; icon: string }> = {
  '未开始': { color: 'text-gray-600', bg: 'bg-gray-50', icon: 'circle' },
  '进行中': { color: 'text-blue-600', bg: 'bg-blue-50', icon: 'loader' },
  '已完成': { color: 'text-green-600', bg: 'bg-green-50', icon: 'check' },
  '阻塞': { color: 'text-red-600', bg: 'bg-red-50', icon: 'alert' },
}

// 获取优先级样式
const getPriorityClass = (priority?: string) => {
  if (!priority) return 'text-gray-500 bg-gray-50'
  return priorityConfig[priority] || 'text-gray-500 bg-gray-50'
}

// 获取状态样式
const getStatusClass = (status?: string) => {
  if (!status) return 'text-gray-500 bg-gray-50'
  return statusConfig[status] || 'text-gray-500 bg-gray-50'
}

// 跳转测试用例详情
const goToDetail = (id: number) => {
  router.push(`/testcase/${id}`)
}
</script>

<template>
  <div class="testcase-list">
    <!-- 空状态 -->
    <div v-if="!loading && testcases.length === 0" class="text-center py-12">
      <TestTube class="w-12 h-12 mx-auto text-gray-300 mb-3" />
      <p class="text-gray-500">暂无测试用例</p>
    </div>

    <!-- 测试用例列表 -->
    <div v-else class="space-y-3">
      <div
        v-for="tc in testcases"
        :key="tc.id"
        @click="goToDetail(tc.id)"
        class="bg-white rounded-xl border border-gray-200 p-4 hover:border-primary/50 hover:shadow-sm transition-all cursor-pointer group"
      >
        <div class="flex items-start gap-4">
          <!-- 图标 -->
          <div class="w-10 h-10 rounded-lg bg-teal-50 flex items-center justify-center shrink-0">
            <TestTube class="w-5 h-5 text-teal-600" />
          </div>

          <!-- 内容 -->
          <div class="flex-1 min-w-0">
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0">
                <h4 class="font-medium text-gray-900 group-hover:text-primary transition-colors line-clamp-1">
                  {{ tc.title }}
                </h4>
                <div class="flex items-center gap-3 mt-1.5 flex-wrap">
                  <!-- 优先级 -->
                  <span
                    v-if="tc.priority"
                    :class="['px-2 py-0.5 rounded text-xs font-medium', getPriorityClass(tc.priority)]"
                  >
                    {{ tc.priority }}
                  </span>
                  <!-- 状态 -->
                  <span
                    v-if="tc.status"
                    :class="['px-2 py-0.5 rounded text-xs font-medium', getStatusClass(tc.status)]"
                  >
                    {{ tc.status }}
                  </span>
                  <!-- 测试类型 -->
                  <span v-if="tc.test_type" class="text-xs text-gray-500">
                    {{ tc.test_type }}
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
