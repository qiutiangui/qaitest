<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Menu,
  Search,
  Sun,
  Moon,
  Folder,
  FileText,
  TestTube,
  ClipboardList,
  FileBarChart,
  GitBranch,
  History,
  Sparkles,
  ChevronDown,
  Settings,
} from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()

const isDark = ref(false)
const searchQuery = ref('')
const isCollapsed = ref(false)
const expandedMenu = ref<string | null>(null)

const menuItems = [
  { 
    path: '/ai-cases', 
    name: 'AI用例生成', 
    icon: Sparkles,
    children: [
      { path: '/ai-cases/generate', name: '用例生成' },
      { path: '/ai-cases/function-points', name: '需求管理' },
      { path: '/ai-cases/test-cases', name: '测试用例' },
      { path: '/ai-cases/task-records', name: '任务记录' },
    ]
  },
  { path: '/projects', name: '项目管理', icon: Folder },
  { path: '/versions', name: '版本管理', icon: GitBranch },
  { path: '/testplans', name: '测试计划', icon: ClipboardList },
  { path: '/testreports', name: '测试报告', icon: FileBarChart },
  { 
    path: '/settings', 
    name: '设置', 
    icon: Settings,
    children: [
      { path: '/settings/model', name: '模型配置' },
      { path: '/settings/prompt', name: '提示词管理' },
    ]
  },
]

const activeMenu = computed(() => route.path)

const toggleTheme = () => {
  isDark.value = !isDark.value
  document.documentElement.classList.toggle('dark', isDark.value)
}

const handleMenuSelect = (path: string) => {
  router.push(path)
}

const toggleMenu = (path: string) => {
  expandedMenu.value = expandedMenu.value === path ? null : path
}

const isMenuActive = (item: any) => {
  if (item.children) {
    return item.children.some((child: any) => route.path === child.path)
  }
  return route.path === item.path
}
</script>

<template>
  <div class="min-h-screen bg-background-secondary">
    <!-- 顶部导航栏 -->
    <header class="fixed top-0 left-0 right-0 h-14 bg-white shadow-sm z-50 flex items-center px-4">
      <!-- Logo -->
      <div class="flex items-center gap-2 mr-8">
        <TestTube class="w-6 h-6 text-primary" />
        <span class="text-lg font-semibold text-text-primary">qaitest智测平台</span>
      </div>

      <!-- 搜索框 -->
      <div class="flex-1 max-w-md mx-4">
        <div class="relative">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-placeholder" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索项目、用例..."
            class="input-field pl-10 py-2 text-sm"
          />
        </div>
      </div>

      <!-- 右侧操作 -->
      <div class="flex items-center gap-4">
        <button
          @click="toggleTheme"
          class="p-2 rounded-md hover:bg-background-secondary transition-colors cursor-pointer"
        >
          <Sun v-if="isDark" class="w-5 h-5 text-text-secondary" />
          <Moon v-else class="w-5 h-5 text-text-secondary" />
        </button>
      </div>
    </header>

    <!-- 左侧菜单栏 -->
    <aside
      :class="[
        'fixed left-0 top-14 bottom-0 bg-white shadow-sm transition-all duration-300 z-40',
        isCollapsed ? 'w-16' : 'w-56'
      ]"
    >
      <!-- 折叠按钮 -->
      <div class="h-10 flex items-center justify-end px-2 border-b border-gray-100">
        <button
          @click="isCollapsed = !isCollapsed"
          class="p-1.5 rounded hover:bg-background-secondary transition-colors cursor-pointer"
        >
          <Menu class="w-4 h-4 text-text-secondary" />
        </button>
      </div>

      <!-- 菜单列表 -->
      <nav class="py-2">
        <div
          v-for="item in menuItems"
          :key="item.path"
        >
          <!-- 一级菜单 -->
          <div
            :class="[
              'flex items-center gap-3 px-4 py-3 cursor-pointer transition-colors',
              isMenuActive(item)
                ? 'bg-primary/10 text-primary border-r-2 border-primary'
                : 'text-text-secondary hover:bg-background-secondary hover:text-text-primary'
            ]"
            @click="item.children ? toggleMenu(item.path) : handleMenuSelect(item.path)"
          >
            <component :is="item.icon" class="w-5 h-5 flex-shrink-0" />
            <span v-if="!isCollapsed" class="text-sm flex-1">{{ item.name }}</span>
            <ChevronDown 
              v-if="!isCollapsed && item.children" 
              :class="[
                'w-4 h-4 transition-transform',
                expandedMenu === item.path ? 'rotate-180' : ''
              ]" 
            />
          </div>
          
          <!-- 二级菜单 -->
          <div
            v-if="!isCollapsed && item.children && expandedMenu === item.path"
            class="bg-gray-50 border-l-2 border-primary/20"
          >
            <div
              v-for="child in item.children"
              :key="child.path"
              :class="[
                'flex items-center gap-3 pl-12 pr-4 py-2 cursor-pointer transition-colors text-sm',
                route.path === child.path
                  ? 'text-primary font-medium'
                  : 'text-text-secondary hover:text-text-primary'
              ]"
              @click="handleMenuSelect(child.path)"
            >
              {{ child.name }}
            </div>
          </div>
        </div>
      </nav>
    </aside>

    <!-- 主内容区 -->
    <main
      :class="[
        'pt-14 min-h-screen transition-all duration-300',
        isCollapsed ? 'pl-16' : 'pl-56'
      ]"
    >
      <div class="p-6">
        <slot />
      </div>
    </main>
  </div>
</template>

<style scoped>
</style>