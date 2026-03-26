<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Edit, Delete, Save, X, FileText, CheckSquare, ArrowRight } from 'lucide-vue-next'
import useRequirementStore from '@/stores/requirement'
import useProjectStore from '@/stores/project'
import useVersionStore from '@/stores/version'
import type { RequirementUpdate } from '@/types/requirement'
import { testcaseApi } from '@/api/testcase'
import type { TestCase, TestCaseListResponse } from '@/types/testcase'
import DetailHeader from '@/components/detail/DetailHeader.vue'
import DetailCard from '@/components/detail/DetailCard.vue'
import EditableField from '@/components/detail/EditableField.vue'
import StatusBadge from '@/components/detail/StatusBadge.vue'

const route = useRoute()
const router = useRouter()
const requirementStore = useRequirementStore()
const projectStore = useProjectStore()
const versionStore = useVersionStore()

const loading = ref(true)
const isEditing = ref(false)
const formData = ref<RequirementUpdate>({})
const relatedTestCases = ref<TestCase[]>([])
const testCasesLoading = ref(false)
const testCasesTotal = ref(0)

// 当前功能点
const requirement = computed(() => requirementStore.currentRequirement)

// 所属项目
const project = computed(() => {
  if (!requirement.value) return null
  return projectStore.projects.find(p => p.id === requirement.value?.project_id)
})

// 所属版本
const version = computed(() => {
  if (!requirement.value?.version_id) return null
  return versionStore.versions.find(v => v.id === requirement.value?.version_id)
})

// 类别和优先级选项
const categoryOptions = ['功能需求', '非功能需求', '界面需求', '数据需求', '安全需求', '性能需求']
const priorityOptions = ['高', '中', '低']

// 加载数据
async function loadData() {
  const id = Number(route.params.id)
  if (!id) {
    ElMessage.error('功能点ID无效')
    router.push('/requirements')
    return
  }

  loading.value = true
  try {
    await requirementStore.fetchRequirement(id)
    await projectStore.fetchProjects({ page_size: 100 })
    await versionStore.fetchVersions({ page_size: 100 })
    await fetchRelatedTestCases()
  } catch {
    ElMessage.error('加载功能点失败')
    router.push('/requirements')
  } finally {
    loading.value = false
  }
}

// 开始编辑
function handleEdit() {
  if (!requirement.value) return
  isEditing.value = true
  formData.value = {
    name: requirement.value.name,
    description: requirement.value.description || '',
    category: requirement.value.category || '',
    module: requirement.value.module || '',
    priority: requirement.value.priority || '',
    acceptance_criteria: requirement.value.acceptance_criteria || '',
    keywords: requirement.value.keywords || ''
  }
}

// 取消编辑
function handleCancel() {
  isEditing.value = false
  formData.value = {}
}

// 保存
async function handleSave() {
  if (!requirement.value) return
  
  try {
    await requirementStore.updateRequirement(requirement.value.id, formData.value)
    ElMessage.success('保存成功')
    isEditing.value = false
    await loadData()
  } catch {
    ElMessage.error('保存失败')
  }
}

