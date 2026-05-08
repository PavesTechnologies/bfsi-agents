import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { pipelineApi, type LoanApplicationSummary } from '@/api/pipeline'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { PipelineStatusBadge } from '@/components/common/StatusBadge'
import { formatCurrency, formatDate } from '@/lib/utils'
import { ChevronLeft, ChevronRight } from 'lucide-react'

const POST_DECISION_STATUSES = [
  'AWAITING_APPLICANT_RESPONSE',
  'AWAITING_SIGNATURE',
  'SIGNATURE_COMPLETE',
  'DISBURSEMENT_IN_PROGRESS',
  'DISBURSED',
  'BANK_DECLINED',
  'CANCELLED',
]

export default function ApplicationListPage() {
  const navigate = useNavigate()
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState('')

  const statuses = statusFilter ? [statusFilter] : POST_DECISION_STATUSES

  const { data, isLoading } = useQuery({
    queryKey: ['applications-postdecision', page, statusFilter],
    queryFn: () => pipelineApi.list({ page, page_size: 20, statuses }),
    refetchInterval: 15000,
  })

  const totalPages = Math.ceil((data?.total ?? 0) / 20)

  const finalAmount = (a: LoanApplicationSummary) => a.bank_approved_amount ?? a.llm_approved_amount
  const finalRate = (a: LoanApplicationSummary) => a.bank_interest_rate ?? a.llm_interest_rate
  const finalDecision = (a: LoanApplicationSummary) => a.bank_final_decision ?? a.llm_decision

  return (
    <div className="space-y-4">
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-3">
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">Status</label>
              <select
                value={statusFilter}
                onChange={(e) => { setStatusFilter(e.target.value); setPage(1) }}
                className="h-9 rounded-md border border-input bg-background px-3 text-sm"
              >
                <option value="">All post-decision</option>
                {POST_DECISION_STATUSES.map((s) => (
                  <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>
                ))}
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex items-center justify-center h-48 text-muted-foreground">Loading…</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-gray-50">
                    <th className="px-4 py-3 text-left font-medium text-gray-500">Application</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-500">Status</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-500">Decision</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-500">Tier</th>
                    <th className="px-4 py-3 text-right font-medium text-gray-500">Risk Score</th>
                    <th className="px-4 py-3 text-right font-medium text-gray-500">Approved Amount</th>
                    <th className="px-4 py-3 text-right font-medium text-gray-500">Rate</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-500">Decided</th>
                  </tr>
                </thead>
                <tbody>
                  {data?.items.map((app) => {
                    const decision = finalDecision(app)
                    const amount = finalAmount(app)
                    const rate = finalRate(app)
                    return (
                      <tr
                        key={app.id}
                        className="border-b hover:bg-gray-50 cursor-pointer"
                        onClick={() => navigate(`/pipeline/${app.id}`)}
                      >
                        <td className="px-4 py-3">
                          <p className="font-mono text-xs">{app.external_application_id.slice(0, 8)}…</p>
                          {app.loan_purpose && <p className="text-xs text-muted-foreground">{app.loan_purpose}</p>}
                        </td>
                        <td className="px-4 py-3"><PipelineStatusBadge status={app.pipeline_status} /></td>
                        <td className="px-4 py-3">
                          {decision ? (
                            <span className={`text-xs font-medium ${decision === 'APPROVE' ? 'text-green-600' : decision === 'DECLINE' ? 'text-red-600' : 'text-amber-600'}`}>
                              {decision}
                            </span>
                          ) : <span className="text-muted-foreground text-xs">—</span>}
                        </td>
                        <td className="px-4 py-3 text-xs">{app.llm_risk_tier ? `Tier ${app.llm_risk_tier}` : '—'}</td>
                        <td className="px-4 py-3 text-right">{app.llm_risk_score?.toFixed(1) ?? '—'}</td>
                        <td className="px-4 py-3 text-right">{formatCurrency(amount)}</td>
                        <td className="px-4 py-3 text-right">{rate ? `${rate}%` : '—'}</td>
                        <td className="px-4 py-3 text-xs text-muted-foreground">{formatDate(app.bank_decided_at ?? app.updated_at)}</td>
                      </tr>
                    )
                  })}
                  {data?.items.length === 0 && (
                    <tr><td colSpan={8} className="px-4 py-12 text-center text-muted-foreground">No applications found</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <span>{data?.total ?? 0} total applications</span>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}><ChevronLeft className="h-4 w-4" /></Button>
          <span>Page {page} of {totalPages || 1}</span>
          <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}><ChevronRight className="h-4 w-4" /></Button>
        </div>
      </div>
    </div>
  )
}
