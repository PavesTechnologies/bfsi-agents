import { apiClient } from './client'

export interface LoanApplicationSummary {
  id: string
  external_application_id: string
  pipeline_status: string
  loan_amount_requested: number
  loan_tenure_months: number
  loan_purpose: string | null
  kyc_status: string | null
  llm_decision: string | null
  llm_risk_tier: string | null
  llm_risk_score: number | null
  llm_approved_amount: number | null
  llm_interest_rate: number | null
  llm_tenure_months: number | null
  bank_final_decision: string | null
  bank_approved_amount: number | null
  bank_interest_rate: number | null
  bank_tenure_months: number | null
  bank_decided_at: string | null
  created_at: string
  updated_at: string
}

export interface LoanApplicationDetail extends LoanApplicationSummary {
  applicant_snapshot: Record<string, any>
  kyc_result_snapshot: Record<string, any> | null
  kyc_completed_at: string | null
  active_analyzers: string[] | null
  analyzers_selected_at: string | null
  decisioning_result_snapshot: Record<string, any> | null
  llm_counter_offer_options: any[] | null
  decisioning_completed_at: string | null
  bank_override_reason: string | null
  applicant_accepted: boolean | null
  signed_at: string | null
  disbursement_transaction_id: string | null
  disbursed_amount: number | null
  disbursed_at: string | null
}

export const pipelineApi = {
  list: (params?: { page?: number; page_size?: number; status?: string; statuses?: string[] }) =>
    apiClient
      .get<{ items: LoanApplicationSummary[]; total: number; page: number; page_size: number }>(
        '/pipeline/applications',
        {
          params,
          // Repeat ?statuses=A&statuses=B (FastAPI accepts repeated query params natively).
          paramsSerializer: { indexes: null },
        },
      )
      .then((r) => r.data),

  get: (id: string) =>
    apiClient.get<LoanApplicationDetail>(`/pipeline/applications/${id}`).then((r) => r.data),

  saveAnalyzers: (id: string, active_analyzers: string[] | null) =>
    apiClient
      .patch<{ pipeline_status: string; active_analyzers: string[] | null }>(
        `/pipeline/applications/${id}/analyzers`,
        { active_analyzers },
      )
      .then((r) => r.data),

  runDecisioning: (id: string) =>
    apiClient
      .post<{ pipeline_status: string }>(`/pipeline/applications/${id}/run-decisioning`)
      .then((r) => r.data),

  submitDecision: (
    id: string,
    payload: {
      final_decision: string
      approved_amount?: number
      interest_rate?: number
      tenure_months?: number
      override_reason?: string
    },
  ) =>
    apiClient
      .post<{ pipeline_status: string }>(`/pipeline/applications/${id}/bank-decision`, payload)
      .then((r) => r.data),
}

// User-specific rule overrides
export interface UserRuleWithOverride {
  id: string
  rule_key: string
  display_name: string
  description: string | null
  current_value: any
  data_type: string
  risk_level: string
  is_overridden: boolean
  override_value: any
  override_reason: string | null
  effective_value: any
}

export const userRulesApi = {
  list: (userId: string) =>
    apiClient.get<UserRuleWithOverride[]>(`/users/${userId}/rules`).then((r) => r.data),

  upsert: (userId: string, ruleId: string, override_value: any, override_reason?: string) =>
    apiClient
      .post<{ id: string }>(`/users/${userId}/rules/${ruleId}/override`, {
        override_value,
        override_reason,
      })
      .then((r) => r.data),

  delete: (userId: string, ruleId: string) =>
    apiClient.delete(`/users/${userId}/rules/${ruleId}/override`),
}
