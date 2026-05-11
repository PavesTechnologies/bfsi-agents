import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Pencil, Plus, Trash2 } from 'lucide-react'
import { rulesApi, type Rule, type RuleCreatePayload } from '@/api/rules'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { RoleGuard } from '@/components/common/RoleGuard'
import { formatDate } from '@/lib/utils'
import { isComplexValue, prettyJson, summarizeRuleValue, unwrapRuleValue } from '@/lib/rule-format'
import { toast } from '@/components/ui/toaster'

// ─── Edit Rule (JSON-aware) ───────────────────────────────────────────────

function EditRuleModal({ rule, onClose }: { rule: Rule; onClose: () => void }) {
  const queryClient = useQueryClient()
  const currentInner = unwrapRuleValue(rule.current_value)
  const isJson = rule.data_type === 'json' || isComplexValue(currentInner)

  const [scalarValue, setScalarValue] = useState(
    rule.data_type === 'boolean'
      ? String(currentInner === true)
      : currentInner == null ? '' : String(currentInner),
  )
  const [jsonText, setJsonText] = useState(prettyJson(currentInner))
  const [jsonError, setJsonError] = useState<string | null>(null)
  const [reason, setReason] = useState('')
  const schema = rule.validation_schema as { min?: number; max?: number } | null

  const buildNewValue = (): Record<string, unknown> | null => {
    if (isJson) {
      try {
        const parsed = JSON.parse(jsonText)
        setJsonError(null)
        return { value: parsed }
      } catch (e: unknown) {
        setJsonError(e instanceof Error ? e.message : 'Invalid JSON')
        return null
      }
    }
    if (rule.data_type === 'boolean') return { value: scalarValue === 'true' }
    if (rule.data_type === 'number') return { value: Number(scalarValue) }
    return { value: scalarValue }
  }

  const mutation = useMutation({
    mutationFn: (newValue: Record<string, unknown>) => rulesApi.propose(rule.id, newValue, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rules'] })
      queryClient.invalidateQueries({ queryKey: ['pending-approvals'] })
      toast({
        title: 'Rule change submitted',
        description: rule.requires_approval ? 'Awaiting SUPER_ADMIN approval.' : 'Applied immediately.',
      })
      onClose()
    },
    onError: (e: any) => toast({ title: 'Error', description: e.response?.data?.detail || 'Failed to submit change', variant: 'destructive' }),
  })

  return (
    <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
      <DialogHeader>
        <DialogTitle>Edit Rule: {rule.display_name}</DialogTitle>
      </DialogHeader>
      <div className="space-y-4">
        {rule.description && <p className="text-sm text-muted-foreground">{rule.description}</p>}

        <div className="grid grid-cols-1 gap-3 text-sm">
          <div className="bg-gray-50 rounded p-2">
            <p className="text-xs text-muted-foreground mb-1">Current value</p>
            <pre className="font-mono text-xs whitespace-pre-wrap">{prettyJson(currentInner)}</pre>
          </div>
        </div>

        <div className="space-y-1">
          <Label>
            New Value
            {!isJson && schema && (schema.min != null || schema.max != null) && (
              <span className="ml-2 text-xs text-muted-foreground">({schema.min ?? '−∞'} – {schema.max ?? '∞'})</span>
            )}
          </Label>
          {isJson ? (
            <>
              <textarea
                value={jsonText}
                onChange={(e) => setJsonText(e.target.value)}
                className="w-full min-h-[180px] font-mono text-xs rounded-md border border-input bg-background px-3 py-2"
                spellCheck={false}
              />
              {jsonError && <p className="text-xs text-red-600">JSON parse error: {jsonError}</p>}
              <p className="text-[11px] text-muted-foreground">
                Edit the JSON value directly. The whole structure will be wrapped in {'`{"value": ...}`'} before saving.
              </p>
            </>
          ) : rule.data_type === 'boolean' ? (
            <select
              value={scalarValue}
              onChange={(e) => setScalarValue(e.target.value)}
              className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
            >
              <option value="true">true</option>
              <option value="false">false</option>
            </select>
          ) : (
            <Input
              type={rule.data_type === 'number' ? 'number' : 'text'}
              value={scalarValue}
              onChange={(e) => setScalarValue(e.target.value)}
              min={schema?.min}
              max={schema?.max}
              step={
                rule.data_type === 'number' &&
                typeof currentInner === 'number' &&
                String(currentInner).includes('.')
                  ? '0.001'
                  : '1'
              }
            />
          )}
        </div>

        <div className="space-y-1">
          <Label>
            Reason for change <span className="text-destructive">*</span>
          </Label>
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Briefly explain why this value needs to change…"
            className="w-full min-h-[60px] rounded-md border border-input bg-background px-3 py-2 text-sm"
          />
        </div>
        {rule.requires_approval && (
          <p className="text-xs text-yellow-700 bg-yellow-50 rounded p-2">
            This rule requires approval. The change will be queued in Pending Approvals until a
            SUPER_ADMIN reviews it.
          </p>
        )}
      </div>
      <DialogFooter>
        <Button variant="outline" onClick={onClose}>Cancel</Button>
        <Button
          onClick={() => {
            const v = buildNewValue()
            if (v) mutation.mutate(v)
          }}
          disabled={!reason.trim() || mutation.isPending}
        >
          {mutation.isPending ? 'Submitting…' : 'Submit Change'}
        </Button>
      </DialogFooter>
    </DialogContent>
  )
}

