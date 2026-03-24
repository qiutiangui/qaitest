<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, GitCompare, ArrowRight, Plus, Minus, Check } from 'lucide-vue-next'
import { ElMessage } from 'element-plus'
import useVersionStore from '@/stores/version'
import useProjectStore from '@/stores/project'
import { projectApi } from '@/api/project'
import { versionApi } from '@/api/version'

const route = useRoute()
const router = useRouter()
const versionStore = useVersionStore()
const projectStore = useProjectStore()

const projectFilter = ref<number | null>(null)
const versionAId = ref<number | null>(null)
const versionBId = ref<number | null>(null)
const compareResult = ref<any>(null)
const loading = ref(false)

const versionsA = ref<any[]>([])
const versionsB = ref<any[]>([])

onMounted(async () => {
  await projectStore.fetchProjects({ page_size: 100 })
})

const loadVersions = async (target: 'A' | 'B') => {
  if (!projectFilter.value) {
    if (target === 'A') versionsA.value = []
    else versionsB.value = []
    return
  }
  
  try {
    const res = await versionApi.list({ project_id: projectFilter.value })
    if (target === 'A') {
      versionsA.value = res.items
      versionAId.value = null
    } else {
      versionsB.value = res.items
      versionBId.value = null
    }
  } catch (e) {
    ElMessage.error('加载版本列表失败')
  }
}

watch(projectFilter, () => {
  loadVersions('A')
  loadVersions('B')
  compareResult.value = null
})

const handleCompare = async () => {
  if (!versionAId.value || !versionBId.value) {
    ElMessage.warning('请选择要对比的两个版本')
    return
  }
  
  if (versionAId.value === versionBId.value) {
    ElMessage.warning('请选择不同的版本进行对比')
    return
  }
  
  loading.value = true
  try {
    compareResult.value = await versionApi.compare(versionAId.value, versionBId.value)
  } catch (e) {
    ElMessage.error('版本对比失败')
  } finally {
    loading.value = false
  }
}

const getVersionLabel = (version: any) => {
  return version ? `${version.version_number} (${version.status})` : ''
}

const getChangeCount = (changes: any) => {
  if (!changes) return 0
  return (changes.added?.length || 0) + (changes.removed?.length || 0)
}

const getChangeSummary = (changes: any) => {
  const added = changes.added?.length || 0
  const removed = changes.removed?.length || 0
  const common = changes.common?.length || 0
  
  const parts = []
  if (added > 0) parts.push(`新增 ${added}`)
  if (removed > 0) parts.push(`删除 ${removed}`)
  if (common > 0) parts.push(`共同 ${common}`)
  
  return parts.join(' | ')
}
</script>

