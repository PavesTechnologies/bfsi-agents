import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Pencil, RotateCcw, History } from 'lucide-react'
import { rulesApi, type Rule } from '@/api/rules'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { RoleGuard } from '@/components/common/RoleGuard'
import { ApprovalStatusBadge } from '@/components/common/StatusBadge'
import { formatDate } from '@/lib/utils'
import { toast } from '@/components/ui/toaster'

function EditRuleModal({ rule, onClose }: { rule: Rule; onClose: () => void }) {
  const queryClient = useQueryClient()
  const [newValue, setNewValue] = useState(String(rule.current_value?.value ?? ''))
  const [reason, setReason] = useState('')
  const schema = rule.validation_schema

  const mutation = useMutation({
    mutationFn: () => rulesApi.propose(rule.id, { value: rule.data_type === 'boolean' ? newValue === 'true' : Number(newValue) }, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rules'] })
      toast({ title: 'Rule change submitted', description: rule.requires_approval ? 'Awaiting SUPER_ADMIN approval.' : 'Applied immediately.' })
      onClose()
    },
    onError: (e: any) => toast({ title: 'Error', description: e.response?.data?.detail || 'Failed to submit change', variant: 'destructive' }),
  })

  return (
    <DialogContent className="max-w-md">
      <DialogHeader>
        <DialogTitle>Edit Rule: {rule.display_name}</DialogTitle>
      </DialogHeader>
      <div className="space-y-4">
        <div>
          <p className="text-sm text-muted-foreground">{rule.description}</p>
        </div>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="bg-gray-50 rounded p-2">
            <p className="text-xs text-muted-foreground">Current value</p>
            <p className="font-medium">{String(rule.current_value?.value)}</p>
          </div>
          <div className="bg-gray-50 rounded p-2">
            <p className="text-xs text-muted-foreground">Default value</p>
            <p className="font-medium">{String(rule.default_value?.value)}</p>
          </div>
        </div>
        <div className="space-y-1">
          <Label>New Value {schema && <span className="text-xs text-muted-foreground">({schema.min} – {schema.max})</span>}</Label>
          {rule.data_type === 'boolean' ? (
            <select value={newValue} onChange={(e) => setNewValue(e.target.value)} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm">
              <option value="true">true</option>
              <option value="false">false</option>
            </select>
          ) : (
            <Input type="number" value={newValue} onChange={(e) => setNewValue(e.target.value)} min={schema?.min} max={schema?.max} step={rule.data_type === 'number' && String(rule.current_value?.value).includes('.') ? '0.001' : '1'} />
          )}
        </div>
        <div className="space-y-1">
          <Label>Reason for change <span className="text-destructive">*</span></Label>
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Briefly explain why this value needs to change..."
            className="w-full min-h-[80px] rounded-md border border-input bg-background px-3 py-2 text-sm"
          />
        </div>
        {rule.requires_approval && (
          <p className="text-xs text-yellow-700 bg-yellow-50 rounded p-2">This is a high-risk rule. Change will require SUPER_ADMIN approval before taking effect.</p>
        )}
      </div>
      <DialogFooter>
        <Button variant="outline" onClick={onClose}>Cancel</Button>
        <Button onClick={() => mutation.mutate()} disabled={!reason.trim() || mutation.isPending}>
          {mutation.isPending ? 'Submitting…' : 'Submit Change'}
        </Button>
      </DialogFooter>
    </DialogContent>
  )
}

export default function RulesListPage() {
  const navigate = useNavigate()
  const { data, isLoading } = useQuery({ queryKey: ['rules'], queryFn: () => rulesApi.list() })
  const [editingRule, setEditingRule] = useState<Rule | null>(null)

  const grouped = data?.items.reduce((acc, rule) => {
    const cat = rule.category.name
    if (!acc[cat]) acc[cat] = []
    acc[cat].push(rule)
    return acc
  }, {} as Record<string, Rule[]>) ?? {}

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">{data?.total ?? 0} active rules across {Object.keys(grouped).length} categories</p>
        <RoleGuard permission="approve_rule_changes">
          <Button variant="outline" size="sm" onClick={() => navigate('/rules/pending')}>Pending Approvals</Button>
        </RoleGuard>
      </div>

      {isLoading && <div className="flex items-center justify-center h-48 text-muted-foreground">Loading rules…</div>}

      {Object.entries(grouped).map(([category, rules]) => (
        <Card key={category}>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">{category.replace('_', ' ')}</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50">
                  <th className="px-4 py-2 text-left font-medium text-gray-500">Rule</th>
                  <th className="px-4 py-2 text-left font-medium text-gray-500">Current Value</th>
                  <th className="px-4 py-2 text-left font-medium text-gray-500">Risk</th>
                  <th className="px-4 py-2 text-left font-medium text-gray-500">Version</th>
                  <th className="px-4 py-2 text-left font-medium text-gray-500">Updated</th>
                  <th className="px-4 py-2 text-right font-medium text-gray-500">Actions</th>
                </tr>
              </thead>
              <tbody>
                {rules.map((rule) => (
                  <tr key={rule.id} className="border-b last:border-0">
                    <td className="px-4 py-3">
                      <p className="font-medium">{rule.display_name}</p>
                      <p className="text-xs text-muted-foreground font-mono">{rule.rule_key}</p>
                    </td>
                    <td className="px-4 py-3 font-semibold">{String(rule.current_value?.value)}</td>
                    <td className="px-4 py-3">
                      <Badge variant={rule.risk_level === 'high' ? 'destructive' : 'secondary'} className="capitalize">{rule.risk_level}</Badge>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">v{rule.version}</td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">{formatDate(rule.updated_at)}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-1">
                        <RoleGuard permission="edit_low_risk_rules">
                          <Button variant="ghost" size="icon" onClick={() => setEditingRule(rule)} title="Edit">
                            <Pencil className="h-3.5 w-3.5" />
                          </Button>
                        </RoleGuard>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      ))}

      <Dialog open={!!editingRule} onOpenChange={(open) => !open && setEditingRule(null)}>
        {editingRule && <EditRuleModal rule={editingRule} onClose={() => setEditingRule(null)} />}
      </Dialog>
    </div>
  )
}
