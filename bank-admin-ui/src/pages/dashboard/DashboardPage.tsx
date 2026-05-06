import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { TrendingUp, CheckCircle, XCircle, RefreshCw, AlertTriangle } from 'lucide-react'
import { applicationsApi } from '@/api/applications'
import { rulesApi } from '@/api/rules'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { DecisionBadge, RiskTierBadge } from '@/components/common/StatusBadge'
import { formatCurrency, formatDate, formatPercent } from '@/lib/utils'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

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
  const { data: recentApps } = useQuery({ queryKey: ['recent-applications'], queryFn: () => applicationsApi.list({ page: 1, page_size: 8 }) })

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
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Application ID</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Decision</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Risk Tier</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-500">Amount</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Date</th>
                </tr>
              </thead>
              <tbody>
                {recentApps?.items.map((app) => (
                  <tr
                    key={app.application_id}
                    className="border-b hover:bg-gray-50 cursor-pointer"
                    onClick={() => navigate(`/applications/${app.application_id}`)}
                  >
                    <td className="px-4 py-3 font-mono text-xs text-gray-700">{app.application_id}</td>
                    <td className="px-4 py-3"><DecisionBadge decision={app.decision} /></td>
                    <td className="px-4 py-3"><RiskTierBadge tier={app.risk_tier} /></td>
                    <td className="px-4 py-3 text-right">{formatCurrency(app.approved_amount)}</td>
                    <td className="px-4 py-3 text-gray-500">{formatDate(app.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
