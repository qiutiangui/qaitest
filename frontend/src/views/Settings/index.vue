<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Settings as SettingsIcon, Sparkles } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()

const activeMenu = computed(() => {
  const path = route.path
  if (path.includes('/prompt')) return '/settings/prompt'
  return '/settings/model'
})

const subMenus = [
  { path: '/settings/model', name: '模型配置', icon: Sparkles },
  { path: '/settings/prompt', name: '提示词管理', icon: SettingsIcon },
]

const handleMenuSelect = (path: string) => {
  router.push(path)
}
</script>

<template>
  <div class="h-full flex flex-col">
    <!-- 顶部二级菜单栏 -->
    <div class="bg-white border-b border-gray-200 px-6 py-3 flex items-center gap-2">
      <SettingsIcon class="w-5 h-5 text-primary" />
      <span class="text-base font-semibold text-text-primary mr-6">设置</span>
      
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
