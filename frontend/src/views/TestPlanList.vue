<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { Plus, Trash2, Eye } from 'lucide-vue-next'
import useTestplanStore from '@/stores/testplan'
import useProjectStore from '@/stores/project'
import { useRouter } from 'vue-router'

const router = useRouter()
const testplanStore = useTestplanStore()
const projectStore = useProjectStore()

// 筛选条件
const selectedProject = ref<number | undefined>()
const selectedVersion = ref<number | undefined>()
const selectedStatus = ref<string | undefined>()

// 分页
const currentPage = ref(1)
const pageSize = ref(12)

// 创建计划弹窗
const showCreateDialog = ref(false)
const newPlan = ref({
  name: '',
  description: '',
  project_id: undefined as number | undefined,
  version_id: undefined as number | undefined,
  status: '未开始',
})

// 状态选项
const statuses = ['未开始', '进行中', '已完成', '已归档']

// 计算总页数
const totalPages = computed(() => Math.ceil(testplanStore.total / pageSize.value))

// 获取计划列表
async function fetchList() {
  await testplanStore.fetchTestplans({
    page: currentPage.value,
    page_size: pageSize.value,
    project_id: selectedProject.value,
    version_id: selectedVersion.value,
    status: selectedStatus.value,
  })
}

// 筛选变化
function handleFilterChange() {
  currentPage.value = 1
  fetchList()
}

// 分页变化
function handlePageChange(page: number) {
  currentPage.value = page
  fetchList()
}

// 创建计划
async function handleCreate() {
  if (!newPlan.value.name || !newPlan.value.project_id) {
    alert('请填写计划名称和选择项目')
    return
  }

  await testplanStore.createTestplan(newPlan.value as any)
  showCreateDialog.value = false
  newPlan.value = {
    name: '',
    description: '',
    project_id: undefined,
    version_id: undefined,
    status: '未开始',
  }
  fetchList()
}

// 删除计划
async function deletePlan(id: number, name: string) {
  if (confirm(`确定要删除测试计划"${name}"吗？`)) {
    await testplanStore.deleteTestplan(id)
    fetchList()
  }
}

// 查看详情
function viewDetail(id: number) {
  router.push(`/testplans/${id}`)
}

// 获取状态颜色
function getStatusColor(status: string) {
  const colors: Record<string, string> = {
    '未开始': 'bg-gray-100 text-gray-700',
    '进行中': 'bg-blue-100 text-blue-700',
    '已完成': 'bg-green-100 text-green-700',
    '已归档': 'bg-gray-100 text-gray-500',
  }
  return colors[status] || 'bg-gray-100 text-gray-700'
}

onMounted(async () => {
  await projectStore.fetchProjects({ page_size: 100 })
  fetchList()
})
</script>

