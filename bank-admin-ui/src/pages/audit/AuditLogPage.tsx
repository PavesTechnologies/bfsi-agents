import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/api/client'
import { Card, CardContent } from '@/components/ui/card'
import { formatDate } from '@/lib/utils'

interface AuditLog {
  id: string
  user_id: string | null
  action: string
  resource_type: string | null
  resource_id: string | null
  before_snapshot: unknown
  after_snapshot: unknown
  ip_address: string | null
  created_at: string
}

const ACTION_COLORS: Record<string, string> = {
  RULE_CHANGE_PROPOSED: 'bg-yellow-100 text-yellow-800',
  RULE_CHANGE_APPROVED: 'bg-green-100 text-green-800',
  RULE_CHANGE_REJECTED: 'bg-red-100 text-red-800',
  RULE_RESET: 'bg-orange-100 text-orange-800',
  DOCUMENT_UPLOADED: 'bg-blue-100 text-blue-800',
  DOCUMENT_REPLACED: 'bg-indigo-100 text-indigo-800',
  DOCUMENT_DELETED: 'bg-red-100 text-red-800',
  USER_CREATED: 'bg-teal-100 text-teal-800',
  USER_UPDATED: 'bg-gray-100 text-gray-700',
}

export default function AuditLogPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['audit-logs'],
    queryFn: () => apiClient.get<AuditLog[]>('/audit', { params: { limit: 100 } }).then(r => r.data),
  })

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">Showing last 100 audit events</p>
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex items-center justify-center h-40 text-muted-foreground">Loading…</div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50">
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Action</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Resource</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">User</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">IP</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Date</th>
                </tr>
              </thead>
              <tbody>
                {data?.map((log) => (
                  <tr key={log.id} className="border-b last:border-0">
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${ACTION_COLORS[log.action] ?? 'bg-gray-100 text-gray-700'}`}>
                        {log.action}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs">
                      {log.resource_type && <span className="text-muted-foreground">{log.resource_type}: </span>}
                      <span className="font-mono">{log.resource_id?.slice(0, 16) ?? '—'}</span>
                    </td>
                    <td className="px-4 py-3 text-xs font-mono text-muted-foreground">{log.user_id?.slice(0, 8) ?? 'system'}</td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">{log.ip_address ?? '—'}</td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">{formatDate(log.created_at)}</td>
                  </tr>
                ))}
                {(data?.length ?? 0) === 0 && (
                  <tr><td colSpan={5} className="px-4 py-12 text-center text-muted-foreground">No audit events</td></tr>
                )}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
