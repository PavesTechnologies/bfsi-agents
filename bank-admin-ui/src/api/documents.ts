import { apiClient } from './client'

export interface RagDocument {
  id: string
  collection_name: string
  document_name: string
  original_filename: string | null
  file_size_bytes: number | null
  status: string
  chunk_count: number | null
  uploaded_by: string | null
  created_at: string
  updated_at: string
}

export interface IngestionJob {
  id: string
  document_id: string
  status: string
  progress_pct: number
  error_message: string | null
  started_at: string | null
  completed_at: string | null
  created_at: string
}

export const documentsApi = {
  list: (collection?: string) =>
    apiClient.get<{ items: RagDocument[]; total: number }>('/documents/', { params: collection ? { collection } : {} }).then((r) => r.data),

  get: (id: string) => apiClient.get<RagDocument>(`/documents/${id}`).then((r) => r.data),

  upload: (file: File, collection_name: string, document_name: string) => {
    const form = new FormData()
    form.append('file', file)
    form.append('collection_name', collection_name)
    form.append('document_name', document_name)
    return apiClient.post<IngestionJob>('/documents/', form, { headers: { 'Content-Type': 'multipart/form-data' } }).then((r) => r.data)
  },

  replace: (documentId: string, file: File, document_name: string) => {
    const form = new FormData()
    form.append('file', file)
    form.append('document_name', document_name)
    return apiClient.post<IngestionJob>(`/documents/${documentId}/replace`, form, { headers: { 'Content-Type': 'multipart/form-data' } }).then((r) => r.data)
  },

  delete: (id: string) => apiClient.delete(`/documents/${id}`),

  getJob: (jobId: string) => apiClient.get<IngestionJob>(`/documents/ingestion-jobs/${jobId}`).then((r) => r.data),

  listJobs: (limit = 20) => apiClient.get<IngestionJob[]>('/documents/ingestion-jobs', { params: { limit } }).then((r) => r.data),
}
