import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { pipelineApi } from '@/api/pipeline'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { PipelineStatusBadge } from '@/components/common/StatusBadge'
import { formatCurrency, formatDate } from '@/lib/utils'
import { ChevronLeft, ChevronRight } from 'lucide-react'

const STATUSES = [
  '',
  'AWAITING_BANK_REVIEW',
  'DECISIONING_IN_PROGRESS',
  'AWAITING_BANK_APPROVAL',
  'BANK_DECLINED',
  'AWAITING_APPLICANT_RESPONSE',
  'AWAITING_SIGNATURE',
  'SIGNATURE_COMPLETE',
  'DISBURSED',
  'CANCELLED',
]

export default function LoanPipelinePage() {
  const navigate = useNavigate()
  const [page, setPage] = useState(1)
  const [status, setStatus] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['pipeline-apps', page, status],
    queryFn: () => pipelineApi.list({ page, page_size: 20, status: status || undefined }),
    refetchInterval: 15000,
  })

  const totalPages = Math.ceil((data?.total ?? 0) / 20)

  return (
    <div className="space-y-4">
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-3">
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">Status</label>
              <select
                value={status}
                onChange={(e) => { setStatus(e.target.value); setPage(1) }}
                className="h-9 rounded-md border border-input bg-background px-3 text-sm"
              >
                {STATUSES.map((s) => (
                  <option key={s} value={s}>
                    {s ? s.replace(/_/g, ' ') : 'All Statuses'}
                  </option>
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
                    <th className="px-4 py-3 text-left font-medium text-gray-500">KYC</th>
                    <th className="px-4 py-3 text-right font-medium text-gray-500">Requested</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-500">LLM Decision</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-500">Bank Decision</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-500">Received</th>
                  </tr>
                </thead>
                <tbody>
                  {data?.items.map((app) => (
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
                        <span className={`text-xs font-medium ${app.kyc_status === 'PASS' ? 'text-green-600' : 'text-red-600'}`}>
                          {app.kyc_status ?? '—'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right font-medium">{formatCurrency(app.loan_amount_requested)}</td>
                      <td className="px-4 py-3">
                        {app.llm_decision ? (
                          <span className={`text-xs font-medium ${app.llm_decision === 'APPROVE' ? 'text-green-600' : app.llm_decision === 'DECLINE' ? 'text-red-600' : 'text-amber-600'}`}>
                            {app.llm_decision} {app.llm_risk_tier ? `(Tier ${app.llm_risk_tier})` : ''}
                          </span>
                        ) : <span className="text-muted-foreground text-xs">—</span>}
                      </td>
                      <td className="px-4 py-3">
                        {app.bank_final_decision ? (
                          <span className={`text-xs font-medium ${app.bank_final_decision === 'APPROVE' ? 'text-green-600' : 'text-red-600'}`}>
                            {app.bank_final_decision}
                          </span>
                        ) : <span className="text-muted-foreground text-xs">—</span>}
                      </td>
                      <td className="px-4 py-3 text-xs text-muted-foreground">{formatDate(app.created_at)}</td>
                    </tr>
                  ))}
                  {data?.items.length === 0 && (
                    <tr><td colSpan={7} className="px-4 py-12 text-center text-muted-foreground">No applications found</td></tr>
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
          <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span>Page {page} of {totalPages || 1}</span>
          <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}
