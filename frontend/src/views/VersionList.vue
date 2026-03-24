<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Search, Edit, Trash, GitCompare, Archive, Rocket } from 'lucide-vue-next'
import { ElMessage, ElMessageBox } from 'element-plus'
import useVersionStore from '@/stores/version'
import useProjectStore from '@/stores/project'
import type { ProjectVersion } from '@/types/version'

const router = useRouter()
const versionStore = useVersionStore()
const projectStore = useProjectStore()

const searchKeyword = ref('')
const statusFilter = ref('')
const projectFilter = ref<number | null>(null)
const dialogVisible = ref(false)
const dialogTitle = ref('新建版本')
const editingId = ref<number | null>(null)
const versionForm = ref({
  project_id: null as number | null,
  version_number: '',
  version_name: '',
  description: '',
  status: '开发中',
})

const statusOptions = ['开发中', '测试中', '已发布', '已归档']

onMounted(async () => {
  await projectStore.fetchProjects({ page_size: 100 })
  await loadVersions()
})

const loadVersions = () => {
  versionStore.fetchVersions({
    project_id: projectFilter.value || undefined,
    status: statusFilter.value || undefined,
  })
}

const handleSearch = () => {
  loadVersions()
}

const handleCreate = () => {
  dialogTitle.value = '新建版本'
  editingId.value = null
  versionForm.value = {
    project_id: null,
    version_number: '',
    version_name: '',
    description: '',
    status: '开发中',
  }
  dialogVisible.value = true
}

const handleEdit = (version: ProjectVersion) => {
  dialogTitle.value = '编辑版本'
  editingId.value = version.id
  versionForm.value = {
    project_id: version.project_id,
    version_number: version.version_number,
    version_name: version.version_name || '',
    description: version.description || '',
    status: version.status,
  }
  dialogVisible.value = true
}

const handleDelete = async (version: ProjectVersion) => {
  try {
    await ElMessageBox.confirm(`确定删除版本「${version.version_number}」吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await versionStore.deleteVersion(version.id)
    ElMessage.success('删除成功')
  } catch (e) {
    // 取消删除
  }
}

const handleRelease = async (version: ProjectVersion) => {
  try {
    await ElMessageBox.confirm(`确定发布版本「${version.version_number}」吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'info',
    })
    await versionStore.releaseVersion(version.id)
    ElMessage.success('发布成功')
  } catch (e) {
    // 取消
  }
}

