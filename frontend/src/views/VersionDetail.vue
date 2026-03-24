<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, GitCompare, Archive, Rocket, Camera, FileText, CheckSquare, BarChart3, FileCheck, GitBranch, Edit, Delete, Save, X } from 'lucide-vue-next'
import { ElMessage, ElMessageBox } from 'element-plus'
import useVersionStore from '@/stores/version'
import useProjectStore from '@/stores/project'
import type { ProjectVersion } from '@/types/version'
import DetailHeader from '@/components/detail/DetailHeader.vue'
import DetailCard from '@/components/detail/DetailCard.vue'
import EditableField from '@/components/detail/EditableField.vue'
import StatusBadge from '@/components/detail/StatusBadge.vue'

const route = useRoute()
const router = useRouter()
const versionStore = useVersionStore()
const projectStore = useProjectStore()

const activeTab = ref('overview')
const version = ref<ProjectVersion | null>(null)
const loading = ref(true)
const isEditing = ref(false)
const formData = ref({
  version_number: '',
  version_name: '',
  description: '',
  release_notes: ''
})
const stats = ref({
  requirement_count: 0,
  testcase_count: 0,
  testplan_count: 0,
  report_count: 0,
})

const versionId = computed(() => Number(route.params.id))

onMounted(async () => {
  await loadData()
})

const loadData = async () => {
  loading.value = true
  try {
    version.value = await versionStore.fetchVersion(versionId.value)
    if (version.value) {
      // 获取版本统计信息
      const statsData = await versionStore.getVersionStats(versionId.value)
      stats.value = statsData
    }
  } finally {
    loading.value = false
  }
}

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    '开发中': 'bg-blue-100 text-blue-700',
    '测试中': 'bg-yellow-100 text-yellow-700',
    '已发布': 'bg-green-100 text-green-700',
    '已归档': 'bg-gray-100 text-gray-500',
  }
  return colors[status] || 'bg-gray-100 text-gray-700'
}

// 开始编辑
function handleEdit() {
  if (!version.value) return
  isEditing.value = true
  formData.value = {
    version_number: version.value.version_number || '',
    version_name: version.value.version_name || '',
    description: version.value.description || '',
    release_notes: version.value.release_notes || ''
  }
}

// 取消编辑
function handleCancel() {
  isEditing.value = false
  formData.value = {
    version_number: '',
    version_name: '',
    description: '',
    release_notes: ''
  }
}

// 保存
async function handleSave() {
  if (!version.value) return
  
  try {
    await versionStore.updateVersion(version.value.id, formData.value)
    ElMessage.success('保存成功')
    isEditing.value = false
    await loadData()
  } catch {
    ElMessage.error('保存失败')
  }
}

