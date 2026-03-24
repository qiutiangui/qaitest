<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Sparkles, Zap, ListChecks, TestTube, History } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()

const subMenus = [
  { path: '/ai-cases/generate', name: '用例生成', icon: Zap },
  { path: '/ai-cases/function-points', name: '需求管理', icon: ListChecks },
  { path: '/ai-cases/test-cases', name: '测试用例', icon: TestTube },
  { path: '/ai-cases/task-records', name: '任务记录', icon: History },
]

const activeMenu = computed(() => route.path)

const handleMenuSelect = (path: string) => {
  router.push(path)
}
</script>

<template>
  <div class="h-full flex flex-col">
    <!-- 顶部二级菜单栏 -->
    <div class="bg-white border-b border-gray-200 px-6 py-3 flex items-center gap-2">
      <Sparkles class="w-5 h-5 text-primary" />
      <span class="text-base font-semibold text-text-primary mr-6">AI用例生成</span>
      
      <nav class="flex items-center gap-1">
        <button
          v-for="menu in subMenus"
          :key="menu.path"
          :class="[
            'flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all cursor-pointer',
            activeMenu === menu.path
              ? 'bg-primary text-white shadow-sm'
              : 'text-text-secondary hover:bg-gray-100 hover:text-text-primary'
          ]"
          @click="handleMenuSelect(menu.path)"
        >
          <component :is="menu.icon" class="w-4 h-4" />
          <span>{{ menu.name }}</span>
        </button>
      </nav>
    </div>

    <!-- 主内容区 -->
    <div class="flex-1 overflow-auto bg-background-secondary">
      <router-view />
    </div>
  </div>
</template>

<style scoped>
</style>