const handleArchive = async (version: ProjectVersion) => {
  try {
    await ElMessageBox.confirm(`确定归档版本「${version.version_number}」吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await versionStore.archiveVersion(version.id)
    ElMessage.success('归档成功')
  } catch (e) {
    // 取消
  }
}

const handleCompare = () => {
  router.push('/versions/compare')
}

const handleSubmit = async () => {
  if (!versionForm.value.project_id) {
    ElMessage.warning('请选择项目')
    return
  }
  if (!versionForm.value.version_number) {
    ElMessage.warning('请输入版本号')
    return
  }
  
  try {
    if (editingId.value) {
      await versionStore.updateVersion(editingId.value, versionForm.value)
      ElMessage.success('更新成功')
    } else {
      await versionStore.createVersion(versionForm.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
  } catch (e) {
    ElMessage.error(editingId.value ? '更新失败' : '创建失败')
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

const getProjectName = (projectId: number) => {
  const project = projectStore.projects.find(p => p.id === projectId)
  return project?.name || '未知项目'
}
</script>

<template>
  <div class="version-list-page">
    <!-- 页面标题 -->
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-semibold text-text-primary">版本管理</h1>
      <div class="flex gap-2">
        <button @click="handleCompare" class="btn-secondary flex items-center gap-2">
          <GitCompare class="w-4 h-4" />
          版本对比
        </button>
        <button @click="handleCreate" class="btn-primary flex items-center gap-2">
          <Plus class="w-4 h-4" />
          新建版本
        </button>
      </div>
    </div>

    <!-- 筛选区域 -->
    <div class="card mb-6">
      <div class="flex items-center gap-4">
        <div class="w-48">
          <select v-model="projectFilter" @change="loadVersions" class="input-field">
            <option :value="null">全部项目</option>
            <option v-for="project in projectStore.projects" :key="project.id" :value="project.id">
              {{ project.name }}
            </option>
          </select>
        </div>
        <div class="w-32">
          <select v-model="statusFilter" @change="loadVersions" class="input-field">
            <option value="">全部状态</option>
            <option v-for="status in statusOptions" :key="status" :value="status">{{ status }}</option>
          </select>
        </div>
        <div class="flex-1 relative">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-placeholder" />
          <input
            v-model="searchKeyword"
            type="text"
            placeholder="搜索版本号..."
            class="input-field pl-10"
            @keyup.enter="handleSearch"
          />
        </div>
        <button @click="handleSearch" class="btn-primary">搜索</button>
      </div>
    </div>

    <!-- 版本列表 -->
    <div v-if="versionStore.loading" class="text-center py-10">
      <span class="text-text-secondary">加载中...</span>
    </div>
    
    <div v-else-if="versionStore.versions.length === 0" class="card text-center py-10">
      <span class="text-text-secondary">暂无版本，点击「新建版本」开始创建</span>
    </div>
    
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="version in versionStore.versions"
        :key="version.id"
        class="card hover:shadow-md transition-shadow cursor-pointer group"
        @click="router.push(`/versions/${version.id}`)"
      >
        <div class="flex items-start justify-between mb-2">
          <div>
            <div class="flex items-center gap-2 mb-1">
              <h3 class="text-lg font-medium text-text-primary">{{ version.version_number }}</h3>
              <span :class="['px-2 py-0.5 rounded text-xs', getStatusColor(version.status)]">
                {{ version.status }}
              </span>
              <span v-if="version.is_baseline" class="px-2 py-0.5 rounded text-xs bg-purple-100 text-purple-700">
                基线
              </span>
            </div>
            <p class="text-xs text-text-placeholder">{{ getProjectName(version.project_id) }}</p>
          </div>
          <div class="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity" @click.stop>
            <button
              v-if="version.status === '测试中'"
              @click="handleRelease(version)"
              class="p-1.5 rounded hover:bg-green-50 transition-colors"
              title="发布"
            >
              <Rocket class="w-4 h-4 text-green-600" />
            </button>
            <button
              v-if="version.status === '已发布'"
              @click="handleArchive(version)"
              class="p-1.5 rounded hover:bg-gray-100 transition-colors"
              title="归档"
            >
              <Archive class="w-4 h-4 text-gray-500" />
            </button>
            <button
              @click="handleEdit(version)"
              class="p-1.5 rounded hover:bg-background-secondary transition-colors"
            >
              <Edit class="w-4 h-4 text-text-secondary" />
            </button>
            <button
              @click="handleDelete(version)"
              class="p-1.5 rounded hover:bg-red-50 transition-colors"
            >
              <Trash class="w-4 h-4 text-functional-danger" />
            </button>
          </div>
        </div>
        <p class="text-sm text-text-secondary mb-3 line-clamp-2">
          {{ version.version_name || version.description || '暂无描述' }}
        </p>
        <div class="flex items-center justify-between text-xs text-text-placeholder">
          <span>{{ version.created_by || '系统' }}</span>
          <span>{{ version.released_at ? `发布于 ${new Date(version.released_at).toLocaleDateString()}` : new Date(version.created_at).toLocaleDateString() }}</span>
        </div>
      </div>
    </div>

    <!-- 新建/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
      <el-form :model="versionForm" label-width="80px">
        <el-form-item label="所属项目" required>
          <el-select v-model="versionForm.project_id" placeholder="请选择项目" :disabled="!!editingId">
            <el-option
              v-for="project in projectStore.projects"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="版本号" required>
          <el-input v-model="versionForm.version_number" placeholder="如: v1.0.0" />
        </el-form-item>
        <el-form-item label="版本名称">
          <el-input v-model="versionForm.version_name" placeholder="版本名称" />
        </el-form-item>
        <el-form-item label="版本描述">
          <el-input
            v-model="versionForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入版本描述"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="versionForm.status">
            <el-option v-for="status in statusOptions" :key="status" :label="status" :value="status" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <button @click="dialogVisible = false" class="btn-secondary">取消</button>
        <button @click="handleSubmit" class="btn-primary ml-2">确定</button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
