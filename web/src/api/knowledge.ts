import http from './index'

export interface KnowledgeBase {
  id: string
  name: string
  description: string
  embedding_model_id: string
  embedding_model_name: string
  chunk_size: number
  chunk_overlap: number
  document_count: number
  chunk_count: number
  status: string
  tenant_id: string
  created_at: string
  updated_at: string
}

export interface KnowledgeDocument {
  id: string
  knowledge_base_id: string
  filename: string
  file_size: number
  chunk_count: number
  status: string
  error_message: string
  created_at: string
  updated_at: string
}

export interface CreateKnowledgeBaseParams {
  name: string
  description?: string
  embedding_model_id: string
  chunk_size?: number
  chunk_overlap?: number
  tenant_id?: string
}

export interface UpdateKnowledgeBaseParams {
  name?: string
  description?: string
  chunk_size?: number
  chunk_overlap?: number
}

export function getKnowledgeBases(params?: { page?: number; page_size?: number; tenant_id?: string }) {
  return http.get<{ items: KnowledgeBase[]; total: number }>('/knowledge/bases', { params })
}

export function getKnowledgeBase(id: string) {
  return http.get<KnowledgeBase>(`/knowledge/bases/${id}`)
}

export function createKnowledgeBase(data: CreateKnowledgeBaseParams) {
  return http.post<KnowledgeBase>('/knowledge/bases', data)
}

export function updateKnowledgeBase(id: string, data: UpdateKnowledgeBaseParams) {
  return http.put<KnowledgeBase>(`/knowledge/bases/${id}`, data)
}

export function deleteKnowledgeBase(id: string) {
  return http.delete(`/knowledge/bases/${id}`)
}

export function getDocuments(knowledgeBaseId: string, params?: { page?: number; page_size?: number }) {
  return http.get<{ items: KnowledgeDocument[]; total: number }>(`/knowledge/bases/${knowledgeBaseId}/documents`, { params })
}

export function uploadDocument(knowledgeBaseId: string, file: File) {
  const formData = new FormData()
  formData.append('file', file)
  return http.post<KnowledgeDocument>(`/knowledge/bases/${knowledgeBaseId}/documents`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function deleteDocument(knowledgeBaseId: string, documentId: string) {
  return http.delete(`/knowledge/bases/${knowledgeBaseId}/documents/${documentId}`)
}
