import { useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ArrowLeft,
  Clock,
  Star,
  Trash2,
  Plus,
  Send,
} from 'lucide-react'
import { counterOffersApi, CounterOfferSession, LoanTermOption } from '@/api/counterOffers'
import { pipelineApi } from '@/api/pipeline'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { formatCurrency, formatDate, cn } from '@/lib/utils'
import { toast } from '@/components/ui/toaster'

// ── Helpers ──────────────────────────────────────────────────────────────────

function InfoRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between py-2 border-b last:border-0">
      <span className="text-sm text-muted-foreground w-44 shrink-0">{label}</span>
      <span className="text-sm font-medium text-right">{value ?? '—'}</span>
    </div>
  )
}

function expiresIn(expiresAt: string): string {
  const diffMs = new Date(expiresAt).getTime() - Date.now()
  if (diffMs <= 0) return 'expired'
  const days = Math.floor(diffMs / 86_400_000)
  const hours = Math.floor((diffMs % 86_400_000) / 3_600_000)
  if (days > 0) return `in ${days}d ${hours}h`
  const mins = Math.floor((diffMs % 3_600_000) / 60_000)
  return `in ${hours}h ${mins}m`
}

// Fields the bank employee can type into for each offer option
interface LocalOption {
  proposed_amount: string
  proposed_tenure_months: string
  proposed_interest_rate: string
  justification: string
  note: string
}

function defaultLocal(opt: LoanTermOption): LocalOption {
  return {
    proposed_amount: String(opt.proposed_amount),
    proposed_tenure_months: String(opt.proposed_tenure_months),
    proposed_interest_rate: String(opt.proposed_interest_rate),
    justification: opt.justification,
    note: '',
  }
}

const PROTECTED_IDS = new Set(['CO1', 'CO2', 'CO3'])

// ── Page ─────────────────────────────────────────────────────────────────────

