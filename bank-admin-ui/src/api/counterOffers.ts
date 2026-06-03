import { apiClient } from './client'

export interface LoanTermOption {
  option_id: string
  label: string
  proposed_amount: number
  proposed_tenure_months: number
  proposed_interest_rate: number
  monthly_payment_emi: number
  disbursement_amount: number
  total_repayment: number
  affordability_headroom_pct: number
  is_recommended: boolean
  feasible: boolean
  justification: string
}

export interface CounterOfferSession {
  id: string
  application_id: string
  original_request_dti: number
  max_affordable_emi: number
  monthly_income: number
  existing_monthly_obligations: number
  qualifying_cap: number
  counter_offer_logic: string
  confidence_score: number
  generated_options: LoanTermOption[]
  current_options: LoanTermOption[]
  recommended_option_id: string
  recommendation_rationale: string
  status: 'DRAFT' | 'PUBLISHED' | 'APPLICANT_RESPONDED' | 'EXPIRED'
  published_by: string | null
  published_at: string | null
  applicant_decision: 'ACCEPTED' | 'DECLINED' | null
  accepted_option_id: string | null
  applicant_responded_at: string | null
  expires_at: string
  created_at: string
  updated_at: string
}

export interface EditLogEntry {
  id: string
  session_id: string
  option_id: string | null
  field_name: string
  old_value: unknown
  new_value: unknown
  edited_by: string | null
  note: string | null
  edited_at: string
}

export const counterOffersApi = {
  getByApplicationId: (applicationId: string) =>
    apiClient
      .get<CounterOfferSession>(`/counter-offers/applications/${applicationId}`)
      .then((r) => r.data),

  updateOption: (
    sessionId: string,
    optionId: string,
    payload: {
      proposed_amount?: number
      proposed_tenure_months?: number
      proposed_interest_rate?: number
      justification?: string
      note?: string
    },
  ) =>
    apiClient
      .patch<CounterOfferSession>(`/counter-offers/${sessionId}/options/${optionId}`, payload)
      .then((r) => r.data),

  addOption: (
    sessionId: string,
    payload: {
      label: string
      proposed_amount: number
      proposed_tenure_months: number
      proposed_interest_rate: number
      justification: string
    },
  ) =>
    apiClient
      .post<CounterOfferSession>(`/counter-offers/${sessionId}/options`, payload)
      .then((r) => r.data),

  deleteOption: (sessionId: string, optionId: string) =>
    apiClient
      .delete<CounterOfferSession>(`/counter-offers/${sessionId}/options/${optionId}`)
      .then((r) => r.data),

  setRecommended: (sessionId: string, optionId: string, note?: string) =>
    apiClient
      .patch<CounterOfferSession>(`/counter-offers/${sessionId}/recommend`, {
        option_id: optionId,
        note,
      })
      .then((r) => r.data),

  publish: (sessionId: string) =>
    apiClient
      .post<CounterOfferSession>(`/counter-offers/${sessionId}/publish`)
      .then((r) => r.data),

  getEditLog: (sessionId: string) =>
    apiClient
      .get<EditLogEntry[]>(`/counter-offers/${sessionId}/edit-log`)
      .then((r) => r.data),

  // Bank-initiated offer on a DECLINED application. Seeds a DRAFT session the
  // bank can edit/publish from the standard Counter-Offer Review page.
  createManualOffer: (
    applicationId: string,
    payload?: {
      proposed_amount?: number
      proposed_tenure_months?: number
      proposed_interest_rate?: number
      label?: string
      justification?: string
    },
  ) =>
    apiClient
      .post<{ session_id: string; status: string }>(
        `/counter-offers/applications/${applicationId}/manual-offer`,
        payload ?? {},
      )
      .then((r) => r.data),
}
