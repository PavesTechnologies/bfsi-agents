import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Play, CheckCircle, XCircle } from 'lucide-react'
import { pipelineApi } from '@/api/pipeline'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { PipelineStatusBadge } from '@/components/common/StatusBadge'
import { formatCurrency, formatDate, formatPercent } from '@/lib/utils'
import { toast } from '@/components/ui/toaster'

const ALL_ANALYZERS = [
  { key: 'credit_score', label: 'Credit Score' },
  { key: 'public_record', label: 'Public Record' },
  { key: 'utilization', label: 'Credit Utilization' },
  { key: 'exposure', label: 'Debt Exposure' },
  { key: 'behavior', label: 'Payment Behavior' },
  { key: 'inquiry', label: 'Inquiry Velocity' },
  { key: 'income', label: 'Income & DTI' },
]

function InfoRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between py-2 border-b last:border-0">
      <span className="text-sm text-muted-foreground w-40 shrink-0">{label}</span>
      <span className="text-sm font-medium text-right">{value ?? '—'}</span>
    </div>
  )
}

export default function ApplicationReviewPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: app, isLoading } = useQuery({
    queryKey: ['pipeline-app', id],
    queryFn: () => pipelineApi.get(id!),
    enabled: !!id,
    refetchInterval: 8000,
  })

  // Analyzer selection — default all ON
  const [selectedAnalyzers, setSelectedAnalyzers] = useState<string[]>(ALL_ANALYZERS.map((a) => a.key))
  const [analyzersInitialized, setAnalyzersInitialized] = useState(false)

  // When app loads, initialize from saved value if present
  if (app && !analyzersInitialized) {
    setSelectedAnalyzers(app.active_analyzers ?? ALL_ANALYZERS.map((a) => a.key))
    setAnalyzersInitialized(true)
  }

  // Bank decision form
  const [decision, setDecision] = useState<'APPROVE' | 'DECLINE'>('APPROVE')
  const [approvedAmount, setApprovedAmount] = useState('')
  const [interestRate, setInterestRate] = useState('')
  const [tenureMonths, setTenureMonths] = useState('')
  const [overrideReason, setOverrideReason] = useState('')

  // Pre-fill form when LLM results arrive
  const prefillDecisionForm = (a: typeof app) => {
    if (!a) return
    if (!approvedAmount && a.llm_approved_amount) setApprovedAmount(String(a.llm_approved_amount))
    if (!interestRate && a.llm_interest_rate) setInterestRate(String(a.llm_interest_rate))
    if (!tenureMonths && a.llm_tenure_months) setTenureMonths(String(a.llm_tenure_months))
    if (a.llm_decision === 'DECLINE') setDecision('DECLINE')
  }
  if (app?.pipeline_status === 'AWAITING_BANK_APPROVAL') prefillDecisionForm(app)

  const saveAnalyzersMutation = useMutation({
    mutationFn: () => pipelineApi.saveAnalyzers(id!, selectedAnalyzers),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pipeline-app', id] })
      toast({ title: 'Analyzer selection saved' })
    },
    onError: (e: any) => toast({ title: 'Error', description: e.response?.data?.detail, variant: 'destructive' }),
  })

  const runDecisioningMutation = useMutation({
    mutationFn: async () => {
      await pipelineApi.saveAnalyzers(id!, selectedAnalyzers)
      return pipelineApi.runDecisioning(id!)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pipeline-app', id] })
      queryClient.invalidateQueries({ queryKey: ['pipeline-apps'] })
      toast({ title: 'Decisioning started', description: 'Results will appear shortly…' })
    },
    onError: (e: any) => toast({ title: 'Error', description: e.response?.data?.detail, variant: 'destructive' }),
  })

  const submitDecisionMutation = useMutation({
    mutationFn: () =>
      pipelineApi.submitDecision(id!, {
        final_decision: decision,
        approved_amount: decision === 'APPROVE' ? Number(approvedAmount) : undefined,
        interest_rate: decision === 'APPROVE' ? Number(interestRate) : undefined,
        tenure_months: decision === 'APPROVE' ? Number(tenureMonths) : undefined,
        override_reason: overrideReason || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pipeline-app', id] })
      queryClient.invalidateQueries({ queryKey: ['pipeline-apps'] })
      toast({ title: 'Decision submitted', description: 'Applicant has been notified.' })
    },
    onError: (e: any) => toast({ title: 'Error', description: e.response?.data?.detail, variant: 'destructive' }),
  })

  if (isLoading) return <div className="flex items-center justify-center h-64 text-muted-foreground">Loading…</div>
  if (!app) return <div className="text-center py-12 text-muted-foreground">Application not found</div>

  const canRunDecisioning = app.pipeline_status === 'AWAITING_BANK_REVIEW'
  const canSubmitDecision = app.pipeline_status === 'AWAITING_BANK_APPROVAL'

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => navigate('/pipeline')} className="gap-2">
          <ArrowLeft className="h-4 w-4" /> Back
        </Button>
        <div className="flex-1">
          <h2 className="text-lg font-semibold font-mono">{app.external_application_id}</h2>
          <p className="text-sm text-muted-foreground">{formatDate(app.created_at)}</p>
        </div>
        <PipelineStatusBadge status={app.pipeline_status} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Applicant Info */}
        <Card>
          <CardHeader><CardTitle className="text-base">Applicant</CardTitle></CardHeader>
          <CardContent>
            <InfoRow label="Name" value={app.applicant_snapshot?.full_name} />
            <InfoRow label="PAN" value={app.applicant_snapshot?.pan_number} />
            <InfoRow label="Phone" value={app.applicant_snapshot?.phone} />
            <InfoRow label="Email" value={app.applicant_snapshot?.email} />
            <InfoRow label="KYC Status" value={
              <span className={app.kyc_status === 'PASS' ? 'text-green-600' : 'text-red-600'}>{app.kyc_status}</span>
            } />
          </CardContent>
        </Card>

        {/* Loan Request */}
        <Card>
          <CardHeader><CardTitle className="text-base">Loan Request</CardTitle></CardHeader>
          <CardContent>
            <InfoRow label="Amount Requested" value={formatCurrency(app.loan_amount_requested)} />
            <InfoRow label="Tenure" value={`${app.loan_tenure_months} months`} />
            <InfoRow label="Purpose" value={app.loan_purpose} />
          </CardContent>
        </Card>
      </div>

      {/* Analyzer Selection + Run Decisioning */}
      {(canRunDecisioning || app.pipeline_status === 'DECISIONING_IN_PROGRESS') && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Risk Analyzers</CardTitle>
            <p className="text-xs text-muted-foreground">Select which analyzers to run. Weights redistribute automatically for deselected analyzers.</p>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
              {ALL_ANALYZERS.map(({ key, label }) => (
                <label key={key} className="flex items-center gap-2 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={selectedAnalyzers.includes(key)}
                    disabled={!canRunDecisioning}
                    onChange={(e) =>
                      setSelectedAnalyzers((prev) =>
                        e.target.checked ? [...prev, key] : prev.filter((k) => k !== key),
                      )
                    }
                    className="h-4 w-4 rounded border-gray-300"
                  />
                  <span className="text-sm">{label}</span>
                </label>
              ))}
            </div>
            {canRunDecisioning && (
              <Button
                onClick={() => runDecisioningMutation.mutate()}
                disabled={runDecisioningMutation.isPending || selectedAnalyzers.length === 0}
                className="gap-2"
              >
                <Play className="h-4 w-4" />
                {runDecisioningMutation.isPending ? 'Starting…' : 'Run Decisioning'}
              </Button>
            )}
            {app.pipeline_status === 'DECISIONING_IN_PROGRESS' && (
              <p className="text-sm text-amber-600 mt-2">Decisioning in progress — page auto-refreshes…</p>
            )}
          </CardContent>
        </Card>
      )}

      {/* LLM Decisioning Result */}
      {app.llm_decision && (
        <Card>
          <CardHeader><CardTitle className="text-base">LLM Decisioning Result</CardTitle></CardHeader>
          <CardContent>
            <InfoRow label="LLM Decision" value={
              <span className={app.llm_decision === 'APPROVE' ? 'text-green-600 font-semibold' : app.llm_decision === 'DECLINE' ? 'text-red-600 font-semibold' : 'text-amber-600 font-semibold'}>
                {app.llm_decision}
              </span>
            } />
            <InfoRow label="Risk Tier" value={app.llm_risk_tier ? `Tier ${app.llm_risk_tier}` : null} />
            <InfoRow label="Risk Score" value={app.llm_risk_score?.toFixed(1)} />
            <InfoRow label="Suggested Amount" value={formatCurrency(app.llm_approved_amount)} />
            <InfoRow label="Suggested Rate" value={app.llm_interest_rate ? `${app.llm_interest_rate}%` : null} />
            <InfoRow label="Suggested Tenure" value={app.llm_tenure_months ? `${app.llm_tenure_months} months` : null} />
            {app.llm_counter_offer_options && app.llm_counter_offer_options.length > 0 && (
              <div className="mt-3">
                <p className="text-xs font-medium text-muted-foreground mb-2">Counter Offer Options</p>
                <div className="space-y-2">
                  {app.llm_counter_offer_options.map((opt: any, i: number) => (
                    <div key={i} className="text-xs bg-gray-50 rounded p-2 border">
                      <p className="font-medium">{opt.option_id}: {opt.description}</p>
                      <p className="text-muted-foreground">
                        {formatCurrency(opt.proposed_amount)} · {opt.proposed_tenure_months}m · {opt.proposed_interest_rate}%
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Bank Decision Form */}
      {canSubmitDecision && (
        <Card>
          <CardHeader><CardTitle className="text-base">Bank Decision</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="radio" value="APPROVE" checked={decision === 'APPROVE'} onChange={() => setDecision('APPROVE')} className="h-4 w-4" />
                  <span className="text-sm font-medium text-green-700">Approve</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="radio" value="DECLINE" checked={decision === 'DECLINE'} onChange={() => setDecision('DECLINE')} className="h-4 w-4" />
                  <span className="text-sm font-medium text-red-700">Decline</span>
                </label>
              </div>

              {decision === 'APPROVE' && (
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-1">
                    <Label>Approved Amount (₹)</Label>
                    <Input type="number" value={approvedAmount} onChange={(e) => setApprovedAmount(e.target.value)} placeholder="e.g. 500000" />
                  </div>
                  <div className="space-y-1">
                    <Label>Interest Rate (%)</Label>
                    <Input type="number" step="0.01" value={interestRate} onChange={(e) => setInterestRate(e.target.value)} placeholder="e.g. 10.5" />
                  </div>
                  <div className="space-y-1">
                    <Label>Tenure (months)</Label>
                    <Input type="number" value={tenureMonths} onChange={(e) => setTenureMonths(e.target.value)} placeholder="e.g. 36" />
                  </div>
                </div>
              )}

              <div className="space-y-1">
                <Label>Override Reason (optional)</Label>
                <Input value={overrideReason} onChange={(e) => setOverrideReason(e.target.value)} placeholder="Reason for overriding LLM recommendation…" />
              </div>

              <div className="flex gap-3">
                <Button
                  onClick={() => submitDecisionMutation.mutate()}
                  disabled={submitDecisionMutation.isPending || (decision === 'APPROVE' && (!approvedAmount || !interestRate || !tenureMonths))}
                  className={`gap-2 ${decision === 'APPROVE' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'}`}
                >
                  {decision === 'APPROVE' ? <CheckCircle className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
                  {submitDecisionMutation.isPending ? 'Submitting…' : `Submit ${decision === 'APPROVE' ? 'Approval' : 'Decline'}`}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Final Bank Decision (read-only) */}
      {app.bank_final_decision && !canSubmitDecision && (
        <Card>
          <CardHeader><CardTitle className="text-base">Bank Decision</CardTitle></CardHeader>
          <CardContent>
            <InfoRow label="Final Decision" value={
              <span className={app.bank_final_decision === 'APPROVE' ? 'text-green-600 font-semibold' : 'text-red-600 font-semibold'}>
                {app.bank_final_decision}
              </span>
            } />
            {app.bank_final_decision === 'APPROVE' && (
              <>
                <InfoRow label="Approved Amount" value={formatCurrency(app.bank_approved_amount)} />
                <InfoRow label="Interest Rate" value={app.bank_interest_rate ? `${app.bank_interest_rate}%` : null} />
                <InfoRow label="Tenure" value={app.bank_tenure_months ? `${app.bank_tenure_months} months` : null} />
              </>
            )}
            {app.bank_override_reason && <InfoRow label="Override Reason" value={app.bank_override_reason} />}
            <InfoRow label="Decided At" value={formatDate(app.bank_decided_at)} />
          </CardContent>
        </Card>
      )}

      {/* Applicant Response / Signature */}
      {app.signed_at && (
        <Card>
          <CardHeader><CardTitle className="text-base">Signature</CardTitle></CardHeader>
          <CardContent>
            <InfoRow label="Applicant Accepted" value={<span className="text-green-600">Yes</span>} />
            <InfoRow label="Signed At" value={formatDate(app.signed_at)} />
          </CardContent>
        </Card>
      )}

      {/* Disbursement */}
      {app.disbursed_at && (
        <Card>
          <CardHeader><CardTitle className="text-base">Disbursement</CardTitle></CardHeader>
          <CardContent>
            <InfoRow label="Transaction ID" value={<span className="font-mono text-xs">{app.disbursement_transaction_id}</span>} />
            <InfoRow label="Disbursed Amount" value={formatCurrency(app.disbursed_amount)} />
            <InfoRow label="Disbursed At" value={formatDate(app.disbursed_at)} />
          </CardContent>
        </Card>
      )}
    </div>
  )
}
