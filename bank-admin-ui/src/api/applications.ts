import { apiClient } from './client'

export interface ApplicationSummary {
  application_id: string
  decision: string | null
  risk_tier: string | null
  risk_score: number | null
  approved_amount: number | null
  interest_rate: number | null
  tenure_months: number | null
  created_at: string
}

export interface ApplicationDetail extends ApplicationSummary {
  disbursement_amount: number | null
  explanation: string | null
  decline_reason: string | null
  reasoning_steps: unknown
  counter_offer_data: unknown
  parallel_tasks_executed: unknown
  node_execution_times: unknown
  execution_time_ms: number | null
}

export interface ApplicationListResponse {
  items: ApplicationSummary[]
  total: number
  page: number
  page_size: number
}

export interface DashboardStats {
  total_applications: number
  total_approved: number
  total_declined: number
  total_counter_offer: number
  approval_rate: number
  avg_risk_score: number | null
  pending_rule_approvals: number
}

export interface DailyVolume {
  date: string
  approved: number
  declined: number
  counter_offer: number
  total: number
}

export const applicationsApi = {
  list: (params: { page?: number; page_size?: number; decision?: string; risk_tier?: string; date_from?: string; date_to?: string }) =>
    apiClient.get<ApplicationListResponse>('/applications', { params }).then((r) => r.data),

  get: (id: string) =>
    apiClient.get<ApplicationDetail>(`/applications/${id}`).then((r) => r.data),

  dashboardStats: () =>
    apiClient.get<DashboardStats>('/applications/stats/overview').then((r) => r.data),

  dailyVolume: (days = 14) =>
    apiClient.get<DailyVolume[]>('/applications/stats/daily-volume', { params: { days } }).then((r) => r.data),
}
