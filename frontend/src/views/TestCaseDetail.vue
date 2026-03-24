<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Edit, Delete, Save, X, FileText, List } from 'lucide-vue-next'
import useTestcaseStore from '@/stores/testcase'
import useProjectStore from '@/stores/project'
import useRequirementStore from '@/stores/requirement'
import useVersionStore from '@/stores/version'
import type { TestCaseUpdate } from '@/types/testcase'
import DetailHeader from '@/components/detail/DetailHeader.vue'
import DetailCard from '@/components/detail/DetailCard.vue'
import EditableField from '@/components/detail/EditableField.vue'

const route = useRoute()
const router = useRouter()
const testcaseStore = useTestcaseStore()
const projectStore = useProjectStore()
const requirementStore = useRequirementStore()
const versionStore = useVersionStore()

const loading = ref(true)
const isEditing = ref(false)
const formData = ref<TestCaseUpdate>({})

// 当前测试用例
const testcase = computed(() => testcaseStore.currentTestcase)

// 所属项目
const project = computed(() => {
  if (!testcase.value) return null
  return projectStore.projects.find(p => p.id === testcase.value?.project_id)
})

// 关联需求
const requirement = computed(() => {
  if (!testcase.value?.requirement_id) return null
  return requirementStore.requirements.find(r => r.id === testcase.value?.requirement_id)
})

// 关联版本
const version = computed(() => {
  if (!testcase.value?.version_id) return null
  return versionStore.versions.find(v => v.id === testcase.value?.version_id)
})

// 优先级和状态选项
const priorities = ['高', '中', '低']
const statuses = ['未开始', '进行中', '已完成', '已阻塞']

// 加载数据
async function loadData() {
  const id = Number(route.params.id)
  if (!id) {
    ElMessage.error('测试用例ID无效')
    router.push('/testcases')
    return
  }

  loading.value = true
  try {
    await testcaseStore.fetchTestcase(id)
    await projectStore.fetchProjects({ page_size: 100 })
    await requirementStore.fetchRequirements({ page_size: 100 })
    await versionStore.fetchVersions({ page_size: 100 })
  } catch {
    ElMessage.error('加载测试用例失败')
    router.push('/testcases')
  } finally {
    loading.value = false
  }
}

// 开始编辑
function handleEdit() {
  if (!testcase.value) return
  isEditing.value = true
  formData.value = {
    title: testcase.value.title,
    description: testcase.value.description || '',
    priority: testcase.value.priority || '',
    status: testcase.value.status || '未开始',
    test_type: testcase.value.test_type || '',
    preconditions: testcase.value.preconditions || '',
    test_data: testcase.value.test_data || ''
  }
}

// 取消编辑
function handleCancel() {
  isEditing.value = false
  formData.value = {}
}

// 保存
async function handleSave() {
  if (!testcase.value) return
  
  try {
    await testcaseStore.updateTestcase(testcase.value.id, formData.value)
    ElMessage.success('保存成功')
    isEditing.value = false
    await loadData()
  } catch {
    ElMessage.error('保存失败')
  }
}

// 删除
async function handleDelete() {
  if (!testcase.value) return
  
  try {
    await ElMessageBox.confirm(
      `确定要删除测试用例「${testcase.value.title}」吗？`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await testcaseStore.deleteTestcase(testcase.value.id)
    ElMessage.success('删除成功')
    router.push('/testcases')
  } catch {
    // 用户取消
  }
}

// 返回列表
function handleBack() {
  router.push('/testcases')
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

// 获取状态样式
function getStatusClass(status: string) {
  switch (status) {
    case '已完成': return 'bg-green-100 text-green-700'
    case '进行中': return 'bg-blue-100 text-blue-700'
    case '已阻塞': return 'bg-red-100 text-red-700'
    case '未开始': return 'bg-gray-100 text-gray-700'
    default: return 'bg-gray-100 text-gray-700'
  }
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="testcase-detail-page p-6 max-w-6xl mx-auto">
    <!-- 加载中 -->
    <div v-if="loading" class="text-center py-20">
      <div class="inline-flex items-center gap-2 text-text-secondary">
        <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-primary" />
        <span>加载中...</span>
      </div>
    </div>

    <!-- 详情内容 -->
    <div v-else-if="testcase">
      <!-- Header -->
      <DetailHeader 
        :title="testcase.title"
        :subtitle="testcase.description || '暂无描述'"
        back-to="/testcases"
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
            label="用例标题" 
            v-model="formData.title"
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
            label="关联需求" 
            :model-value="requirement?.name"
            :editable="false"
          />
          <EditableField 
            label="所属版本" 
            :model-value="version?.version_name || version?.version_number"
            :editable="false"
          />
          <EditableField 
            label="优先级" 
            v-model="formData.priority"
            :editable="isEditing"
            type="select"
            :options="priorities.map(p => ({ label: p, value: p }))"
            placeholder="请选择优先级"
          />
          <EditableField 
            label="状态" 
            v-model="formData.status"
            :editable="isEditing"
            type="select"
            :options="statuses.map(s => ({ label: s, value: s }))"
            placeholder="请选择状态"
          />
          <EditableField 
            label="测试类型" 
            v-model="formData.test_type"
            :editable="isEditing"
            placeholder="请输入测试类型"
          />
          <EditableField 
            label="用例描述" 
            v-model="formData.description"
            :editable="isEditing"
            type="textarea"
            :span="2"
            :rows="4"
            placeholder="请输入用例描述"
          />
          <EditableField 
            label="前置条件" 
            v-model="formData.preconditions"
            :editable="isEditing"
            type="textarea"
            :span="2"
            :rows="3"
            placeholder="请输入前置条件"
          />
          <EditableField 
            label="测试数据" 
            v-model="formData.test_data"
            :editable="isEditing"
            type="textarea"
            :span="2"
            :rows="3"
            placeholder="请输入测试数据"
          />
          <EditableField 
            label="创建者" 
            :model-value="testcase.creator"
            :editable="false"
          />
          <EditableField 
            label="创建时间" 
            :model-value="testcase.created_at"
            type="date"
            :editable="false"
          />
          <EditableField 
            label="更新时间" 
            :model-value="testcase.updated_at"
            type="date"
            :editable="false"
          />
        </div>
      </DetailCard>

      <!-- 测试步骤 -->
      <DetailCard title="测试步骤" :icon="List">
        <div v-if="testcase.steps && testcase.steps.length > 0" class="space-y-3">
          <div
            v-for="step in testcase.steps"
            :key="step.id"
            class="bg-background-secondary rounded p-3"
          >
            <div class="flex items-start gap-3">
              <span
                class="flex-shrink-0 w-6 h-6 rounded-full bg-primary text-white flex items-center justify-center text-sm font-medium"
              >
                {{ step.step_number }}
              </span>
              <div class="flex-1">
                <p class="text-text-primary">{{ step.description }}</p>
                <p v-if="step.expected_result" class="text-sm text-text-secondary mt-1">
                  <span class="font-medium">预期结果：</span>{{ step.expected_result }}
                </p>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="text-center py-12">
          <List class="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p class="text-text-secondary">暂无测试步骤</p>
        </div>
      </DetailCard>
    </div>

    <!-- 未找到 -->
    <div v-else class="text-center py-20">
      <FileText class="w-16 h-16 text-gray-300 mx-auto mb-4" />
      <p class="text-text-secondary text-lg mb-4">测试用例不存在或已删除</p>
      <button class="btn-primary" @click="handleBack">返回列表</button>
    </div>
  </div>
</template>
