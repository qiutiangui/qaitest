<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Download, Search, Eye, Trash2, Edit, FileSpreadsheet, FileText } from 'lucide-vue-next'
import { ElMessage } from 'element-plus'
import useTestcaseStore from '@/stores/testcase'
import useProjectStore from '@/stores/project'
import testcaseApi from '@/api/testcase'
import type { TestCaseUpdate } from '@/types/testcase'
import { formatDateTime } from '@/utils/date'

const router = useRouter()
const testcaseStore = useTestcaseStore()
const projectStore = useProjectStore()

// 筛选条件
const selectedProject = ref<number | undefined>()
const selectedPriority = ref<string | undefined>()
const selectedStatus = ref<string | undefined>()
const searchKeyword = ref('')

// 分页
const currentPage = ref(1)
const pageSize = ref(10)

// 编辑弹窗
const editDialogVisible = ref(false)
const editingTestcase = ref<any>(null)
const editForm = ref<TestCaseUpdate>({})

// 导出格式选择
const showExportDialog = ref(false)
const exportFormat = ref<'excel' | 'markdown'>('excel')
const exporting = ref(false)

// 优先级选项
const priorities = ['高', '中', '低']

// 状态选项
const statuses = ['未开始', '进行中', '已完成', '已阻塞']

// 计算总页数
const totalPages = computed(() => Math.ceil(testcaseStore.total / pageSize.value))

// 获取用例列表
async function fetchList() {
  await testcaseStore.fetchTestcases({
    page: currentPage.value,
    page_size: pageSize.value,
    project_id: selectedProject.value,
    priority: selectedPriority.value,
    status: selectedStatus.value,
    keyword: searchKeyword.value || undefined,
  })
}

