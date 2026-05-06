import { apiClient } from './client'

export interface RuleCategory {
  id: number
  name: string
  description: string | null
}

export interface Rule {
  id: string
  category: RuleCategory
  rule_key: string
  display_name: string
  description: string | null
  current_value: Record<string, unknown>
  default_value: Record<string, unknown>
  data_type: string
  validation_schema: Record<string, unknown> | null
  risk_level: string
  requires_approval: boolean
  is_active: boolean
  version: number
  updated_at: string
}

export interface RuleHistory {
  id: string
  rule_id: string
  version: number
  old_value: Record<string, unknown> | null
  new_value: Record<string, unknown>
  changed_by: string
  changed_by_name: string | null
  change_reason: string | null
  approval_status: string
  reviewer_comment: string | null
  created_at: string
  reviewed_at: string | null
}

export interface PendingApproval {
  id: string
  rule_id: string
  rule_key: string
  rule_display_name: string
  old_value: Record<string, unknown> | null
  new_value: Record<string, unknown>
  changed_by: string
  changed_by_name: string | null
  change_reason: string | null
  created_at: string
}

export const rulesApi = {
  list: () => apiClient.get<{ items: Rule[]; total: number }>('/rules/').then((r) => r.data),

  get: (id: string) => apiClient.get<Rule>(`/rules/${id}`).then((r) => r.data),

  history: (id: string) => apiClient.get<RuleHistory[]>(`/rules/${id}/history`).then((r) => r.data),

  propose: (id: string, new_value: Record<string, unknown>, change_reason: string) =>
    apiClient.patch<RuleHistory>(`/rules/${id}`, { new_value, change_reason }).then((r) => r.data),

  pendingApprovals: () => apiClient.get<PendingApproval[]>('/rules/pending-approvals').then((r) => r.data),

  approve: (historyId: string, comment?: string) =>
    apiClient.post<RuleHistory>(`/rules/pending-approvals/${historyId}/approve`, { comment }).then((r) => r.data),

  reject: (historyId: string, comment?: string) =>
    apiClient.post<RuleHistory>(`/rules/pending-approvals/${historyId}/reject`, { comment }).then((r) => r.data),

  reset: (id: string) => apiClient.post<Rule>(`/rules/${id}/reset`).then((r) => r.data),
}