// 删除
async function handleDelete() {
  if (!version.value) return
  
  try {
    await ElMessageBox.confirm(
      `确定要删除版本「${version.value.version_number}」吗？`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await versionStore.deleteVersion(version.value.id)
    ElMessage.success('删除成功')
    router.push('/versions')
  } catch {
    // 用户取消
  }
}

const handleRelease = async () => {
  if (!version.value) return
  
  try {
    await ElMessageBox.confirm(`确定发布版本「${version.value.version_number}」吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'info',
    })
    await versionStore.releaseVersion(version.value.id)
    ElMessage.success('发布成功')
    await loadData()
  } catch (e) {
    // 取消
  }
}

const handleArchive = async () => {
  if (!version.value) return
  
  try {
    await ElMessageBox.confirm(`确定归档版本「${version.value.version_number}」吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await versionStore.archiveVersion(version.value.id)
    ElMessage.success('归档成功')
    await loadData()
  } catch (e) {
    // 取消
  }
}

const handleCreateBaseline = async () => {
  if (!version.value) return
  
  try {
    await versionStore.createBaseline(version.value.id)
    ElMessage.success('基线创建成功')
    await loadData()
  } catch (e) {
    ElMessage.error('基线创建失败')
  }
}

const handleCompare = () => {
  router.push('/versions/compare')
}

const getProjectName = (projectId: number) => {
  const project = projectStore.projects.find(p => p.id === projectId)
  return project?.name || '未知项目'
}
</script>

<template>
  <div class="version-detail-page p-6 max-w-7xl mx-auto">
    <!-- 加载状态 -->
    <div v-if="loading" class="text-center py-20">
      <div class="inline-flex items-center gap-2 text-text-secondary">
        <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-primary" />
        <span>加载中...</span>
      </div>
    </div>

    <template v-else-if="version">
      <!-- Header -->
      <DetailHeader 
        :title="version.version_number"
        :subtitle="version.version_name || '暂无版本名称'"
        back-to="/versions"
        :breadcrumb="[getProjectName(version.project_id)]"
      >
        <template #actions>
          <StatusBadge 
            v-if="version.status" 
            :status="version.status" 
          />
          <span 
            v-if="version.is_baseline" 
            class="px-3 py-1 rounded-full text-sm font-medium bg-gradient-to-r from-purple-500 to-purple-600 text-white shadow-md"
          >
            基线版本
          </span>
          <template v-if="isEditing">
            <button class="px-3 py-1.5 text-white/80 hover:text-white hover:bg-white/10 rounded-lg transition-colors flex items-center gap-1" @click="handleCancel">
              <X class="w-4 h-4" />
              取消
            </button>
            <button class="px-3 py-1.5 bg-white text-blue-600 hover:bg-white/90 rounded-lg font-medium transition-colors flex items-center gap-1" @click="handleSave">
              <Save class="w-4 h-4" />
              保存
            </button>
          </template>
          <template v-else>
            <button class="px-3 py-1.5 text-white/80 hover:text-white hover:bg-white/10 rounded-lg transition-colors flex items-center gap-1 border border-white/30" @click="handleEdit">
              <Edit class="w-4 h-4" />
              编辑
            </button>
            <button class="px-3 py-1.5 text-white/80 hover:text-red-200 hover:bg-red-500/20 rounded-lg transition-colors flex items-center gap-1" @click="handleDelete">
              <Delete class="w-4 h-4" />
              删除
            </button>
            <button v-if="version.status === '测试中'" @click="handleRelease" class="px-3 py-1.5 bg-white text-blue-600 hover:bg-white/90 rounded-lg font-medium transition-colors flex items-center gap-1">
              <Rocket class="w-4 h-4" />
              发布
            </button>
            <button v-if="version.status === '已发布'" @click="handleArchive" class="px-3 py-1.5 text-white/80 hover:text-white hover:bg-white/10 rounded-lg transition-colors flex items-center gap-1 border border-white/30">
              <Archive class="w-4 h-4" />
              归档
            </button>
            <button @click="handleCreateBaseline" class="px-3 py-1.5 text-white/80 hover:text-white hover:bg-white/10 rounded-lg transition-colors flex items-center gap-1 border border-white/30">
              <Camera class="w-4 h-4" />
              创建基线
            </button>
            <button @click="handleCompare" class="px-3 py-1.5 text-white/80 hover:text-white hover:bg-white/10 rounded-lg transition-colors flex items-center gap-1 border border-white/30">
              <GitCompare class="w-4 h-4" />
              版本对比
            </button>
          </template>
        </template>
      </DetailHeader>

      <!-- 基本信息 -->
      <DetailCard title="基本信息" :icon="FileText" class="mb-6">
        <div class="grid grid-cols-2 gap-6">
          <EditableField 
            label="版本号" 
            v-model="formData.version_number"
            :editable="isEditing"
            required
          />
          <EditableField 
            label="版本名称" 
            v-model="formData.version_name"
            :editable="isEditing"
            placeholder="请输入版本名称"
          />
          <EditableField 
            label="版本描述" 
            v-model="formData.description"
            :editable="isEditing"
            type="textarea"
            :span="2"
            :rows="3"
            placeholder="请输入版本描述"
          />
          <EditableField 
            label="发布说明" 
            v-model="formData.release_notes"
            :editable="isEditing"
            type="textarea"
            :span="2"
            :rows="4"
            placeholder="请输入发布说明"
          />
          <EditableField 
            label="所属项目" 
            :model-value="getProjectName(version.project_id)"
            :editable="false"
          />
          <EditableField 
            label="创建时间" 
            :model-value="version.created_at"
            type="date"
            :editable="false"
          />
          <EditableField 
            v-if="version.released_at"
            label="发布时间" 
            :model-value="version.released_at"
            type="date"
            :editable="false"
          />
          <EditableField 
            v-if="version.created_by"
            label="创建人" 
            :model-value="version.created_by"
            :editable="false"
          />
        </div>
      </DetailCard>

      <!-- 统计卡片 -->
      <div class="grid grid-cols-4 gap-4 mb-6">
        <!-- 功能点 -->
        <div class="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-6 text-white shadow-lg hover:shadow-xl transition-shadow">
          <div class="flex items-center justify-between mb-2">
            <FileText class="w-8 h-8 opacity-80" />
            <span class="text-4xl font-bold">{{ stats.requirement_count }}</span>
          </div>
          <div class="text-sm opacity-90">功能点</div>
        </div>

        <!-- 测试用例 -->
        <div class="bg-gradient-to-br from-green-500 to-green-600 rounded-xl p-6 text-white shadow-lg hover:shadow-xl transition-shadow">
          <div class="flex items-center justify-between mb-2">
            <CheckSquare class="w-8 h-8 opacity-80" />
            <span class="text-4xl font-bold">{{ stats.testcase_count }}</span>
          </div>
          <div class="text-sm opacity-90">测试用例</div>
        </div>

        <!-- 测试计划 -->
        <div class="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl p-6 text-white shadow-lg hover:shadow-xl transition-shadow">
          <div class="flex items-center justify-between mb-2">
            <BarChart3 class="w-8 h-8 opacity-80" />
            <span class="text-4xl font-bold">{{ stats.testplan_count }}</span>
          </div>
          <div class="text-sm opacity-90">测试计划</div>
        </div>

        <!-- 测试报告 -->
        <div class="bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl p-6 text-white shadow-lg hover:shadow-xl transition-shadow">
          <div class="flex items-center justify-between mb-2">
            <FileCheck class="w-8 h-8 opacity-80" />
            <span class="text-4xl font-bold">{{ stats.report_count }}</span>
          </div>
          <div class="text-sm opacity-90">测试报告</div>
        </div>
      </div>

      <!-- Tab 切换 -->
      <DetailCard title="版本内容" :icon="GitBranch">
        <div class="flex border-b border-gray-100 mb-4">
          <button
            v-for="tab in ['overview', 'requirements', 'testcases', 'plans', 'reports', 'changelog']"
            :key="tab"
            :class="[
              'px-6 py-3 text-sm font-medium transition-all',
              activeTab === tab 
                ? 'text-primary border-b-2 border-primary bg-blue-50/50' 
                : 'text-text-secondary hover:text-text-primary hover:bg-gray-50'
            ]"
            @click="activeTab = tab"
          >
            {{ { overview: '概览', requirements: '功能点', testcases: '测试用例', plans: '测试计划', reports: '测试报告', changelog: '变更日志' }[tab] }}
          </button>
        </div>

        <div v-if="activeTab === 'overview'" class="text-center py-12">
          <BarChart3 class="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p class="text-text-secondary">概览信息展示区域</p>
          <p class="text-sm text-text-placeholder mt-2">可以展示版本相关的趋势图表和统计数据</p>
        </div>
        
        <div v-else-if="activeTab === 'requirements'" class="text-center py-12">
          <FileText class="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p class="text-text-secondary">功能点列表</p>
          <p class="text-sm text-text-placeholder mt-2">展示该版本关联的功能点</p>
        </div>
        
        <div v-else-if="activeTab === 'testcases'" class="text-center py-12">
          <CheckSquare class="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p class="text-text-secondary">测试用例列表</p>
          <p class="text-sm text-text-placeholder mt-2">展示该版本关联的测试用例</p>
        </div>
        
        <div v-else-if="activeTab === 'plans'" class="text-center py-12">
          <BarChart3 class="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p class="text-text-secondary">测试计划列表</p>
          <p class="text-sm text-text-placeholder mt-2">展示该版本关联的测试计划</p>
        </div>
        
        <div v-else-if="activeTab === 'reports'" class="text-center py-12">
          <FileCheck class="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p class="text-text-secondary">测试报告列表</p>
          <p class="text-sm text-text-placeholder mt-2">展示该版本关联的测试报告</p>
        </div>
        
        <div v-else-if="activeTab === 'changelog'" class="text-center py-12">
          <GitBranch class="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p class="text-text-secondary">变更日志</p>
          <p class="text-sm text-text-placeholder mt-2">展示该版本的变更历史记录</p>
        </div>
      </DetailCard>
    </template>

    <div v-else class="text-center py-20">
      <GitBranch class="w-16 h-16 text-gray-300 mx-auto mb-4" />
      <p class="text-text-secondary text-lg">版本不存在</p>
    </div>
  </div>
</template>