<template>
  <div class="testplan-list-page">
    <!-- 页面标题 -->
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-semibold text-text-primary">测试计划</h1>
      <button class="btn-primary flex items-center gap-2" @click="showCreateDialog = true">
        <Plus class="w-4 h-4" />
        新建计划
      </button>
    </div>

    <!-- 筛选区域 -->
    <div class="card mb-4">
      <div class="flex flex-wrap items-center gap-4">
        <!-- 项目筛选 -->
        <div class="flex items-center gap-2">
          <label class="text-sm text-text-secondary">项目：</label>
          <select
            v-model="selectedProject"
            class="input-field w-48"
            @change="handleFilterChange"
          >
            <option :value="undefined">全部项目</option>
            <option
              v-for="project in projectStore.projects"
              :key="project.id"
              :value="project.id"
            >
              {{ project.name }}
            </option>
          </select>
        </div>

        <!-- 状态筛选 -->
        <div class="flex items-center gap-2">
          <label class="text-sm text-text-secondary">状态：</label>
          <select
            v-model="selectedStatus"
            class="input-field w-32"
            @change="handleFilterChange"
          >
            <option :value="undefined">全部</option>
            <option v-for="s in statuses" :key="s" :value="s">{{ s }}</option>
          </select>
        </div>
      </div>
    </div>

    <!-- 计划卡片列表 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="plan in testplanStore.testplans"
        :key="plan.id"
        class="card hover:shadow-md transition-shadow group"
      >
        <div class="flex items-start justify-between mb-2">
          <h3 class="text-lg font-medium text-text-primary">{{ plan.name }}</h3>
          <div class="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              class="text-primary hover:text-primary-light transition-colors"
              title="查看详情"
              @click.stop="viewDetail(plan.id)"
            >
              <Eye class="w-4 h-4" />
            </button>
            <button
              class="text-functional-danger hover:text-red-600 transition-colors"
              title="删除"
              @click.stop="deletePlan(plan.id, plan.name)"
            >
              <Trash2 class="w-4 h-4" />
            </button>
          </div>
        </div>
        
        <p class="text-sm text-text-secondary mb-3 line-clamp-2">
          {{ plan.description || '暂无描述' }}
        </p>
        
        <div class="flex items-center justify-between">
          <span :class="['px-2 py-0.5 rounded text-xs font-medium', getStatusColor(plan.status)]">
            {{ plan.status }}
          </span>
          <span class="text-xs text-text-placeholder">
            {{ new Date(plan.created_at).toLocaleDateString() }}
          </span>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div
      v-if="testplanStore.testplans.length === 0 && !testplanStore.loading"
      class="card text-center py-10 text-text-secondary"
    >
      暂无测试计划
    </div>

    <!-- 加载中 -->
    <div v-if="testplanStore.loading" class="card text-center py-10 text-text-secondary">
      加载中...
    </div>

    <!-- 分页 -->
    <div v-if="testplanStore.total > 0" class="flex items-center justify-between mt-6 px-2">
      <div class="text-sm text-text-secondary">共 {{ testplanStore.total }} 条记录</div>
      <div class="flex items-center gap-2">
        <button
          class="px-3 py-1 rounded border border-gray-300 text-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="currentPage === 1"
          @click="handlePageChange(currentPage - 1)"
        >
          上一页
        </button>

        <div class="flex items-center gap-1">
          <button
            v-for="page in Math.min(totalPages, 5)"
            :key="page"
            :class="[
              'px-3 py-1 rounded text-sm transition-colors',
              currentPage === page
                ? 'bg-primary text-white'
                : 'border border-gray-300 hover:bg-gray-50',
            ]"
            @click="handlePageChange(page)"
          >
            {{ page }}
          </button>
          <span v-if="totalPages > 5" class="text-text-secondary px-2">...</span>
          <button
            v-if="totalPages > 5"
            :class="[
              'px-3 py-1 rounded text-sm transition-colors',
              currentPage === totalPages
                ? 'bg-primary text-white'
                : 'border border-gray-300 hover:bg-gray-50',
            ]"
            @click="handlePageChange(totalPages)"
          >
            {{ totalPages }}
          </button>
        </div>

        <button
          class="px-3 py-1 rounded border border-gray-300 text-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="currentPage === totalPages"
          @click="handlePageChange(currentPage + 1)"
        >
          下一页
        </button>
      </div>
    </div>

    <!-- 创建计划弹窗 -->
    <div
      v-if="showCreateDialog"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      @click.self="showCreateDialog = false"
    >
      <div class="bg-white rounded-lg shadow-xl w-[500px]">
        <div class="p-6">
          <h2 class="text-xl font-semibold text-text-primary mb-4">新建测试计划</h2>

          <div class="space-y-4">
            <div>
              <label class="block text-sm text-text-secondary mb-1">计划名称 *</label>
              <input
                v-model="newPlan.name"
                type="text"
                class="input-field"
                placeholder="请输入计划名称"
              />
            </div>

            <div>
              <label class="block text-sm text-text-secondary mb-1">所属项目 *</label>
              <select v-model="newPlan.project_id" class="input-field">
                <option :value="undefined">请选择项目</option>
                <option
                  v-for="project in projectStore.projects"
                  :key="project.id"
                  :value="project.id"
                >
                  {{ project.name }}
                </option>
              </select>
            </div>

            <div>
              <label class="block text-sm text-text-secondary mb-1">关联版本</label>
              <select v-model="newPlan.version_id" class="input-field">
                <option :value="undefined">不关联版本</option>
                <!-- TODO: 根据选择的项目动态加载版本列表 -->
              </select>
            </div>

            <div>
              <label class="block text-sm text-text-secondary mb-1">计划描述</label>
              <textarea
                v-model="newPlan.description"
                class="input-field h-20 resize-none"
                placeholder="请输入计划描述"
              />
            </div>

            <div>
              <label class="block text-sm text-text-secondary mb-1">状态</label>
              <select v-model="newPlan.status" class="input-field">
                <option v-for="s in statuses" :key="s" :value="s">{{ s }}</option>
              </select>
            </div>
          </div>

          <div class="flex items-center justify-end gap-2 mt-6">
            <button class="btn-secondary" @click="showCreateDialog = false">取消</button>
            <button class="btn-primary" @click="handleCreate">创建</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