// 搜索
function handleSearch() {
  currentPage.value = 1
  fetchList()
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

// 查看详情
function viewDetail(id: number) {
  router.push(`/testcases/${id}`)
}

// 删除用例
async function deleteTestcase(id: number) {
  if (confirm('确定要删除这个测试用例吗？')) {
    await testcaseStore.deleteTestcase(id)
    fetchList()
  }
}

// 编辑用例
function handleEdit(testcase: any) {
  editingTestcase.value = testcase
  editForm.value = {
    title: testcase.title,
    description: testcase.description || '',
    priority: testcase.priority || '',
    status: testcase.status || '未开始',
    test_type: testcase.test_type || '',
    preconditions: testcase.preconditions || '',
    test_data: testcase.test_data || ''
  }
  editDialogVisible.value = true
}

// 保存编辑
async function handleSaveEdit() {
  if (!editingTestcase.value) return
  
  if (!editForm.value.title) {
    ElMessage.warning('请输入用例标题')
    return
  }
  
  try {
    await testcaseApi.update(editingTestcase.value.id, editForm.value)
    ElMessage.success('更新成功')
    editDialogVisible.value = false
    fetchList()
  } catch (error) {
    ElMessage.error('更新失败')
  }
}

// 导出用例
async function handleExport() {
  if (!selectedProject.value) {
    alert('请先选择项目')
    return
  }
  
  exporting.value = true
  try {
    const result = await testcaseApi.export(selectedProject.value, exportFormat.value)
    
    if (exportFormat.value === 'markdown') {
      // 下载Markdown文件
      const blob = new Blob([result.content!], { type: 'text/markdown' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `测试用例_${new Date().toISOString().slice(0, 10)}.md`
      a.click()
      URL.revokeObjectURL(url)
    } else {
      // 导出Excel - 使用简单的CSV格式
      const data = result.data!
      if (data.length === 0) {
        alert('没有可导出的数据')
        return
      }
      
      // 生成CSV内容
      const headers = Object.keys(data[0])
      const csvContent = [
        headers.join(','),
        ...data.map(row => headers.map(h => `"${row[h] || ''}"`).join(','))
      ].join('\n')
      
      // 下载CSV文件
      const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `测试用例_${new Date().toISOString().slice(0, 10)}.csv`
      a.click()
      URL.revokeObjectURL(url)
    }
    
    showExportDialog.value = false
  } catch (error) {
    console.error('导出失败:', error)
    alert('导出失败')
  } finally {
    exporting.value = false
  }
}

onMounted(async () => {
  await projectStore.fetchProjects({ page_size: 100 })
  fetchList()
})
</script>

<template>
  <div class="testcase-list-page">
    <!-- 页面标题 -->
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-semibold text-text-primary">用例管理</h1>
      <button
        class="btn-secondary flex items-center gap-2"
        @click="showExportDialog = true"
      >
        <Download class="w-4 h-4" />
        导出
      </button>
    </div>

    <!-- 筛选和搜索区域 -->
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

        <!-- 优先级筛选 -->
        <div class="flex items-center gap-2">
          <label class="text-sm text-text-secondary">优先级：</label>
          <select
            v-model="selectedPriority"
            class="input-field w-32"
            @change="handleFilterChange"
          >
            <option :value="undefined">全部</option>
            <option v-for="p in priorities" :key="p" :value="p">{{ p }}</option>
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

        <!-- 搜索框 -->
        <div class="flex-1 flex items-center gap-2 min-w-64">
          <input
            v-model="searchKeyword"
            type="text"
            placeholder="搜索用例标题..."
            class="input-field flex-1"
            @keyup.enter="handleSearch"
          />
          <button class="btn-primary flex items-center gap-2" @click="handleSearch">
            <Search class="w-4 h-4" />
            搜索
          </button>
        </div>
      </div>
    </div>

    <!-- 用例列表表格 -->
    <div class="card overflow-x-auto">
      <table class="w-full">
        <thead>
          <tr class="border-b border-gray-100">
            <th class="text-left py-3 px-4 font-medium text-text-secondary">用例标题</th>
            <th class="text-left py-3 px-4 font-medium text-text-secondary">优先级</th>
            <th class="text-left py-3 px-4 font-medium text-text-secondary">状态</th>
            <th class="text-left py-3 px-4 font-medium text-text-secondary">类型</th>
            <th class="text-left py-3 px-4 font-medium text-text-secondary">创建者</th>
            <th class="text-left py-3 px-4 font-medium text-text-secondary">创建时间</th>
            <th class="text-left py-3 px-4 font-medium text-text-secondary">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="testcase in testcaseStore.testcases"
            :key="testcase.id"
            class="border-b border-gray-50 hover:bg-background-secondary transition-colors"
          >
            <td class="py-3 px-4 text-text-primary max-w-md truncate">
              {{ testcase.title }}
            </td>
            <td class="py-3 px-4">
              <span
                :class="[
                  'px-2 py-0.5 rounded text-xs font-medium',
                  testcase.priority === '高' ? 'bg-red-100 text-red-700' : '',
                  testcase.priority === '中' ? 'bg-yellow-100 text-yellow-700' : '',
                  testcase.priority === '低' ? 'bg-green-100 text-green-700' : '',
                ]"
              >
                {{ testcase.priority || '-' }}
              </span>
            </td>
            <td class="py-3 px-4">
              <span
                :class="[
                  'px-2 py-0.5 rounded text-xs',
                  testcase.status === '已完成' ? 'bg-green-100 text-green-700' : '',
                  testcase.status === '进行中' ? 'bg-blue-100 text-blue-700' : '',
                  testcase.status === '已阻塞' ? 'bg-red-100 text-red-700' : '',
                  testcase.status === '未开始' ? 'bg-gray-100 text-gray-700' : '',
                ]"
              >
                {{ testcase.status || '未开始' }}
              </span>
            </td>
            <td class="py-3 px-4 text-text-secondary">
              {{ testcase.test_type || '-' }}
            </td>
            <td class="py-3 px-4 text-text-secondary">{{ testcase.creator }}</td>
            <td class="py-3 px-4 text-text-secondary">
              {{ formatDateTime(testcase.created_at) }}
            </td>
            <td class="py-3 px-4">
              <div class="flex items-center gap-2">
                <button
                  class="text-primary hover:text-primary-light transition-colors"
                  title="查看详情"
                  @click="viewDetail(testcase.id)"
                >
                  <Eye class="w-4 h-4" />
                </button>
                <button
                  class="text-text-secondary hover:text-primary transition-colors"
                  title="编辑"
                  @click="handleEdit(testcase)"
                >
                  <Edit class="w-4 h-4" />
                </button>
                <button
                  class="text-functional-danger hover:text-red-600 transition-colors"
                  title="删除"
                  @click="deleteTestcase(testcase.id)"
                >
                  <Trash2 class="w-4 h-4" />
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- 空状态 -->
      <div
        v-if="testcaseStore.testcases.length === 0 && !testcaseStore.loading"
        class="text-center py-10 text-text-secondary"
      >
        暂无测试用例
      </div>

      <!-- 加载中 -->
      <div v-if="testcaseStore.loading" class="text-center py-10 text-text-secondary">
        加载中...
      </div>
    </div>

    <!-- 分页 -->
    <div v-if="testcaseStore.total > 0" class="flex items-center justify-between mt-4 px-2">
      <div class="text-sm text-text-secondary">
        共 {{ testcaseStore.total }} 条记录
      </div>
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

    <!-- 导出格式选择弹窗 -->
    <div
      v-if="showExportDialog"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      @click.self="showExportDialog = false"
    >
      <div class="bg-white rounded-lg shadow-xl w-96">
        <div class="p-6">
          <h3 class="text-lg font-semibold text-text-primary mb-4">选择导出格式</h3>
          
          <div class="space-y-3 mb-6">
            <label
              class="flex items-center gap-3 p-3 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors"
              :class="{ 'border-primary bg-blue-50': exportFormat === 'excel' }"
            >
              <input
                v-model="exportFormat"
                type="radio"
                value="excel"
                class="text-primary"
              />
              <FileSpreadsheet class="w-5 h-5 text-green-600" />
              <div>
                <p class="font-medium text-text-primary">Excel格式 (CSV)</p>
                <p class="text-sm text-text-secondary">适合数据分析和编辑</p>
              </div>
            </label>

            <label
              class="flex items-center gap-3 p-3 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors"
              :class="{ 'border-primary bg-blue-50': exportFormat === 'markdown' }"
            >
              <input
                v-model="exportFormat"
                type="radio"
                value="markdown"
                class="text-primary"
              />
              <FileText class="w-5 h-5 text-blue-600" />
              <div>
                <p class="font-medium text-text-primary">Markdown格式</p>
                <p class="text-sm text-text-secondary">适合文档分享和阅读</p>
              </div>
            </label>
          </div>

          <div class="flex items-center justify-end gap-2">
            <button
              class="btn-secondary"
              @click="showExportDialog = false"
            >
              取消
            </button>
            <button
              class="btn-primary"
              :disabled="exporting"
              @click="handleExport"
            >
              {{ exporting ? '导出中...' : '导出' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 编辑弹窗 -->
    <el-dialog v-model="editDialogVisible" title="编辑测试用例" width="600px">
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="用例标题" required>
          <el-input v-model="editForm.title" placeholder="请输入用例标题" />
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="优先级">
              <el-select v-model="editForm.priority" placeholder="请选择" clearable>
                <el-option v-for="p in priorities" :key="p" :label="p" :value="p" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态">
              <el-select v-model="editForm.status" placeholder="请选择">
                <el-option v-for="s in statuses" :key="s" :label="s" :value="s" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="测试类型">
          <el-input v-model="editForm.test_type" placeholder="请输入测试类型" />
        </el-form-item>

        <el-form-item label="用例描述">
          <el-input
            v-model="editForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入用例描述"
          />
        </el-form-item>

        <el-form-item label="前置条件">
          <el-input
            v-model="editForm.preconditions"
            type="textarea"
            :rows="3"
            placeholder="请输入前置条件"
          />
        </el-form-item>

        <el-form-item label="测试数据">
          <el-input
            v-model="editForm.test_data"
            type="textarea"
            :rows="3"
            placeholder="请输入测试数据"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <button class="btn-secondary" @click="editDialogVisible = false">取消</button>
        <button class="btn-primary ml-2" @click="handleSaveEdit">确定</button>
      </template>
    </el-dialog>
  </div>
</template>