// 删除
async function handleDelete() {
  if (!requirement.value) return
  
  try {
    await ElMessageBox.confirm(
      `确定要删除功能点「${requirement.value.name}」吗？`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await requirementStore.deleteRequirement(requirement.value.id)
    ElMessage.success('删除成功')
    router.push('/requirements')
  } catch {
    // 用户取消
  }
}

// 返回列表
function handleBack() {
  router.push('/requirements')
}

// 格式化日期
function formatDate(date: string | null) {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN')
}

// 获取优先级样式
function getPriorityClass(priority: string | null) {
  if (!priority) return ''
  switch (priority) {
    case '高': return 'bg-red-100 text-red-700'
    case '中': return 'bg-orange-100 text-orange-700'
    case '低': return 'bg-green-100 text-green-700'
    default: return 'bg-gray-100 text-gray-700'
  }
}

// 获取关联的测试用例
async function fetchRelatedTestCases() {
  if (!requirement.value?.id) return
  
  testCasesLoading.value = true
  try {
    const res: TestCaseListResponse = await testcaseApi.list({
      requirement_id: requirement.value.id,
      page_size: 100
    })
    relatedTestCases.value = res.items
    testCasesTotal.value = res.total
  } catch {
    // 静默处理
  } finally {
    testCasesLoading.value = false
  }
}

// 跳转到测试用例详情
function goToTestCase(testcase: TestCase) {
  router.push(`/testcases/${testcase.id}`)
}

// 获取状态样式
function getStatusClass(status: string | null) {
  if (!status) return 'bg-gray-100 text-gray-700'
  switch (status) {
    case '已通过': return 'bg-green-100 text-green-700'
    case '未通过': return 'bg-red-100 text-red-700'
    case '待执行': return 'bg-yellow-100 text-yellow-700'
    case '执行中': return 'bg-blue-100 text-blue-700'
    case '未开始': return 'bg-gray-100 text-gray-700'
    default: return 'bg-gray-100 text-gray-700'
  }
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="requirement-detail-page p-6 max-w-6xl mx-auto">
    <!-- 加载中 -->
    <div v-if="loading" class="text-center py-20">
      <div class="inline-flex items-center gap-2 text-text-secondary">
        <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-primary" />
        <span>加载中...</span>
      </div>
    </div>

    <!-- 详情内容 -->
    <div v-else-if="requirement">
      <!-- Header -->
      <DetailHeader 
        :title="requirement.name"
        :subtitle="requirement.description || '暂无描述'"
        back-to="/requirements"
        :breadcrumb="[project?.name || '未知项目']"
      >
        <template #actions>
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
          </template>
        </template>
      </DetailHeader>

      <!-- 基本信息 -->
      <DetailCard title="基本信息" :icon="FileText" class="mb-6">
        <div class="grid grid-cols-2 gap-6">
          <EditableField 
            label="功能点名称" 
            :model-value="isEditing ? formData.name : requirement?.name"
            @update:model-value="formData.name = $event"
            :editable="isEditing"
            required
            :span="2"
          />
          <EditableField 
            label="所属项目" 
            :model-value="project?.name"
            :editable="false"
          />
          <EditableField 
            label="所属版本" 
            :model-value="version?.version_name || version?.version_number"
            :editable="false"
          />
          <EditableField 
            label="所属模块" 
            :model-value="isEditing ? formData.module : requirement?.module"
            @update:model-value="formData.module = $event"
            :editable="isEditing"
            placeholder="请输入所属模块"
          />
          <EditableField 
            label="类别" 
            :model-value="isEditing ? formData.category : requirement?.category"
            @update:model-value="formData.category = $event"
            :editable="isEditing"
            type="select"
            :options="categoryOptions.map(c => ({ label: c, value: c }))"
            placeholder="请选择类别"
          />
          <EditableField 
            label="优先级" 
            :model-value="isEditing ? formData.priority : requirement?.priority"
            @update:model-value="formData.priority = $event"
            :editable="isEditing"
            type="select"
            :options="priorityOptions.map(p => ({ label: p, value: p }))"
            placeholder="请选择优先级"
          />
          <EditableField 
            label="功能点描述" 
            :model-value="isEditing ? formData.description : requirement?.description"
            @update:model-value="formData.description = $event"
            :editable="isEditing"
            type="textarea"
            :span="2"
            :rows="4"
            placeholder="请输入功能点描述"
          />
          <EditableField 
            label="验收标准" 
            :model-value="isEditing ? formData.acceptance_criteria : requirement?.acceptance_criteria"
            @update:model-value="formData.acceptance_criteria = $event"
            :editable="isEditing"
            type="textarea"
            :span="2"
            :rows="3"
            placeholder="请输入验收标准"
          />
          <EditableField 
            label="关键词" 
            :model-value="isEditing ? formData.keywords : requirement?.keywords"
            @update:model-value="formData.keywords = $event"
            :editable="isEditing"
            placeholder="多个关键词用逗号分隔"
          />
          <EditableField 
            label="创建时间" 
            :model-value="requirement.created_at"
            type="date"
            :editable="false"
          />
          <EditableField 
            label="更新时间" 
            :model-value="requirement.updated_at"
            type="date"
            :editable="false"
          />
        </div>
      </DetailCard>

      <!-- 关联测试用例 -->
      <DetailCard title="关联测试用例" :icon="CheckSquare">
        <!-- 加载状态 -->
        <div v-if="testCasesLoading" class="text-center py-12">
          <div class="inline-flex items-center gap-2 text-text-secondary">
            <div class="animate-spin rounded-full h-5 w-5 border-b-2 border-primary" />
            <span>加载测试用例...</span>
          </div>
        </div>
        
        <!-- 空状态 -->
        <div v-else-if="relatedTestCases.length === 0" class="text-center py-12">
          <CheckSquare class="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p class="text-text-secondary mb-4">暂无关联的测试用例</p>
        </div>
        
        <!-- 测试用例列表 -->
        <div v-else class="space-y-3">
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm text-text-secondary">共 {{ testCasesTotal }} 个测试用例</span>
          </div>
          <div 
            v-for="testcase in relatedTestCases" 
            :key="testcase.id"
            class="p-4 border border-gray-200 rounded-lg hover:border-primary/50 hover:bg-primary/5 cursor-pointer transition-all group"
            @click="goToTestCase(testcase)"
          >
            <div class="flex items-center justify-between">
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-1">
                  <h4 class="font-medium text-gray-900 truncate">{{ testcase.title }}</h4>
                </div>
                <div class="flex items-center gap-3 text-sm text-text-secondary">
                  <span v-if="testcase.test_type" class="px-2 py-0.5 bg-gray-100 rounded text-xs">
                    {{ testcase.test_type }}
                  </span>
                  <span v-if="testcase.priority" class="px-2 py-0.5 rounded text-xs" :class="getPriorityClass(testcase.priority)">
                    {{ testcase.priority }}
                  </span>
                  <span class="px-2 py-0.5 rounded text-xs" :class="getStatusClass(testcase.status)">
                    {{ testcase.status || '未开始' }}
                  </span>
                  <span v-if="testcase.creator" class="text-xs">
                    创建者: {{ testcase.creator }}
                  </span>
                </div>
              </div>
              <ArrowRight class="w-5 h-5 text-gray-400 group-hover:text-primary transition-colors" />
            </div>
          </div>
        </div>
      </DetailCard>
    </div>

    <!-- 未找到 -->
    <div v-else class="text-center py-20">
      <FileText class="w-16 h-16 text-gray-300 mx-auto mb-4" />
      <p class="text-text-secondary text-lg mb-4">功能点不存在或已删除</p>
      <button class="btn-primary" @click="handleBack">返回列表</button>
    </div>
  </div>
</template>
