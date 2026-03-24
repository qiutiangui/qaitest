<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Search, Edit, Trash, Trash2, Database, FileText, TestTube, ClipboardList, FileBarChart, GitBranch, Layers, ChevronRight } from 'lucide-vue-next'
import { ElMessage, ElMessageBox } from 'element-plus'
import useProjectStore from '@/stores/project'
import type { Project } from '@/types/project'
import ragApi from '@/api/rag'

interface ProjectStats {
  version_count: number
  requirement_count: number
  requirement_group_count: number
  testcase_count: number
  testplan_count: number
}

const router = useRouter()
const projectStore = useProjectStore()

const searchKeyword = ref('')
const dialogVisible = ref(false)
const dialogTitle = ref('新建项目')
const editingId = ref<number | null>(null)
const projectForm = ref({
  name: '',
  description: '',
  status: '活跃',
})

// RAG索引状态
const ragStats = ref<Record<number, { exists: boolean; count: number }>>({})

// 项目统计数据
const projectStats = ref<Record<number, ProjectStats>>({})

onMounted(async () => {
  await projectStore.fetchProjects()
  // 加载所有项目的索引状态和统计数据
  loadAllRAGStats()
  loadAllProjectStats()
})

// 加载所有项目的索引状态
const loadAllRAGStats = async () => {
  for (const project of projectStore.projects) {
    try {
      const res = await ragApi.getRAGStats(project.id)
      ragStats.value[project.id] = res.data as { exists: boolean; count: number }
    } catch (e) {
      ragStats.value[project.id] = { exists: false, count: 0 }
    }
  }
}

// 加载所有项目的统计数据
const loadAllProjectStats = async () => {
  for (const project of projectStore.projects) {
    try {
      const response = await fetch(`/api/projects/${project.id}/stats`)
      const stats = await response.json()
      projectStats.value[project.id] = {
        version_count: stats.version_count || 0,
        requirement_count: stats.requirement_count || 0,
        requirement_group_count: stats.requirement_group_count || 0,
        testcase_count: stats.testcase_count || 0,
        testplan_count: stats.testplan_count || 0
      }
    } catch (e) {
      projectStats.value[project.id] = {
        version_count: 0,
        requirement_count: 0,
        requirement_group_count: 0,
        testcase_count: 0,
        testplan_count: 0
      }
    }
  }
}

// 获取项目索引状态
const getIndexStatus = (projectId: number) => {
  return ragStats.value[projectId]
}