// ─── New Rule (create-with-HITL) ───────────────────────────────────────────

function NewRuleModal({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient()
  const { data: categories } = useQuery({ queryKey: ['rule-categories'], queryFn: () => rulesApi.categories() })

  const [form, setForm] = useState<RuleCreatePayload>({
    category_id: 0,
    rule_key: '',
    display_name: '',
    description: '',
    current_value: { value: '' },
    data_type: 'number',
    validation_schema: null,
    risk_level: 'low',
    requires_approval: true, // server always enforces — sent only for back-compat
    change_reason: '',
  })
  const [scalarValue, setScalarValue] = useState('')
  const [jsonText, setJsonText] = useState('[]')
  const [jsonError, setJsonError] = useState<string | null>(null)

  useEffect(() => {
    // Default to first category once loaded.
    if (categories && categories.length > 0 && !form.category_id) {
      setForm((f) => ({ ...f, category_id: categories[0].id }))
    }
  }, [categories]) // eslint-disable-line react-hooks/exhaustive-deps

  const isJson = form.data_type === 'json'

  const buildValue = (): Record<string, unknown> | null => {
    if (isJson) {
      try {
        const parsed = JSON.parse(jsonText)
        setJsonError(null)
        return { value: parsed }
      } catch (e) {
        setJsonError(e instanceof Error ? e.message : 'Invalid JSON')
        return null
      }
    }
    if (form.data_type === 'boolean') return { value: scalarValue === 'true' }
    if (form.data_type === 'number') {
      const n = Number(scalarValue)
      if (Number.isNaN(n)) {
        setJsonError('Value must be numeric')
        return null
      }
      return { value: n }
    }
    return { value: scalarValue }
  }

  const mutation = useMutation({
    mutationFn: (payload: RuleCreatePayload) => rulesApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rules'] })
      queryClient.invalidateQueries({ queryKey: ['pending-approvals'] })
      toast({
        title: 'Rule created',
        description: 'Awaiting SUPER_ADMIN approval — the rule will activate once approved.',
      })
      onClose()
    },
    onError: (e: any) => toast({ title: 'Error', description: e.response?.data?.detail || 'Failed to create rule', variant: 'destructive' }),
  })

  const submit = () => {
    const v = buildValue()
    if (!v) return
    mutation.mutate({ ...form, current_value: v, default_value: v })
  }

  const formInvalid =
    !form.category_id || !form.rule_key.trim() || !form.display_name.trim() || !form.change_reason.trim()

  return (
    <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
      <DialogHeader>
        <DialogTitle>New Rule</DialogTitle>
      </DialogHeader>
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1">
            <Label>Category</Label>
            <select
              value={form.category_id || ''}
              onChange={(e) => setForm({ ...form, category_id: Number(e.target.value) })}
              className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
            >
              {(categories ?? []).map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <Label>Data type</Label>
            <select
              value={form.data_type}
              onChange={(e) => setForm({ ...form, data_type: e.target.value })}
              className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
            >
              <option value="number">number</option>
              <option value="boolean">boolean</option>
              <option value="string">string</option>
              <option value="json">json</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1">
            <Label>Rule key</Label>
            <Input
              value={form.rule_key}
              onChange={(e) => setForm({ ...form, rule_key: e.target.value.replace(/\s+/g, '_').toLowerCase() })}
              placeholder="e.g. max_dti_tier_b"
              className="font-mono text-xs"
            />
          </div>
          <div className="space-y-1">
            <Label>Display name</Label>
            <Input
              value={form.display_name}
              onChange={(e) => setForm({ ...form, display_name: e.target.value })}
              placeholder="e.g. Max DTI — Tier B"
            />
          </div>
        </div>

        <div className="space-y-1">
          <Label>Description (optional)</Label>
          <Input
            value={form.description ?? ''}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            placeholder="What this rule controls"
          />
        </div>

        <div className="space-y-1">
          <Label>Initial value</Label>
          {isJson ? (
            <>
              <textarea
                value={jsonText}
                onChange={(e) => setJsonText(e.target.value)}
                className="w-full min-h-[160px] font-mono text-xs rounded-md border border-input bg-background px-3 py-2"
                spellCheck={false}
                placeholder='[{"label": "PRIME", "min": 750, "max": 900}]'
              />
              {jsonError && <p className="text-xs text-red-600">{jsonError}</p>}
            </>
          ) : form.data_type === 'boolean' ? (
            <select
              value={scalarValue || 'true'}
              onChange={(e) => setScalarValue(e.target.value)}
              className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
            >
              <option value="true">true</option>
              <option value="false">false</option>
            </select>
          ) : (
            <Input
              type={form.data_type === 'number' ? 'number' : 'text'}
              value={scalarValue}
              onChange={(e) => setScalarValue(e.target.value)}
              placeholder={form.data_type === 'number' ? '0.50' : 'value'}
            />
          )}
        </div>

        <div className="space-y-1">
          <Label>Risk level</Label>
          <select
            value={form.risk_level}
            onChange={(e) => setForm({ ...form, risk_level: e.target.value })}
            className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
          >
            <option value="low">low</option>
            <option value="high">high</option>
          </select>
        </div>

        <div className="space-y-1">
          <Label>
            Reason <span className="text-destructive">*</span>
          </Label>
          <textarea
            value={form.change_reason}
            onChange={(e) => setForm({ ...form, change_reason: e.target.value })}
            placeholder="Why is this rule being added?"
            className="w-full min-h-[60px] rounded-md border border-input bg-background px-3 py-2 text-sm"
          />
        </div>

        <p className="text-xs text-amber-700 bg-amber-50 rounded p-2">
          New rules are created <strong>inactive</strong>. A SUPER_ADMIN must approve the entry in
          Pending Approvals before the decisioning agent will pick it up.
        </p>
      </div>
      <DialogFooter>
        <Button variant="outline" onClick={onClose}>Cancel</Button>
        <Button onClick={submit} disabled={formInvalid || mutation.isPending}>
          {mutation.isPending ? 'Creating…' : 'Create rule'}
        </Button>
      </DialogFooter>
    </DialogContent>
  )
}

// ─── Delete Rule (propose-delete with HITL) ───────────────────────────────

function DeleteRuleModal({ rule, onClose }: { rule: Rule; onClose: () => void }) {
  const queryClient = useQueryClient()
  const [reason, setReason] = useState('')

  const mutation = useMutation({
    mutationFn: () => rulesApi.proposeDelete(rule.id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rules'] })
      queryClient.invalidateQueries({ queryKey: ['pending-approvals'] })
      toast({
        title: 'Deletion submitted',
        description: 'Awaiting SUPER_ADMIN approval. The rule stays active until approved.',
      })
      onClose()
    },
    onError: (e: any) =>
      toast({ title: 'Error', description: e.response?.data?.detail || 'Failed to submit deletion', variant: 'destructive' }),
  })

  return (
    <DialogContent className="max-w-md">
      <DialogHeader>
        <DialogTitle>Delete Rule: {rule.display_name}</DialogTitle>
      </DialogHeader>
      <div className="space-y-4">
        <div className="rounded bg-red-50 border border-red-200 p-3 text-sm">
          <p className="font-medium text-red-800">This will soft-delete the rule.</p>
          <p className="text-xs text-red-700 mt-1">
            After SUPER_ADMIN approval, <span className="font-mono">{rule.rule_key}</span> will be
            deactivated and the decisioning agent will stop using it on the next request.
          </p>
        </div>
        <div className="space-y-1">
          <Label>
            Reason for deletion <span className="text-destructive">*</span>
          </Label>
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Why does this rule need to be removed?"
            className="w-full min-h-[80px] rounded-md border border-input bg-background px-3 py-2 text-sm"
          />
        </div>
      </div>
      <DialogFooter>
        <Button variant="outline" onClick={onClose}>Cancel</Button>
        <Button
          variant="destructive"
          onClick={() => mutation.mutate()}
          disabled={!reason.trim() || mutation.isPending}
        >
          {mutation.isPending ? 'Submitting…' : 'Submit Deletion'}
        </Button>
      </DialogFooter>
    </DialogContent>
  )
}

// ─── List page ────────────────────────────────────────────────────────────

export default function RulesListPage() {
  const navigate = useNavigate()
  const { data, isLoading } = useQuery({ queryKey: ['rules'], queryFn: () => rulesApi.list() })
  const [editingRule, setEditingRule] = useState<Rule | null>(null)
  const [deletingRule, setDeletingRule] = useState<Rule | null>(null)
  const [creating, setCreating] = useState(false)

  const grouped = data?.items.reduce((acc, rule) => {
    const cat = rule.category.name
    if (!acc[cat]) acc[cat] = []
    acc[cat].push(rule)
    return acc
  }, {} as Record<string, Rule[]>) ?? {}

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          {data?.total ?? 0} rules across {Object.keys(grouped).length} categories
        </p>
        <div className="flex items-center gap-2">
          <RoleGuard permission="edit_low_risk_rules">
            <Button size="sm" className="gap-1" onClick={() => setCreating(true)}>
              <Plus className="h-3.5 w-3.5" /> New Rule
            </Button>
          </RoleGuard>
          <RoleGuard permission="approve_rule_changes">
            <Button variant="outline" size="sm" onClick={() => navigate('/rules/pending')}>
              Pending Approvals
            </Button>
          </RoleGuard>
        </div>
      </div>

      {isLoading && <div className="flex items-center justify-center h-48 text-muted-foreground">Loading rules…</div>}

      {Object.entries(grouped).map(([category, rules]) => (
        <Card key={category}>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
              {category.replace(/_/g, ' ')}
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50">
                  <th className="px-4 py-2 text-left font-medium text-gray-500">Rule</th>
                  <th className="px-4 py-2 text-left font-medium text-gray-500">Current Value</th>
                  <th className="px-4 py-2 text-left font-medium text-gray-500">Risk</th>
                  <th className="px-4 py-2 text-left font-medium text-gray-500">Active</th>
                  <th className="px-4 py-2 text-left font-medium text-gray-500">Version</th>
                  <th className="px-4 py-2 text-left font-medium text-gray-500">Updated</th>
                  <th className="px-4 py-2 text-right font-medium text-gray-500">Actions</th>
                </tr>
              </thead>
              <tbody>
                {rules.map((rule) => {
                  const inner = unwrapRuleValue(rule.current_value)
                  return (
                    <tr key={rule.id} className="border-b last:border-0">
                      <td className="px-4 py-3 align-top">
                        <p className="font-medium">{rule.display_name}</p>
                        <p className="text-xs text-muted-foreground font-mono">{rule.rule_key}</p>
                      </td>
                      <td className="px-4 py-3 align-top">
                        {isComplexValue(inner) ? (
                          <details className="group">
                            <summary className="cursor-pointer text-xs text-muted-foreground hover:text-foreground">
                              <span className="font-semibold text-foreground">{summarizeRuleValue(inner)}</span>
                              <span className="ml-1 text-[10px] opacity-60 group-open:hidden">click to expand</span>
                            </summary>
                            <pre className="mt-2 font-mono text-[11px] bg-gray-50 rounded p-2 max-w-[480px] overflow-x-auto">
                              {prettyJson(inner)}
                            </pre>
                          </details>
                        ) : (
                          <span className="font-semibold">{summarizeRuleValue(inner)}</span>
                        )}
                      </td>
                      <td className="px-4 py-3 align-top">
                        <Badge variant={rule.risk_level === 'high' ? 'destructive' : 'secondary'} className="capitalize">{rule.risk_level}</Badge>
                      </td>
                      <td className="px-4 py-3 align-top">
                        {rule.is_active ? (
                          <Badge variant="secondary" className="bg-green-100 text-green-800 hover:bg-green-100">active</Badge>
                        ) : (
                          <Badge variant="outline" className="text-amber-700 border-amber-300">pending</Badge>
                        )}
                      </td>
                      <td className="px-4 py-3 align-top text-muted-foreground">v{rule.version}</td>
                      <td className="px-4 py-3 align-top text-xs text-muted-foreground">{formatDate(rule.updated_at)}</td>
                      <td className="px-4 py-3 align-top">
                        <div className="flex items-center justify-end gap-1">
                          <RoleGuard permission="edit_low_risk_rules">
                            <Button variant="ghost" size="icon" onClick={() => setEditingRule(rule)} title="Edit">
                              <Pencil className="h-3.5 w-3.5" />
                            </Button>
                            {rule.is_active && (
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => setDeletingRule(rule)}
                                title="Propose deletion"
                                className="text-red-600 hover:text-red-700 hover:bg-red-50"
                              >
                                <Trash2 className="h-3.5 w-3.5" />
                              </Button>
                            )}
                          </RoleGuard>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </CardContent>
        </Card>
      ))}

      <Dialog open={!!editingRule} onOpenChange={(open) => !open && setEditingRule(null)}>
        {editingRule && <EditRuleModal rule={editingRule} onClose={() => setEditingRule(null)} />}
      </Dialog>

      <Dialog open={!!deletingRule} onOpenChange={(open) => !open && setDeletingRule(null)}>
        {deletingRule && <DeleteRuleModal rule={deletingRule} onClose={() => setDeletingRule(null)} />}
      </Dialog>

      <Dialog open={creating} onOpenChange={(open) => !open && setCreating(false)}>
        {creating && <NewRuleModal onClose={() => setCreating(false)} />}
      </Dialog>
    </div>
  )
}
