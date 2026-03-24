<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { AlertTriangle, CheckCircle, Settings, ArrowRight } from 'lucide-vue-next'
import { ElButton, ElCard } from 'element-plus'
import { modelConfigApi, type ModelStatusSummary, type ModelStatus } from '@/api/modelConfig'

const router = useRouter()

const loading = ref(true)
const modelStatus = ref<ModelStatus | null>(null)
const summary = ref<ModelStatusSummary | null>(null)

// 获取模型配置状态
const fetchModelStatus = async () => {
  loading.value = true
  try {
    const [statusRes, summaryRes] = await Promise.all([
      modelConfigApi.getModelStatus(),
      modelConfigApi.getModelStatusSummary()
    ])
    modelStatus.value = statusRes
    summary.value = summaryRes
  } catch (error) {
    console.error('获取模型状态失败:', error)
  } finally {
    loading.value = false
  }
}

// 初始化模型配置
const initializeModels = async () => {
  try {
    const res = await modelConfigApi.initializeModels()
    if (res.success) {
      ElMessage.success('模型配置初始化成功')
      await fetchModelStatus()
    } else {
      ElMessage.error(res.message || '初始化失败')
    }
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '初始化失败')
  }
}

// 跳转到模型配置页面
const goToConfig = () => {
  router.push('/settings/model-config')
}

// 计算属性
const isAllConfigured = computed(() => summary.value?.all_configured ?? false)

const missingModels = computed(() => summary.value?.missing_models ?? [])

// 用途映射
const purposeLabels: Record<string, string> = {
  requirement_analyze: '需求分析',
  testcase_generate: '用例生成',
  testcase_review: '用例评审',
  embedding: '嵌入模型（RAG）'
}

// 获取用途标签
const getPurposeLabel = (purpose: string) => purposeLabels[purpose] || purpose

onMounted(() => {
  fetchModelStatus()
})

// 暴露给父组件
defineExpose({
  modelStatus,
  summary,
  isAllConfigured,
  missingModels,
  fetchModelStatus
})
</script>

<template>
  <div class="model-config-guide">
    <!-- 配置未完成 -->
    <ElCard v-if="!loading && !isAllConfigured" class="guide-card warning">
      <template #header>
        <div class="card-header">
          <AlertTriangle class="warning-icon" :size="20" />
          <span>AI 功能配置提醒</span>
        </div>
      </template>
      
      <div class="guide-content">
        <p class="guide-tip">
          在使用 AI 功能前，请先配置以下模型：
        </p>
        
        <ul class="missing-list">
          <li 
            v-for="item in missingModels" 
            :key="item.purpose"
            class="missing-item"
          >
            <span class="purpose-label">{{ item.display_name }}</span>
            <span class="status-badge missing">未配置</span>
          </li>
        </ul>

        <!-- 快速初始化按钮 -->
        <div class="init-section" v-if="missingModels.length > 0">
          <ElButton 
            type="primary" 
            size="small"
            @click="initializeModels"
            :loading="loading"
          >
            初始化默认配置
          </ElButton>
          <span class="init-tip">（创建预置模型模板）</span>
        </div>
        
        <div class="action-section">
          <ElButton 
            type="primary" 
            @click="goToConfig"
          >
            <Settings :size="16" style="margin-right: 4px" />
            前往配置
            <ArrowRight :size="16" style="margin-left: 4px" />
          </ElButton>
        </div>
      </div>
    </ElCard>

    <!-- 配置已完成 -->
    <ElCard v-else-if="!loading && isAllConfigured" class="guide-card success">
      <template #header>
        <div class="card-header">
          <CheckCircle class="success-icon" :size="20" />
          <span>AI 功能已配置</span>
        </div>
      </template>
      
      <div class="guide-content">
        <ul class="configured-list">
          <li 
            v-for="(status, purpose) in modelStatus" 
            :key="purpose"
            class="configured-item"
            v-show="typeof status === 'object' && 'configured' in status"
          >
            <span class="purpose-label">{{ getPurposeLabel(purpose) }}</span>
            <span class="status-badge success">
              {{ status.configured ? (status.model || '已配置') : '未配置' }}
            </span>
          </li>
        </ul>
        
        <div class="action-section">
          <ElButton 
            link 
            @click="goToConfig"
          >
            <Settings :size="14" style="margin-right: 4px" />
            管理模型配置
          </ElButton>
        </div>
      </div>
    </ElCard>

    <!-- 加载中 -->
    <ElCard v-else class="guide-card loading">
      <div class="loading-content">
        <div class="loading-spinner"></div>
        <span>加载中...</span>
      </div>
    </ElCard>
  </div>
</template>

<style scoped>
.model-config-guide {
  width: 100%;
}

.guide-card {
  margin-bottom: 16px;
}

.guide-card.warning {
  border-left: 4px solid #e6a23c;
}

.guide-card.success {
  border-left: 4px solid #67c23a;
}

.guide-card.loading {
  border-left: 4px solid #909399;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.warning-icon {
  color: #e6a23c;
}

.success-icon {
  color: #67c23a;
}

.guide-content {
  padding: 8px 0;
}

.guide-tip {
  color: #606266;
  margin-bottom: 16px;
}

.missing-list,
.configured-list {
  list-style: none;
  padding: 0;
  margin: 0 0 16px 0;
}

.missing-item,
.configured-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  margin-bottom: 8px;
  background: #f5f7fa;
  border-radius: 4px;
}

.purpose-label {
  font-weight: 500;
  color: #303133;
}

.status-badge {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
}

.status-badge.missing {
  background: #fef0f0;
  color: #f56c6c;
}

.status-badge.success {
  background: #f0f9eb;
  color: #67c23a;
}

.init-section {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  padding: 12px;
  background: #fdf6ec;
  border-radius: 4px;
}

.init-tip {
  font-size: 12px;
  color: #909399;
}

.action-section {
  display: flex;
  justify-content: flex-end;
}

.loading-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 20px;
  color: #909399;
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #dcdfe6;
  border-top-color: #409eff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
