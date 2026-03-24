import api from './index'

export interface AgentPrompt {
  id: number
  agent_type: string
  name: string
  description: string | null
  system_prompt: string
  user_prompt_template: string | null
  variables: Array<{ name: string; description: string }>
  is_active: boolean
  is_editable: boolean
  version: number
  created_at: string
  updated_at: string | null
}

export interface PromptCategory {
  category: string
  items: Array<{
    agent_type: string
    name: string
    description: string
    is_active: boolean
    is_editable: boolean
  }>
}

export const agentPromptApi = {
  // 获取所有提示词
  list: (params?: { agent_type?: string; is_active?: boolean }) => {
    return api.get<AgentPrompt[]>('/agent-prompts', { params })
  },

  // 获取提示词类型列表（按分类）
  listTypes: () => {
    return api.get<{ categories: PromptCategory[] }>('/agent-prompts/types')
  },

  // 获取单个提示词
  get: (id: number) => {
    return api.get<AgentPrompt>(`/agent-prompts/${id}`)
  },

  // 根据类型获取提示词
  getByType: (agentType: string) => {
    return api.get<AgentPrompt>(`/agent-prompts/by-type/${agentType}`)
  },

  // 创建提示词
  create: (data: Partial<AgentPrompt>) => {
    return api.post<AgentPrompt>('/agent-prompts', data)
  },

  // 更新提示词
  update: (id: number, data: Partial<AgentPrompt>) => {
    return api.put<AgentPrompt>(`/agent-prompts/${id}`, data)
  },

  // 删除提示词（软删除）
  delete: (id: number) => {
    return api.delete(`/agent-prompts/${id}`)
  },

  // 重置为默认
  reset: (id: number) => {
    return api.post<AgentPrompt>(`/agent-prompts/${id}/reset`)
  },

  // 启用提示词
  enable: (id: number) => {
    return api.post<AgentPrompt>(`/agent-prompts/${id}/enable`)
  },

  // 初始化默认提示词
  init: () => {
    return api.post('/agent-prompts/init')
  },

  // 获取模板变量说明
  getVariables: () => {
    return api.get('/agent-prompts/variables/template')
  },
}
