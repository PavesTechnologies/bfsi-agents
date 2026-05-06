import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft } from 'lucide-react'
import { applicationsApi } from '@/api/applications'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { DecisionBadge, RiskTierBadge } from '@/components/common/StatusBadge'
import { formatCurrency, formatDate } from '@/lib/utils'

function InfoRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between py-2 border-b last:border-0">
      <span className="text-sm text-muted-foreground w-48 shrink-0">{label}</span>
      <span className="text-sm font-medium text-right">{value}</span>
    </div>
  )
}

export default function ApplicationDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const { data: app, isLoading } = useQuery({
    queryKey: ['application', id],
    queryFn: () => applicationsApi.get(id!),
    enabled: !!id,
  })

  if (isLoading) return <div className="flex items-center justify-center h-64 text-muted-foreground">Loading application…</div>
  if (!app) return <div className="text-muted-foreground">Application not found</div>

  return (
    <div className="space-y-6 max-w-4xl">
      <Button variant="ghost" size="sm" onClick={() => navigate(-1)} className="gap-2">
        <ArrowLeft className="h-4 w-4" /> Back
      </Button>

      <div className="flex items-center gap-4">
        <div>
          <h2 className="text-xl font-semibold font-mono">{app.application_id}</h2>
          <p className="text-sm text-muted-foreground">{formatDate(app.created_at)}</p>
        </div>
        <DecisionBadge decision={app.decision} />
        <RiskTierBadge tier={app.risk_tier} />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Loan Details */}
        <Card>
          <CardHeader><CardTitle className="text-base">Loan Details</CardTitle></CardHeader>
          <CardContent>
            <InfoRow label="Decision" value={<DecisionBadge decision={app.decision} />} />
            <InfoRow label="Risk Tier" value={<RiskTierBadge tier={app.risk_tier} />} />
            <InfoRow label="Risk Score" value={app.risk_score?.toFixed(2) ?? '—'} />
            <InfoRow label="Approved Amount" value={formatCurrency(app.approved_amount)} />
            <InfoRow label="Disbursement Amount" value={formatCurrency(app.disbursement_amount)} />
            <InfoRow label="Interest Rate" value={app.interest_rate ? `${app.interest_rate}%` : '—'} />
            <InfoRow label="Tenure" value={app.tenure_months ? `${app.tenure_months} months` : '—'} />
            {app.decline_reason && <InfoRow label="Decline Reason" value={app.decline_reason} />}
          </CardContent>
        </Card>

        {/* Performance */}
        <Card>
          <CardHeader><CardTitle className="text-base">Processing Metrics</CardTitle></CardHeader>
          <CardContent>
            <InfoRow label="Execution Time" value={app.execution_time_ms ? `${app.execution_time_ms}ms` : '—'} />
            {app.node_execution_times && (
              <div className="mt-3">
                <p className="text-xs text-muted-foreground mb-2">Node Execution Times</p>
                <div className="space-y-1">
                  {Object.entries(app.node_execution_times as Record<string, number>).map(([node, ms]) => (
                    <div key={node} className="flex justify-between text-xs">
                      <span className="text-gray-600">{node}</span>
                      <span className="font-mono">{ms}ms</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Explanation */}
      {app.explanation && (
        <Card>
          <CardHeader><CardTitle className="text-base">Decision Explanation</CardTitle></CardHeader>
          <CardContent>
            <p className="text-sm text-gray-700 leading-relaxed">{app.explanation}</p>
          </CardContent>
        </Card>
      )}

      {/* Counter Offer */}
      {app.counter_offer_data && (
        <Card>
          <CardHeader><CardTitle className="text-base">Counter Offer Options</CardTitle></CardHeader>
          <CardContent>
            <pre className="text-xs bg-gray-50 rounded-md p-4 overflow-auto">{JSON.stringify(app.counter_offer_data, null, 2)}</pre>
          </CardContent>
        </Card>
      )}

      {/* Reasoning Steps */}
      {app.reasoning_steps && (
        <Card>
          <CardHeader><CardTitle className="text-base">Analyzer Reasoning</CardTitle></CardHeader>
          <CardContent>
            <pre className="text-xs bg-gray-50 rounded-md p-4 overflow-auto max-h-96">{JSON.stringify(app.reasoning_steps, null, 2)}</pre>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
