import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { applicationsApi } from '@/api/applications'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { DecisionBadge, RiskTierBadge } from '@/components/common/StatusBadge'
import { formatCurrency, formatDate, formatPercent } from '@/lib/utils'
import { ChevronLeft, ChevronRight, Search } from 'lucide-react'

const DECISIONS = ['', 'APPROVE', 'DECLINE', 'COUNTER_OFFER']
const TIERS = ['', 'A', 'B', 'C', 'F']

export default function ApplicationListPage() {
  const navigate = useNavigate()
  const [page, setPage] = useState(1)
  const [decision, setDecision] = useState('')
  const [tier, setTier] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['applications', page, decision, tier],
    queryFn: () => applicationsApi.list({ page, page_size: 20, decision: decision || undefined, risk_tier: tier || undefined }),
  })

  const totalPages = Math.ceil((data?.total ?? 0) / 20)

  return (
    <div className="space-y-4">
      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-3">
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">Decision</label>
              <select
                value={decision}
                onChange={(e) => { setDecision(e.target.value); setPage(1) }}
                className="h-9 rounded-md border border-input bg-background px-3 text-sm"
              >
                {DECISIONS.map((d) => <option key={d} value={d}>{d || 'All Decisions'}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">Risk Tier</label>
              <select
                value={tier}
                onChange={(e) => { setTier(e.target.value); setPage(1) }}
                className="h-9 rounded-md border border-input bg-background px-3 text-sm"
              >
                {TIERS.map((t) => <option key={t} value={t}>{t ? `Tier ${t}` : 'All Tiers'}</option>)}
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex items-center justify-center h-48 text-muted-foreground">Loading…</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-gray-50">
                    <th className="px-4 py-3 text-left font-medium text-gray-500">Application ID</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-500">Decision</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-500">Risk Tier</th>
                    <th className="px-4 py-3 text-right font-medium text-gray-500">Risk Score</th>
                    <th className="px-4 py-3 text-right font-medium text-gray-500">Approved Amount</th>
                    <th className="px-4 py-3 text-right font-medium text-gray-500">Rate</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-500">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {data?.items.map((app) => (
                    <tr
                      key={app.application_id}
                      className="border-b hover:bg-gray-50 cursor-pointer"
                      onClick={() => navigate(`/applications/${app.application_id}`)}
                    >
                      <td className="px-4 py-3 font-mono text-xs">{app.application_id}</td>
                      <td className="px-4 py-3"><DecisionBadge decision={app.decision} /></td>
                      <td className="px-4 py-3"><RiskTierBadge tier={app.risk_tier} /></td>
                      <td className="px-4 py-3 text-right">{app.risk_score?.toFixed(1) ?? '—'}</td>
                      <td className="px-4 py-3 text-right">{formatCurrency(app.approved_amount)}</td>
                      <td className="px-4 py-3 text-right">{app.interest_rate ? `${app.interest_rate}%` : '—'}</td>
                      <td className="px-4 py-3 text-gray-500 text-xs">{formatDate(app.created_at)}</td>
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

      {/* Pagination */}
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