export default function CounterOfferReviewPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  // Application detail (for applicant info header)
  const { data: app } = useQuery({
    queryKey: ['pipeline-app', id],
    queryFn: () => pipelineApi.get(id!),
    enabled: !!id,
  })

  // Counter-offer session — poll while DRAFT so the bank employee sees live updates
  const { data: session, isLoading: sessionLoading } = useQuery({
    queryKey: ['counter-offer-session', id],
    queryFn: () => counterOffersApi.getByApplicationId(id!),
    enabled: !!id,
    refetchInterval: (query) =>
      query.state.data?.status === 'DRAFT' ? 8000 : false,
  })

  // Tab state
  const [tab, setTab] = useState<'offers' | 'audit'>('offers')

  // Per-option local edit state (tracks what the user has typed)
  const [localEdits, setLocalEdits] = useState<Record<string, LocalOption>>({})
  const [initialized, setInitialized] = useState(false)

  if (session && !initialized) {
    const initial: Record<string, LocalOption> = {}
    for (const opt of session.current_options) {
      initial[opt.option_id] = defaultLocal(opt)
    }
    setLocalEdits(initial)
    setInitialized(true)
  }

  // Debounce timer refs — one per option_id
  const debounceTimers = useRef<Record<string, ReturnType<typeof setTimeout>>>({})

  // Add-option form state
  const [isAddingOption, setIsAddingOption] = useState(false)
  const [newOpt, setNewOpt] = useState({
    label: '',
    proposed_amount: '',
    proposed_tenure_months: '',
    proposed_interest_rate: '',
    justification: '',
  })

  // ── Mutations ──────────────────────────────────────────────────────────────

  const updateOptionMutation = useMutation({
    mutationFn: ({
      optionId,
      payload,
    }: {
      optionId: string
      payload: Record<string, number | string>
    }) => counterOffersApi.updateOption(session!.id, optionId, payload),
    onSuccess: (updated, variables) => {
      queryClient.setQueryData(['counter-offer-session', id], updated)
      // Clear the audit note for this option after a successful save
      setLocalEdits((prev) => ({
        ...prev,
        [variables.optionId]: { ...prev[variables.optionId], note: '' },
      }))
    },
    onError: (e: any) =>
      toast({
        title: 'Save failed',
        description: e.response?.data?.detail,
        variant: 'destructive',
      }),
  })

  const setRecommendedMutation = useMutation({
    mutationFn: ({ optionId, note }: { optionId: string; note?: string }) =>
      counterOffersApi.setRecommended(session!.id, optionId, note),
    onSuccess: (updated) => {
      queryClient.setQueryData(['counter-offer-session', id], updated)
      toast({ title: 'Recommendation updated' })
    },
    onError: (e: any) =>
      toast({
        title: 'Error',
        description: e.response?.data?.detail,
        variant: 'destructive',
      }),
  })

  const deleteOptionMutation = useMutation({
    mutationFn: (optionId: string) =>
      counterOffersApi.deleteOption(session!.id, optionId),
    onSuccess: (updated) => {
      queryClient.setQueryData(['counter-offer-session', id], updated)
      toast({ title: 'Option removed' })
    },
    onError: (e: any) =>
      toast({
        title: 'Error',
        description: e.response?.data?.detail,
        variant: 'destructive',
      }),
  })

  const addOptionMutation = useMutation({
    mutationFn: () =>
      counterOffersApi.addOption(session!.id, {
        label: newOpt.label,
        proposed_amount: Number(newOpt.proposed_amount),
        proposed_tenure_months: Number(newOpt.proposed_tenure_months),
        proposed_interest_rate: Number(newOpt.proposed_interest_rate),
        justification: newOpt.justification,
      }),
    onSuccess: (updated) => {
      // Initialize local edits for any newly returned option
      const newOptions = updated.current_options.filter((o) => !localEdits[o.option_id])
      if (newOptions.length > 0) {
        setLocalEdits((prev) => {
          const extras: Record<string, LocalOption> = {}
          for (const o of newOptions) extras[o.option_id] = defaultLocal(o)
          return { ...prev, ...extras }
        })
      }
      queryClient.setQueryData(['counter-offer-session', id], updated)
      toast({ title: 'Custom option added' })
      setIsAddingOption(false)
      setNewOpt({
        label: '',
        proposed_amount: '',
        proposed_tenure_months: '',
        proposed_interest_rate: '',
        justification: '',
      })
    },
    onError: (e: any) =>
      toast({
        title: 'Error',
        description: e.response?.data?.detail,
        variant: 'destructive',
      }),
  })

  const publishMutation = useMutation({
    mutationFn: () => counterOffersApi.publish(session!.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['counter-offer-session', id] })
      queryClient.invalidateQueries({ queryKey: ['pipeline-app', id] })
      queryClient.invalidateQueries({ queryKey: ['pipeline-apps'] })
      toast({
        title: 'Counter offers published',
        description: 'Applicant has been notified and can now choose an offer.',
      })
      navigate(`/pipeline/${id}`)
    },
    onError: (e: any) =>
      toast({
        title: 'Publish failed',
        description: e.response?.data?.detail,
        variant: 'destructive',
      }),
  })

  // ── Audit log query (loaded only when tab is active) ──────────────────────

  const { data: editLog } = useQuery({
    queryKey: ['counter-offer-edit-log', session?.id],
    queryFn: () => counterOffersApi.getEditLog(session!.id),
    enabled: tab === 'audit' && !!session?.id,
  })

  // ── Debounced field change handler ─────────────────────────────────────────

  const scheduleOptionPatch = (optionId: string, local: LocalOption) => {
    if (debounceTimers.current[optionId]) clearTimeout(debounceTimers.current[optionId])

    debounceTimers.current[optionId] = setTimeout(() => {
      // Use cached server state to diff — avoids no-op patches
      const cached = queryClient.getQueryData<CounterOfferSession>([
        'counter-offer-session',
        id,
      ])
      const serverOpt = cached?.current_options.find((o) => o.option_id === optionId)
      if (!serverOpt) return

      const payload: Record<string, number | string> = {}
      const amount = Number(local.proposed_amount)
      const tenure = Number(local.proposed_tenure_months)
      const rate = Number(local.proposed_interest_rate)

      if (!isNaN(amount) && amount > 0 && amount !== serverOpt.proposed_amount)
        payload.proposed_amount = amount
      if (!isNaN(tenure) && tenure > 0 && tenure !== serverOpt.proposed_tenure_months)
        payload.proposed_tenure_months = tenure
      if (!isNaN(rate) && rate > 0 && rate !== serverOpt.proposed_interest_rate)
        payload.proposed_interest_rate = rate
      if (local.justification !== serverOpt.justification)
        payload.justification = local.justification
      if (local.note) payload.note = local.note

      if (Object.keys(payload).length === 0) return
      updateOptionMutation.mutate({ optionId, payload })
    }, 300)
  }

  const handleFieldChange = (
    optionId: string,
    field: keyof LocalOption,
    value: string,
  ) => {
    setLocalEdits((prev) => {
      const updated = { ...prev, [optionId]: { ...prev[optionId], [field]: value } }
      scheduleOptionPatch(optionId, updated[optionId])
      return updated
    })
  }

  // ── Render guards ──────────────────────────────────────────────────────────

  if (sessionLoading)
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground">
        Loading…
      </div>
    )
  if (!session)
    return (
      <div className="text-center py-12 text-muted-foreground">
        No counter offer session found for this application
      </div>
    )

  const isEditable = session.status === 'DRAFT'

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="space-y-6">
      {/* ── Page header ──────────────────────────────────────────────────── */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate(`/pipeline/${id}`)}
          className="gap-2"
        >
          <ArrowLeft className="h-4 w-4" /> Back to Review
        </Button>
        <div className="flex-1">
          <h2 className="text-lg font-semibold">Counter Offer Review</h2>
          <p className="text-sm text-muted-foreground font-mono">
            {app?.external_application_id}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Badge
            variant={
              session.status === 'DRAFT'
                ? 'warning'
                : session.status === 'PUBLISHED'
                  ? 'success'
                  : 'secondary'
            }
          >
            {session.status}
          </Badge>
          <span className="text-xs text-muted-foreground flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {expiresIn(session.expires_at)}
          </span>
        </div>
      </div>

      {/* ── Tabs ─────────────────────────────────────────────────────────── */}
      <div className="flex gap-1 border-b">
        {(['offers', 'audit'] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={cn(
              'px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors',
              tab === t
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground',
            )}
          >
            {t === 'offers' ? 'Counter Offers' : 'Audit Log'}
          </button>
        ))}
      </div>

      {/* ── Counter Offers tab ────────────────────────────────────────────── */}
      {tab === 'offers' && (
        <>
          {/* Financial context */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Affordability Profile</CardTitle>
              </CardHeader>
              <CardContent>
                <InfoRow
                  label="Monthly Income"
                  value={formatCurrency(session.monthly_income)}
                />
                <InfoRow
                  label="Existing Obligations"
                  value={formatCurrency(session.existing_monthly_obligations)}
                />
                <InfoRow
                  label="Max Affordable EMI"
                  value={
                    <span className="text-green-700 font-semibold">
                      {formatCurrency(session.max_affordable_emi)}
                    </span>
                  }
                />
                <InfoRow
                  label="Qualifying Cap"
                  value={
                    <span className="text-amber-700 font-semibold">
                      {formatCurrency(session.qualifying_cap)}
                    </span>
                  }
                />
                <InfoRow
                  label="Original Request DTI"
                  value={`${(session.original_request_dti * 100).toFixed(2)}%`}
                />
                <InfoRow
                  label="Model Confidence"
                  value={`${(session.confidence_score * 100).toFixed(0)}%`}
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Why Original Was Not Approved</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm leading-relaxed">{session.counter_offer_logic}</p>
                <div className="mt-4 pt-3 border-t">
                  <p className="text-xs font-medium text-muted-foreground mb-1">
                    System recommendation rationale
                  </p>
                  <p className="text-sm leading-relaxed">{session.recommendation_rationale}</p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Offer cards */}
          <div className="space-y-4">
            {session.current_options.map((opt) => {
              const local = localEdits[opt.option_id] ?? defaultLocal(opt)
              const isRecommended = opt.option_id === session.recommended_option_id
              const isProtected = PROTECTED_IDS.has(opt.option_id)

              return (
                <Card
                  key={opt.option_id}
                  className={cn(isRecommended && 'ring-2 ring-primary ring-offset-1')}
                >
                  <CardHeader>
                    <div className="flex items-center gap-3 flex-wrap">
                      <span className="font-mono text-xs bg-gray-100 px-2 py-0.5 rounded">
                        {opt.option_id}
                      </span>
                      <CardTitle className="text-base">{opt.label}</CardTitle>
                      {isRecommended && (
                        <Badge variant="default" className="ml-auto gap-1">
                          <Star className="h-3 w-3" /> Recommended
                        </Badge>
                      )}
                      {!opt.feasible && (
                        <Badge variant="destructive">Infeasible</Badge>
                      )}
                    </div>
                  </CardHeader>

                  <CardContent>
                    {/* Editable financial inputs */}
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
                      <div className="space-y-1">
                        <Label>Amount (₹)</Label>
                        <Input
                          type="number"
                          value={local.proposed_amount}
                          disabled={!isEditable}
                          onChange={(e) =>
                            handleFieldChange(opt.option_id, 'proposed_amount', e.target.value)
                          }
                        />
                      </div>
                      <div className="space-y-1">
                        <Label>Tenure (months)</Label>
                        <Input
                          type="number"
                          value={local.proposed_tenure_months}
                          disabled={!isEditable}
                          onChange={(e) =>
                            handleFieldChange(
                              opt.option_id,
                              'proposed_tenure_months',
                              e.target.value,
                            )
                          }
                        />
                      </div>
                      <div className="space-y-1">
                        <Label>Rate (%)</Label>
                        <Input
                          type="number"
                          step="0.01"
                          value={local.proposed_interest_rate}
                          disabled={!isEditable}
                          onChange={(e) =>
                            handleFieldChange(
                              opt.option_id,
                              'proposed_interest_rate',
                              e.target.value,
                            )
                          }
                        />
                      </div>
                    </div>

                    {/* Auto-calculated summary (always from server) */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-gray-50 rounded-lg p-3 mb-4 text-center">
                      <div>
                        <p className="text-xs text-muted-foreground">Monthly EMI</p>
                        <p className="text-sm font-semibold">
                          {formatCurrency(opt.monthly_payment_emi)}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground">Disbursement</p>
                        <p className="text-sm font-semibold">
                          {formatCurrency(opt.disbursement_amount)}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground">Total Repaid</p>
                        <p className="text-sm font-semibold">
                          {formatCurrency(opt.total_repayment)}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground">Headroom</p>
                        <p
                          className={cn(
                            'text-sm font-semibold',
                            opt.affordability_headroom_pct < 0
                              ? 'text-red-600'
                              : opt.affordability_headroom_pct < 10
                                ? 'text-amber-600'
                                : 'text-green-600',
                          )}
                        >
                          {opt.affordability_headroom_pct.toFixed(1)}%
                        </p>
                      </div>
                    </div>

                    {/* Justification */}
                    <div className="space-y-1 mb-3">
                      <Label className="text-xs">Justification</Label>
                      {isEditable ? (
                        <Input
                          value={local.justification}
                          onChange={(e) =>
                            handleFieldChange(opt.option_id, 'justification', e.target.value)
                          }
                          placeholder="Why is this offer appropriate for this applicant?"
                        />
                      ) : (
                        <p className="text-sm text-muted-foreground">{opt.justification}</p>
                      )}
                    </div>

                    {/* Audit note (only while editing) */}
                    {isEditable && (
                      <div className="space-y-1 mb-4">
                        <Label className="text-xs text-muted-foreground">
                          Edit note (stored in audit log)
                        </Label>
                        <Input
                          value={local.note}
                          onChange={(e) =>
                            setLocalEdits((prev) => ({
                              ...prev,
                              [opt.option_id]: { ...prev[opt.option_id], note: e.target.value },
                            }))
                          }
                          placeholder="Optional reason for this change…"
                        />
                      </div>
                    )}

                    {/* Option-level actions */}
                    {isEditable && (
                      <div className="flex items-center gap-2 flex-wrap">
                        {!isRecommended && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() =>
                              setRecommendedMutation.mutate({ optionId: opt.option_id })
                            }
                            disabled={setRecommendedMutation.isPending}
                            className="gap-1"
                          >
                            <Star className="h-3 w-3" /> Set as Recommended
                          </Button>
                        )}
                        {!isProtected && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => deleteOptionMutation.mutate(opt.option_id)}
                            disabled={deleteOptionMutation.isPending}
                            className="gap-1 text-red-600 hover:text-red-700 hover:bg-red-50"
                          >
                            <Trash2 className="h-3 w-3" /> Remove
                          </Button>
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>
              )
            })}
          </div>

          {/* Add custom option */}
          {isEditable && !isAddingOption && (
            <Button
              variant="outline"
              onClick={() => setIsAddingOption(true)}
              className="gap-2"
            >
              <Plus className="h-4 w-4" /> Add Custom Option
            </Button>
          )}

          {isEditable && isAddingOption && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">New Custom Option</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="space-y-1">
                    <Label>Label *</Label>
                    <Input
                      value={newOpt.label}
                      onChange={(e) =>
                        setNewOpt((p) => ({ ...p, label: e.target.value }))
                      }
                      placeholder="e.g. Special Relationship Rate"
                    />
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="space-y-1">
                      <Label>Amount (₹) *</Label>
                      <Input
                        type="number"
                        value={newOpt.proposed_amount}
                        onChange={(e) =>
                          setNewOpt((p) => ({ ...p, proposed_amount: e.target.value }))
                        }
                      />
                    </div>
                    <div className="space-y-1">
                      <Label>Tenure (months) *</Label>
                      <Input
                        type="number"
                        value={newOpt.proposed_tenure_months}
                        onChange={(e) =>
                          setNewOpt((p) => ({ ...p, proposed_tenure_months: e.target.value }))
                        }
                      />
                    </div>
                    <div className="space-y-1">
                      <Label>Rate (%) *</Label>
                      <Input
                        type="number"
                        step="0.01"
                        value={newOpt.proposed_interest_rate}
                        onChange={(e) =>
                          setNewOpt((p) => ({ ...p, proposed_interest_rate: e.target.value }))
                        }
                      />
                    </div>
                  </div>
                  <div className="space-y-1">
                    <Label>Justification *</Label>
                    <Input
                      value={newOpt.justification}
                      onChange={(e) =>
                        setNewOpt((p) => ({ ...p, justification: e.target.value }))
                      }
                      placeholder="Why is this option appropriate for this applicant?"
                    />
                  </div>
                  <div className="flex gap-2">
                    <Button
                      onClick={() => addOptionMutation.mutate()}
                      disabled={
                        addOptionMutation.isPending ||
                        !newOpt.label ||
                        !newOpt.proposed_amount ||
                        !newOpt.proposed_tenure_months ||
                        !newOpt.proposed_interest_rate ||
                        !newOpt.justification
                      }
                    >
                      {addOptionMutation.isPending ? 'Adding…' : 'Add Option'}
                    </Button>
                    <Button variant="outline" onClick={() => setIsAddingOption(false)}>
                      Cancel
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Publish action */}
          {isEditable && (
            <div className="pt-4 border-t">
              <Button
                onClick={() => publishMutation.mutate()}
                disabled={publishMutation.isPending}
                className="gap-2 bg-green-600 hover:bg-green-700"
              >
                <Send className="h-4 w-4" />
                {publishMutation.isPending ? 'Publishing…' : 'Publish to Applicant'}
              </Button>
              <p className="text-xs text-muted-foreground mt-2">
                Publishing notifies the applicant and locks all offers from further edits.
                Make sure the recommended option is set correctly before publishing.
              </p>
            </div>
          )}

          {/* Post-publish status banners */}
          {session.status === 'PUBLISHED' && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <p className="text-sm text-green-800 font-medium">Offers published</p>
              <p className="text-xs text-green-700 mt-1">
                Published {formatDate(session.published_at)} — awaiting applicant response.
              </p>
            </div>
          )}

          {session.status === 'APPLICANT_RESPONDED' && (
            <div
              className={cn(
                'border rounded-lg p-4',
                session.applicant_decision === 'ACCEPTED'
                  ? 'bg-blue-50 border-blue-200'
                  : 'bg-gray-50 border-gray-200',
              )}
            >
              <p
                className={cn(
                  'text-sm font-medium',
                  session.applicant_decision === 'ACCEPTED'
                    ? 'text-blue-800'
                    : 'text-gray-800',
                )}
              >
                Applicant{' '}
                {session.applicant_decision === 'ACCEPTED'
                  ? `accepted ${session.accepted_option_id}`
                  : 'declined all offers'}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                {formatDate(session.applicant_responded_at)}
              </p>
            </div>
          )}

          {session.status === 'EXPIRED' && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-sm text-red-800 font-medium">Session expired</p>
              <p className="text-xs text-red-700 mt-1">
                Expired {formatDate(session.expires_at)} — the applicant can no longer respond.
              </p>
            </div>
          )}
        </>
      )}

      {/* ── Audit Log tab ─────────────────────────────────────────────────── */}
      {tab === 'audit' && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Edit Audit Log</CardTitle>
          </CardHeader>
          <CardContent>
            {!editLog || editLog.length === 0 ? (
              <p className="text-sm text-muted-foreground">No edits recorded yet.</p>
            ) : (
              <div className="divide-y">
                {editLog.map((entry) => (
                  <div key={entry.id} className="py-3">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium">
                        {entry.option_id ? (
                          <>
                            <span className="font-mono text-xs bg-gray-100 px-1.5 py-0.5 rounded mr-2">
                              {entry.option_id}
                            </span>
                            {entry.field_name}
                          </>
                        ) : (
                          <>
                            <span className="text-muted-foreground mr-1">Session —</span>
                            {entry.field_name}
                          </>
                        )}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {formatDate(entry.edited_at)}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-xs">
                      <span className="bg-red-50 text-red-700 px-1.5 py-0.5 rounded font-mono max-w-[200px] truncate">
                        {JSON.stringify(entry.old_value)}
                      </span>
                      <span className="text-muted-foreground">→</span>
                      <span className="bg-green-50 text-green-700 px-1.5 py-0.5 rounded font-mono max-w-[200px] truncate">
                        {JSON.stringify(entry.new_value)}
                      </span>
                    </div>
                    {entry.note && (
                      <p className="text-xs text-muted-foreground mt-1 italic">
                        {entry.note}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
