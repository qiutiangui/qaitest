/**
 * 模型配置 API
 */
import api from './index'

// ============ 旧版接口（保留向后兼容）============

export interface AvailableModel {
  provider: string
  model_name: string
  display_name: string
  description: string
  supported_features: string[]
  is_available: boolean
}

export interface ModelListResponse {
  requirement_analyze_models: AvailableModel[]
  testcase_generate_models: AvailableModel[]
  testcase_review_models: AvailableModel[]
  default_requirement_analyze: string
  default_testcase_generate: string
  default_testcase_review: string
}

export interface ModelProvider {
  name: string
  display_name: string
  description: string
  configured: boolean
  default_model: string
}

// ============ 新版接口（数据库配置）============

export interface LLMModel {
  id: number
  name: string
  display_name: string
  provider: string
  base_url: string
  api_key: string | null
  default_model: string
  description: string | null
  enabled: boolean
  is_default: boolean
  created_at: string | null
  updated_at: string | null
}

export interface EmbeddingModel {
  id: number
  name: string
  display_name: string
  provider: string
  api_base: string
  api_key: string | null
  model_name: string
  dimension: number
  description: string | null
  enabled: boolean
  is_default: boolean
  created_at: string | null
  updated_at: string | null
}

export interface ModelStatus {
  requirement_analyze: {
    configured: boolean
    model: string | null
    model_name: string | null
    provider: string | null
    id: number | null
    is_custom: boolean
  }
  testcase_generate: {
    configured: boolean
    model: string | null
    model_name: string | null
    provider: string | null
    id: number | null
    is_custom: boolean
  }
  testcase_review: {
    configured: boolean
    model: string | null
    model_name: string | null
    provider: string | null
    id: number | null
    is_custom: boolean
  }
  embedding: {
    configured: boolean
    model: string | null
    model_name: string | null
    provider: string | null
    dimension: number | null
  }
  all_required_configured: boolean
  rag_available: boolean
}

export interface ModelStatusSummary {
  configured_count: number
  total_count: number
  all_configured: boolean
  missing_models: Array<{
    purpose: string
    display_name: string
  }>
}

export const modelConfigApi = {
  // ============ 旧版接口（保留向后兼容）============

  /**
   * 获取可用模型列表
   */
  getAvailableModels: () => {
    return api.get<ModelListResponse>('/models/available')
  },

  /**
   * 获取模型提供商列表
   */
  getModelProviders: () => {
    return api.get<{ providers: ModelProvider[] }>('/models/providers')
  },

  // ============ 新版接口（数据库配置）============

  // LLM 模型配置
  getLLMModels: () => {
    return api.get<LLMModel[]>('/v1/llm-models')
  },

  getEnabledLLMModels: () => {
    return api.get<LLMModel[]>('/v1/llm-models/enabled')
  },

  getLLMModel: (id: number) => {
    return api.get<LLMModel>(`/v1/llm-models/${id}`)
  },

  createLLMModel: (data: Partial<LLMModel>) => {
    return api.post<{ id: number; name: string; message: string }>('/v1/llm-models', data)
  },

  updateLLMModel: (id: number, data: Partial<LLMModel>) => {
    return api.put<{ id: number; name: string; message: string }>(`/v1/llm-models/${id}`, data)
  },

  deleteLLMModel: (id: number) => {
    return api.delete<{ message: string }>(`/v1/llm-models/${id}`)
  },

  testLLMConnection: (data: { base_url: string; api_key?: string; model: string; provider?: string }) => {
    return api.post<{ success: boolean; message: string }>('/v1/llm-models/test', data)
  },

  // 测试指定模型连接（后端内部获取真实api_key）
  testLLMModelById: (modelId: number) => {
    return api.post<{ success: boolean; message: string }>(`/v1/llm-models/${modelId}/test`)
  },

  // 获取模型详情（包含真实api_key，用于测试）
  getLLMModelForTest: (id: number) => {
    return api.get<{ id: number; name: string; display_name: string; provider: string; base_url: string; api_key?: string; default_model: string }>(`/v1/llm-models/${id}/for-test`)
  },

  getLLMModelDefaults: () => {
    return api.get<Array<{ purpose: string; model_name: string; model_type: string; updated_at: string }>>('/v1/llm-models/defaults/all')
  },

  setDefaultModel: (purpose: string, model_name: string) => {
    return api.put<{ message: string; purpose: string; model_name: string }>(`/v1/llm-models/defaults/${purpose}`, { model_name })
  },

  getModelForPurpose: (purpose: string) => {
    return api.get<{ configured: boolean; model?: any; message?: string }>(`/v1/llm-models/purpose/${purpose}`)
  },

  // 嵌入模型配置
  getEmbeddingModels: () => {
    return api.get<EmbeddingModel[]>('/v1/embedding-models')
  },

  getEnabledEmbeddingModels: () => {
    return api.get<EmbeddingModel[]>('/v1/embedding-models/enabled')
  },

  getDefaultEmbeddingModel: () => {
    return api.get<{ configured: boolean; model?: any; message?: string }>('/v1/embedding-models/default')
  },

  getEmbeddingModel: (id: number) => {
    return api.get<EmbeddingModel>(`/v1/embedding-models/${id}`)
  },

  createEmbeddingModel: (data: Partial<EmbeddingModel>) => {
    return api.post<{ id: number; name: string; message: string }>('/v1/embedding-models', data)
  },

  updateEmbeddingModel: (id: number, data: Partial<EmbeddingModel>) => {
    return api.put<{ id: number; name: string; message: string }>(`/v1/embedding-models/${id}`, data)
  },

  deleteEmbeddingModel: (id: number) => {
    return api.delete<{ message: string }>(`/v1/embedding-models/${id}`)
  },

  testEmbeddingConnection: (data: { api_base: string; api_key: string; model_name: string; provider?: string; dimension?: number }) => {
    return api.post<{ success: boolean; message: string }>('/v1/embedding-models/test', data)
  },

  setDefaultEmbeddingModel: (name: string) => {
    return api.put<{ message: string; name: string }>(`/v1/embedding-models/default/${name}`)
  },

  // 模型状态
  getModelStatus: () => {
    return api.get<ModelStatus>('/v1/model-status')
  },

  getModelStatusSummary: () => {
    return api.get<ModelStatusSummary>('/v1/model-status/summary')
  },

  initializeModels: () => {
    return api.post<{ success: boolean; message: string; llm_models_count?: number; embedding_configs_count?: number }>('/v1/model-status/initialize')
  },
}