// 删除索引
const handleDeleteIndex = async (project: Project) => {
  try {
    await ElMessageBox.confirm(
      `确定删除项目「${project.name}」的向量数据吗？\n删除后需重新上传需求文档才能使用 RAG 增强功能。`,
      '删除向量数据',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    await ragApi.deleteRAGIndex(project.id)
    ragStats.value[project.id] = { exists: false, count: 0 }
    ElMessage.success('向量数据已删除')
  } catch (e) {
    // 取消删除
  }
}

const handleSearch = () => {
  projectStore.fetchProjects({ keyword: searchKeyword.value })
}

const handleCreate = () => {
  dialogTitle.value = '新建项目'
  editingId.value = null
  projectForm.value = { name: '', description: '', status: '活跃' }
  dialogVisible.value = true
}

const handleEdit = (project: Project) => {
  dialogTitle.value = '编辑项目'
  editingId.value = project.id
  projectForm.value = {
    name: project.name,
    description: project.description || '',
    status: project.status,
  }
  dialogVisible.value = true
}

const handleDelete = async (project: Project) => {
  try {
    await ElMessageBox.confirm(`确定删除项目「${project.name}」吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await projectStore.deleteProject(project.id)
    ElMessage.success('删除成功')
  } catch (e) {
    // 取消删除
  }
}

const handleSubmit = async () => {
  if (!projectForm.value.name) {
    ElMessage.warning('请输入项目名称')
    return
  }
  
  try {
    if (editingId.value) {
      await projectStore.updateProject(editingId.value, projectForm.value)
      ElMessage.success('更新成功')
    } else {
      await projectStore.createProject(projectForm.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
  } catch (e) {
    ElMessage.error(editingId.value ? '更新失败' : '创建失败')
  }
}

// 快捷操作
const handleQuickAction = (action: string, project: Project, event?: Event) => {
  if (event) event.stopPropagation()
  switch (action) {
    case 'requirement':
      router.push(`/requirements/analysis?project_id=${project.id}`)
      break
    case 'testcase':
      router.push(`/testcases/generate?project_id=${project.id}`)
      break
    case 'testplan':
      router.push(`/testplans?project_id=${project.id}`)
      break
    case 'report':
      router.push(`/testreports?project_id=${project.id}`)
      break
    case 'detail':
      router.push(`/projects/${project.id}`)
      break
  }
}

const handleCardClick = (project: Project) => {
  router.push(`/requirements/analysis?project_id=${project.id}`)
}
</script>

<template>
  <div class="project-list-page">
    <!-- 页面标题 -->
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-semibold text-text-primary">项目管理</h1>
      <button @click="handleCreate" class="btn-primary flex items-center gap-2">
        <Plus class="w-4 h-4" />
        新建项目
      </button>
    </div>

    <!-- 搜索区域 -->
    <div class="card mb-6">
      <div class="flex items-center gap-4">
        <div class="flex-1 relative">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-placeholder" />
          <input
            v-model="searchKeyword"
            type="text"
            placeholder="搜索项目名称..."
            class="input-field pl-10"
            @keyup.enter="handleSearch"
          />
        </div>
        <button @click="handleSearch" class="btn-primary">搜索</button>
      </div>
    </div>

    <!-- 项目列表 -->
    <div v-if="projectStore.loading" class="text-center py-10">
      <span class="text-text-secondary">加载中...</span>
    </div>
    
    <div v-else-if="projectStore.projects.length === 0" class="card text-center py-10">
      <span class="text-text-secondary">暂无项目，点击「新建项目」开始创建</span>
    </div>
    
    <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div
        v-for="project in projectStore.projects"
        :key="project.id"
        class="card hover:shadow-lg transition-all duration-200 cursor-pointer group border border-transparent hover:border-primary/20"
        @click="handleCardClick(project)"
      >
        <!-- 头部：项目名称和操作按钮 -->
        <div class="flex items-start justify-between mb-4">
          <div class="flex-1">
            <h3 class="text-lg font-semibold text-text-primary mb-1">{{ project.name }}</h3>
            <p class="text-sm text-text-secondary line-clamp-2">
              {{ project.description || '暂无描述' }}
            </p>
          </div>
          <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity" @click.stop>
            <button
              @click="handleEdit(project)"
              class="p-1.5 rounded hover:bg-gray-100 transition-colors"
              title="编辑"
            >
              <Edit class="w-4 h-4 text-text-secondary" />
            </button>
            <button
              @click="handleDelete(project)"
              class="p-1.5 rounded hover:bg-red-50 transition-colors"
              title="删除"
            >
              <Trash class="w-4 h-4 text-functional-danger" />
            </button>
          </div>
        </div>

        <!-- 统计数据区域 -->
        <div class="grid grid-cols-5 gap-2 mb-4 p-3 bg-gray-50 rounded-lg">
          <div class="text-center">
            <div class="flex items-center justify-center mb-1">
              <GitBranch class="w-4 h-4 text-primary" />
            </div>
            <div class="text-lg font-semibold text-text-primary">{{ projectStats[project.id]?.version_count || 0 }}</div>
            <div class="text-xs text-text-secondary">版本</div>
          </div>
          <div class="text-center">
            <div class="flex items-center justify-center mb-1">
              <Layers class="w-4 h-4 text-green-600" />
            </div>
            <div class="text-lg font-semibold text-text-primary">{{ projectStats[project.id]?.requirement_group_count || 0 }}</div>
            <div class="text-xs text-text-secondary">需求</div>
          </div>
          <div class="text-center">
            <div class="flex items-center justify-center mb-1">
              <FileText class="w-4 h-4 text-orange-500" />
            </div>
            <div class="text-lg font-semibold text-text-primary">{{ projectStats[project.id]?.requirement_count || 0 }}</div>
            <div class="text-xs text-text-secondary">功能点</div>
          </div>
          <div class="text-center">
            <div class="flex items-center justify-center mb-1">
              <TestTube class="w-4 h-4 text-blue-500" />
            </div>
            <div class="text-lg font-semibold text-text-primary">{{ projectStats[project.id]?.testcase_count || 0 }}</div>
            <div class="text-xs text-text-secondary">用例</div>
          </div>
          <div class="text-center">
            <div class="flex items-center justify-center mb-1">
              <ClipboardList class="w-4 h-4 text-purple-500" />
            </div>
            <div class="text-lg font-semibold text-text-primary">{{ projectStats[project.id]?.testplan_count || 0 }}</div>
            <div class="text-xs text-text-secondary">计划</div>
          </div>
        </div>

        <!-- 向量数据状态 -->
        <div class="flex items-center justify-between mb-4 px-1">
          <div class="flex items-center gap-2">
            <Database class="w-3.5 h-3.5 text-text-secondary" />
            <span v-if="getIndexStatus(project.id)?.exists" class="text-xs text-green-600">
              向量数据 ({{ getIndexStatus(project.id)?.count || 0 }} 条)
            </span>
            <span v-else class="text-xs text-text-placeholder">
              暂无向量数据
            </span>
          </div>
          <button
            v-if="getIndexStatus(project.id)?.exists"
            @click.stop="handleDeleteIndex(project)"
            class="text-xs text-red-500 hover:text-red-600 transition-colors opacity-0 group-hover:opacity-100"
          >
            删除向量
          </button>
        </div>

        <!-- 底部：状态和快捷入口 -->
        <div class="flex items-center justify-between pt-3 border-t border-gray-100">
          <div class="flex items-center gap-2">
            <span
              :class="[
                'px-2 py-0.5 rounded text-xs',
                project.status === '活跃' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
              ]"
            >
              {{ project.status }}
            </span>
            <span class="text-xs text-text-placeholder">
              {{ new Date(project.created_at).toLocaleDateString() }}
            </span>
          </div>
          
          <!-- 快捷入口按钮 -->
          <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity" @click.stop>
            <button
              @click="handleQuickAction('requirement', project, $event)"
              class="px-2 py-1 text-xs text-primary hover:bg-primary/10 rounded transition-colors"
            >
              AI需求分析
            </button>
            <button
              @click="handleQuickAction('testcase', project, $event)"
              class="px-2 py-1 text-xs text-primary hover:bg-primary/10 rounded transition-colors"
            >
              AI用例生成
            </button>
            <button
              @click="handleQuickAction('testplan', project, $event)"
              class="px-2 py-1 text-xs text-text-secondary hover:bg-gray-100 rounded transition-colors"
            >
              测试计划
            </button>
            <button
              @click="handleQuickAction('report', project, $event)"
              class="px-2 py-1 text-xs text-text-secondary hover:bg-gray-100 rounded transition-colors"
            >
              报告
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 新建/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
      <el-form :model="projectForm" label-width="80px">
        <el-form-item label="项目名称" required>
          <el-input v-model="projectForm.name" placeholder="请输入项目名称" />
        </el-form-item>
        <el-form-item label="项目描述">
          <el-input
            v-model="projectForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入项目描述"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="projectForm.status">
            <el-option label="活跃" value="活跃" />
            <el-option label="归档" value="归档" />
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
