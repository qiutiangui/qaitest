/**
 * RAG索引管理API
 */
import api from './index'

export interface RAGStats {
  exists: boolean
  collection?: string
  count: number
  error?: string
}

export interface RAGIndexResult {
  success: boolean
  message?: string
  error?: string
  data?: {
    indexed: number
    collection: string
    chunks: number
    filename: string
  }
}

export interface RAGSearchResult {
  success: boolean
  count: number
  data: Array<{
    content: string
    chapter: string
    filename: string
    score: number
  }>
}

/**
 * 获取项目索引状态
 */
export function getRAGStats(projectId: number) {
  return api.get<RAGStats>(`/rag/stats/${projectId}`)
}

/**
 * 手动索引文档
 */
export function indexDocument(data: {
  project_id: number
  version_id?: number
  file?: File
  content?: string
  filename?: string
}) {
  const formData = new FormData()
  formData.append('project_id', String(data.project_id))
  if (data.version_id) {
    formData.append('version_id', String(data.version_id))
  }
  if (data.file) {
    formData.append('file', data.file)
  }
  if (data.content) {
    formData.append('content', data.content)
  }
  if (data.filename) {
    formData.append('filename', data.filename)
  }
  
  return api.post<RAGIndexResult>('/rag/index', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 删除项目索引
 */
export function deleteRAGIndex(projectId: number) {
  return api.delete(`/rag/index/${projectId}`)
}

/**
 * 按版本删除向量数据
 */
export function deleteRAGByVersion(projectId: number, versionId: number) {
  return api.delete(`/rag/index/version/${projectId}/${versionId}`)
}

/**
 * 按需求名称删除向量数据
 */
export function deleteRAGByRequirement(
  projectId: number,
  requirementName: string,
  versionId?: number
) {
  const params: Record<string, string> = {
    project_id: String(projectId),
    requirement_name: requirementName
  }
  if (versionId !== undefined) {
    params.version_id = String(versionId)
  }
  return api.delete('/rag/index/requirement', { params })
}

/**
 * 搜索相似文档
 */
export function searchSimilar(data: {
  project_id: number
  query: string
  top_k?: number
  score_threshold?: number
}) {
  const formData = new FormData()
  formData.append('project_id', String(data.project_id))
  formData.append('query', data.query)
  formData.append('top_k', String(data.top_k || 5))
  formData.append('score_threshold', String(data.score_threshold || 0.7))

  return api.post<RAGSearchResult>('/rag/search', formData)
}

export default {
  getRAGStats,
  indexDocument,
  deleteRAGIndex,
  deleteRAGByVersion,
  deleteRAGByRequirement,
  searchSimilar,
}