<template>
  <div class="version-compare-page">
    <!-- 返回按钮 -->
    <div class="mb-4">
      <button @click="router.back()" class="flex items-center gap-1 text-text-secondary hover:text-primary transition-colors">
        <ArrowLeft class="w-4 h-4" />
        返回列表
      </button>
    </div>

    <!-- 页面标题 -->
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-semibold text-text-primary">版本对比</h1>
    </div>

    <!-- 选择区域 -->
    <div class="card mb-6">
      <div class="flex items-center gap-6">
        <div class="w-48">
          <label class="block text-sm text-text-secondary mb-1">选择项目</label>
          <select v-model="projectFilter" class="input-field">
            <option :value="null">请选择项目</option>
            <option v-for="project in projectStore.projects" :key="project.id" :value="project.id">
              {{ project.name }}
            </option>
          </select>
        </div>
        
        <div class="flex-1">
          <label class="block text-sm text-text-secondary mb-1">版本 A</label>
          <select v-model="versionAId" class="input-field" :disabled="!projectFilter">
            <option :value="null">请选择版本</option>
            <option v-for="version in versionsA" :key="version.id" :value="version.id">
              {{ version.version_number }} ({{ version.status }})
            </option>
          </select>
        </div>
        
        <div class="flex items-end pb-1">
          <GitCompare class="w-5 h-5 text-text-placeholder" />
        </div>
        
        <div class="flex-1">
          <label class="block text-sm text-text-secondary mb-1">版本 B</label>
          <select v-model="versionBId" class="input-field" :disabled="!projectFilter">
            <option :value="null">请选择版本</option>
            <option v-for="version in versionsB" :key="version.id" :value="version.id">
              {{ version.version_number }} ({{ version.status }})
            </option>
          </select>
        </div>
        
        <div class="flex items-end">
          <button 
            @click="handleCompare" 
            class="btn-primary"
            :disabled="!versionAId || !versionBId || loading"
          >
            {{ loading ? '对比中...' : '开始对比' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 对比结果 -->
    <div v-if="compareResult" class="space-y-4">
      <!-- 版本信息对比 -->
      <div class="card">
        <h3 class="text-lg font-medium text-text-primary mb-4">版本信息</h3>
        <div class="grid grid-cols-2 gap-4">
          <div class="p-4 bg-blue-50 rounded-lg">
            <div class="text-sm text-text-secondary mb-1">版本 A</div>
            <div class="text-xl font-semibold text-text-primary">{{ compareResult.version_a.version_number }}</div>
            <div class="text-sm text-text-placeholder">{{ compareResult.version_a.status }}</div>
          </div>
          <div class="p-4 bg-green-50 rounded-lg">
            <div class="text-sm text-text-secondary mb-1">版本 B</div>
            <div class="text-xl font-semibold text-text-primary">{{ compareResult.version_b.version_number }}</div>
            <div class="text-sm text-text-placeholder">{{ compareResult.version_b.status }}</div>
          </div>
        </div>
      </div>

      <!-- 功能点变更 -->
      <div class="card">
        <h3 class="text-lg font-medium text-text-primary mb-4">
          功能点变更
          <span class="text-sm font-normal text-text-secondary ml-2">
            {{ getChangeSummary(compareResult.requirement_changes) }}
          </span>
        </h3>
        
        <div v-if="getChangeCount(compareResult.requirement_changes) === 0" class="text-center py-6 text-text-secondary">
          <Check class="w-6 h-6 mx-auto mb-2 text-functional-success" />
          无变更
        </div>
        
        <div v-else class="space-y-3">
          <div v-if="compareResult.requirement_changes.added?.length" class="p-3 bg-green-50 rounded-lg">
            <div class="flex items-center gap-2 text-green-700 font-medium mb-2">
              <Plus class="w-4 h-4" />
              新增 ({{ compareResult.requirement_changes.added.length }})
            </div>
            <div class="text-sm text-text-secondary">
              ID: {{ compareResult.requirement_changes.added.join(', ') }}
            </div>
          </div>
          
          <div v-if="compareResult.requirement_changes.removed?.length" class="p-3 bg-red-50 rounded-lg">
            <div class="flex items-center gap-2 text-red-700 font-medium mb-2">
              <Minus class="w-4 h-4" />
              删除 ({{ compareResult.requirement_changes.removed.length }})
            </div>
            <div class="text-sm text-text-secondary">
              ID: {{ compareResult.requirement_changes.removed.join(', ') }}
            </div>
          </div>
        </div>
      </div>

      <!-- 测试用例变更 -->
      <div class="card">
        <h3 class="text-lg font-medium text-text-primary mb-4">
          测试用例变更
          <span class="text-sm font-normal text-text-secondary ml-2">
            {{ getChangeSummary(compareResult.testcase_changes) }}
          </span>
        </h3>
        
        <div v-if="getChangeCount(compareResult.testcase_changes) === 0" class="text-center py-6 text-text-secondary">
          <Check class="w-6 h-6 mx-auto mb-2 text-functional-success" />
          无变更
        </div>
        
        <div v-else class="space-y-3">
          <div v-if="compareResult.testcase_changes.added?.length" class="p-3 bg-green-50 rounded-lg">
            <div class="flex items-center gap-2 text-green-700 font-medium mb-2">
              <Plus class="w-4 h-4" />
              新增 ({{ compareResult.testcase_changes.added.length }})
            </div>
            <div class="text-sm text-text-secondary">
              ID: {{ compareResult.testcase_changes.added.join(', ') }}
            </div>
          </div>
          
          <div v-if="compareResult.testcase_changes.removed?.length" class="p-3 bg-red-50 rounded-lg">
            <div class="flex items-center gap-2 text-red-700 font-medium mb-2">
              <Minus class="w-4 h-4" />
              删除 ({{ compareResult.testcase_changes.removed.length }})
            </div>
            <div class="text-sm text-text-secondary">
              ID: {{ compareResult.testcase_changes.removed.join(', ') }}
            </div>
          </div>
        </div>
      </div>

      <!-- 测试计划变更 -->
      <div class="card">
        <h3 class="text-lg font-medium text-text-primary mb-4">
          测试计划变更
          <span class="text-sm font-normal text-text-secondary ml-2">
            {{ getChangeSummary(compareResult.testplan_changes) }}
          </span>
        </h3>
        
        <div v-if="getChangeCount(compareResult.testplan_changes) === 0" class="text-center py-6 text-text-secondary">
          <Check class="w-6 h-6 mx-auto mb-2 text-functional-success" />
          无变更
        </div>
        
        <div v-else class="space-y-3">
          <div v-if="compareResult.testplan_changes.added?.length" class="p-3 bg-green-50 rounded-lg">
            <div class="flex items-center gap-2 text-green-700 font-medium mb-2">
              <Plus class="w-4 h-4" />
              新增 ({{ compareResult.testplan_changes.added.length }})
            </div>
            <div class="text-sm text-text-secondary">
              ID: {{ compareResult.testplan_changes.added.join(', ') }}
            </div>
          </div>
          
          <div v-if="compareResult.testplan_changes.removed?.length" class="p-3 bg-red-50 rounded-lg">
            <div class="flex items-center gap-2 text-red-700 font-medium mb-2">
              <Minus class="w-4 h-4" />
              删除 ({{ compareResult.testplan_changes.removed.length }})
            </div>
            <div class="text-sm text-text-secondary">
              ID: {{ compareResult.testplan_changes.removed.join(', ') }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="card text-center py-20">
      <GitCompare class="w-12 h-12 mx-auto mb-4 text-text-placeholder" />
      <p class="text-text-secondary">请选择要对比的两个版本</p>
      <p class="text-sm text-text-placeholder mt-1">选择项目和版本后点击「开始对比」按钮</p>
    </div>
  </div>
</template>
