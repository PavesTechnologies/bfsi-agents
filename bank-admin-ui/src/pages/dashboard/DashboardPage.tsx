import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { TrendingUp, CheckCircle, XCircle, RefreshCw, AlertTriangle } from 'lucide-react'
import { applicationsApi } from '@/api/applications'
import { pipelineApi, type LoanApplicationSummary } from '@/api/pipeline'
import { rulesApi } from '@/api/rules'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { PipelineStatusBadge } from '@/components/common/StatusBadge'
import { formatCurrency, formatDate, formatPercent } from '@/lib/utils'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const POST_DECISION_STATUSES = [
  'AWAITING_APPLICANT_RESPONSE',
  'AWAITING_SIGNATURE',
  'SIGNATURE_COMPLETE',
  'DISBURSEMENT_IN_PROGRESS',
  'DISBURSED',
  'BANK_DECLINED',
  'CANCELLED',
]

function KPICard({ title, value, sub, icon: Icon, color }: { title: string; value: string | number; sub?: string; icon: any; color: string }) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">{title}</p>
            <p className="text-3xl font-bold mt-1">{value}</p>
            {sub && <p className="text-xs text-muted-foreground mt-1">{sub}</p>}
          </div>
          <div className={`flex h-12 w-12 items-center justify-center rounded-full ${color}`}>
            <Icon className="h-6 w-6 text-white" />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export default function DashboardPage() {
  const navigate = useNavigate()
  const { data: stats, isLoading: statsLoading } = useQuery({ queryKey: ['dashboard-stats'], queryFn: () => applicationsApi.dashboardStats() })
  const { data: volumeData } = useQuery({ queryKey: ['daily-volume'], queryFn: () => applicationsApi.dailyVolume(14) })
  const { data: recentApps } = useQuery({
    queryKey: ['dashboard-recent-pipeline'],
    queryFn: () => pipelineApi.list({ page: 1, page_size: 8, statuses: POST_DECISION_STATUSES }),
    refetchInterval: 15000,
  })

  const finalAmount = (a: LoanApplicationSummary) => a.bank_approved_amount ?? a.llm_approved_amount
  const finalDecision = (a: LoanApplicationSummary) => a.bank_final_decision ?? a.llm_decision

  if (statsLoading) return <div className="flex items-center justify-center h-64"><div className="text-muted-foreground">Loading dashboard…</div></div>

  return (
    <div className="space-y-6">
      {/* Pending approval alert */}
      {stats && stats.pending_rule_approvals > 0 && (
        <div className="flex items-center gap-3 rounded-lg border border-yellow-200 bg-yellow-50 p-4">
          <AlertTriangle className="h-5 w-5 text-yellow-600 shrink-0" />
          <div className="flex-1">
            <p className="text-sm font-medium text-yellow-800">
              {stats.pending_rule_approvals} rule change{stats.pending_rule_approvals > 1 ? 's' : ''} awaiting approval
            </p>
          </div>
          <button onClick={() => navigate('/rules/pending')} className="text-sm font-medium text-yellow-700 underline">
            Review
          </button>
        </div>
      )}

      {/* KPI cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KPICard title="Total Applications" value={stats?.total_applications ?? 0} icon={TrendingUp} color="bg-blue-500" />
        <KPICard title="Approved" value={stats?.total_approved ?? 0} sub={`${formatPercent(stats?.approval_rate)} approval rate`} icon={CheckCircle} color="bg-green-500" />
        <KPICard title="Declined" value={stats?.total_declined ?? 0} icon={XCircle} color="bg-red-500" />
        <KPICard title="Counter Offers" value={stats?.total_counter_offer ?? 0} sub={stats?.avg_risk_score ? `Avg score: ${stats.avg_risk_score}` : undefined} icon={RefreshCw} color="bg-orange-500" />
      </div>

      {/* Chart */}
      {volumeData && volumeData.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">14-Day Application Volume</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={volumeData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={(v) => v.slice(5)} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Legend />
                <Bar dataKey="approved" stackId="a" fill="#22c55e" name="Approved" />
                <Bar dataKey="counter_offer" stackId="a" fill="#f97316" name="Counter Offer" />
                <Bar dataKey="declined" stackId="a" fill="#ef4444" name="Declined" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* Recent applications */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Recent Applications</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50">
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Application</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Status</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Decision</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Tier</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-500">Amount</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Decided</th>
                </tr>
              </thead>
              <tbody>
                {recentApps?.items.map((app) => {
                  const decision = finalDecision(app)
                  const amount = finalAmount(app)
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
                      <td className="px-4 py-3 text-right">{formatCurrency(amount)}</td>
                      <td className="px-4 py-3 text-xs text-muted-foreground">{formatDate(app.bank_decided_at ?? app.updated_at)}</td>
                    </tr>
                  )
                })}
                {recentApps?.items.length === 0 && (
                  <tr><td colSpan={6} className="px-4 py-12 text-center text-muted-foreground">No applications found</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
