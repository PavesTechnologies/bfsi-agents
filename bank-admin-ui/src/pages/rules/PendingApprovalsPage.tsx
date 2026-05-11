import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { rulesApi, type PendingApproval } from '@/api/rules'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { formatDate } from '@/lib/utils'
import { isComplexValue, prettyJson, summarizeRuleValue, unwrapRuleValue } from '@/lib/rule-format'
import { Check, X } from 'lucide-react'
import { toast } from '@/components/ui/toaster'

function ValueBlock({ label, value, highlight }: { label: string; value: unknown; highlight?: boolean }) {
  return (
    <div>
      <p className="text-xs text-muted-foreground mb-1">{label}</p>
      {isComplexValue(value) ? (
        <pre
          className={`font-mono text-[11px] bg-gray-50 rounded p-2 max-w-[420px] max-h-[180px] overflow-auto ${highlight ? 'border border-primary/40' : ''}`}
        >
          {prettyJson(value)}
        </pre>
      ) : (
        <p className={`font-mono font-medium ${highlight ? 'text-primary' : ''}`}>
          {summarizeRuleValue(value)}
        </p>
      )}
    </div>
  )
}

function ActionBadge({ action }: { action: 'CREATE' | 'UPDATE' | 'DELETE' }) {
  if (action === 'CREATE')
    return <Badge variant="default" className="bg-blue-600 hover:bg-blue-600">CREATE</Badge>
  if (action === 'DELETE')
    return <Badge variant="destructive">DELETE</Badge>
  return <Badge variant="secondary">UPDATE</Badge>
}

/** Resolve the action for a pending row. Tolerant of older backends that
 *  only returned `is_create` and not the new `action_type`. */
function resolveAction(approval: PendingApproval): 'CREATE' | 'UPDATE' | 'DELETE' {
  if (approval.action_type) return approval.action_type
  // Detect the delete sentinel on the client too, just in case.
  const nv = approval.new_value as Record<string, unknown> | null
  if (nv && nv._delete === true) return 'DELETE'
  if (approval.is_create || approval.old_value == null) return 'CREATE'
  return 'UPDATE'
}

function ReviewModal({
  approval,
  action,
  onClose,
}: {
  approval: PendingApproval
  action: 'approve' | 'reject'
  onClose: () => void
}) {
  const queryClient = useQueryClient()
  const [comment, setComment] = useState('')
  const actionType = resolveAction(approval)
  const isDelete = actionType === 'DELETE'
  const isCreate = actionType === 'CREATE'

  const titleNoun =
    isCreate ? 'New Rule' : isDelete ? 'Rule Deletion' : 'Rule Change'

  const successTitle =
    action === 'approve'
      ? isCreate
        ? 'Rule activated'
        : isDelete
          ? 'Rule deleted'
          : 'Change approved'
      : isCreate
        ? 'Creation rejected'
        : isDelete
          ? 'Deletion rejected'
          : 'Change rejected'

  const mutation = useMutation({
    mutationFn: () => (action === 'approve' ? rulesApi.approve(approval.id, comment) : rulesApi.reject(approval.id, comment)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pending-approvals'] })
      queryClient.invalidateQueries({ queryKey: ['rules'] })
      toast({
        title: successTitle,
        description: `"${approval.rule_display_name}" has been ${action === 'approve' ? 'approved' : 'rejected'}.`,
      })
      onClose()
    },
    onError: (e: any) => toast({ title: 'Error', description: e.response?.data?.detail, variant: 'destructive' }),
  })

  return (
    <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
      <DialogHeader>
        <DialogTitle>
          {action === 'approve' ? 'Approve' : 'Reject'} {titleNoun}
        </DialogTitle>
      </DialogHeader>
      <div className="space-y-4">
        <div className="rounded-lg bg-gray-50 p-4 space-y-3 text-sm">
          <div className="flex items-center justify-between gap-2">
            <div>
              <p className="font-medium">{approval.rule_display_name}</p>
              <p className="text-xs font-mono text-muted-foreground">{approval.rule_key}</p>
            </div>
            <div className="flex gap-2 shrink-0">
              <ActionBadge action={actionType} />
              {approval.risk_level && (
                <Badge variant={approval.risk_level === 'high' ? 'destructive' : 'secondary'} className="capitalize">
                  {approval.risk_level}
                </Badge>
              )}
            </div>
          </div>
          <p className="text-xs text-muted-foreground">
            Proposed by {approval.changed_by_name ?? approval.changed_by} · {formatDate(approval.created_at)}
            {approval.category_name && <> · {approval.category_name}</>}
          </p>
          <div className="grid grid-cols-2 gap-4 pt-1">
            {isCreate ? (
              <div>
                <p className="text-xs text-muted-foreground mb-1">Old value</p>
                <p className="text-sm text-muted-foreground italic">(new rule — no prior value)</p>
              </div>
            ) : (
              <ValueBlock label={isDelete ? 'Current value' : 'Old value'} value={unwrapRuleValue(approval.old_value)} />
            )}
            {isDelete ? (
              <div>
                <p className="text-xs text-muted-foreground mb-1">After approval</p>
                <p className="text-sm font-medium text-red-700">(rule will be deactivated)</p>
              </div>
            ) : (
              <ValueBlock label={isCreate ? 'Initial value' : 'New value'} value={unwrapRuleValue(approval.new_value)} highlight />
            )}
          </div>
          {approval.change_reason && <p className="text-xs italic text-gray-600">"{approval.change_reason}"</p>}
        </div>
        <div className="space-y-1">
          <label className="text-sm font-medium">
            Comment {action === 'reject' && <span className="text-destructive">*</span>}
          </label>
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder={action === 'approve' ? 'Optional comment…' : 'Reason for rejection…'}
            className="w-full min-h-[80px] rounded-md border border-input bg-background px-3 py-2 text-sm"
          />
        </div>
      </div>
      <DialogFooter>
        <Button variant="outline" onClick={onClose}>Cancel</Button>
        <Button
          variant={action === 'approve' ? 'default' : 'destructive'}
          onClick={() => mutation.mutate()}
          disabled={mutation.isPending || (action === 'reject' && !comment.trim())}
        >
          {mutation.isPending ? 'Processing…' : action === 'approve' ? 'Approve' : 'Reject'}
        </Button>
      </DialogFooter>
    </DialogContent>
  )
}

export default function PendingApprovalsPage() {
  const { data: pending, isLoading } = useQuery({ queryKey: ['pending-approvals'], queryFn: () => rulesApi.pendingApprovals() })
  const [reviewing, setReviewing] = useState<{ approval: PendingApproval; action: 'approve' | 'reject' } | null>(null)

  return (
    <div className="space-y-4">
      {isLoading && <div className="text-muted-foreground">Loading…</div>}
      {!isLoading && (pending?.length ?? 0) === 0 && (
        <Card>
          <CardContent className="flex items-center justify-center h-40 text-muted-foreground">
            No pending rule changes
          </CardContent>
        </Card>
      )}

      {pending?.map((approval) => {
        const actionType = resolveAction(approval)
        const isDelete = actionType === 'DELETE'
        const isCreate = actionType === 'CREATE'
        return (
          <Card key={approval.id}>
            <CardContent className="p-4">
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-2 flex-1">
                  <div className="flex items-center gap-2">
                    <p className="font-medium">{approval.rule_display_name}</p>
                    <ActionBadge action={actionType} />
                    {approval.risk_level && (
                      <Badge variant={approval.risk_level === 'high' ? 'destructive' : 'secondary'} className="capitalize">
                        {approval.risk_level}
                      </Badge>
                    )}
                    {approval.category_name && (
                      <span className="text-xs text-muted-foreground">{approval.category_name}</span>
                    )}
                  </div>
                  <p className="text-xs font-mono text-muted-foreground">{approval.rule_key}</p>
                  <div className="grid grid-cols-2 gap-6 text-sm pt-1 max-w-2xl">
                    {isCreate ? (
                      <div>
                        <p className="text-xs text-muted-foreground mb-1">Old value</p>
                        <p className="text-sm text-muted-foreground italic">(new rule)</p>
                      </div>
                    ) : (
                      <ValueBlock label={isDelete ? 'Current value' : 'Old value'} value={unwrapRuleValue(approval.old_value)} />
                    )}
                    {isDelete ? (
                      <div>
                        <p className="text-xs text-muted-foreground mb-1">After approval</p>
                        <p className="text-sm font-medium text-red-700">(rule will be deactivated)</p>
                      </div>
                    ) : (
                      <ValueBlock label={isCreate ? 'Initial value' : 'New value'} value={unwrapRuleValue(approval.new_value)} highlight />
                    )}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Proposed by {approval.changed_by_name ?? approval.changed_by} · {formatDate(approval.created_at)}
                    {approval.change_reason && <span> · "{approval.change_reason}"</span>}
                  </div>
                </div>
                <div className="flex gap-2 shrink-0">
                  <Button
                    size="sm"
                    variant="outline"
                    className="text-green-700 border-green-200 hover:bg-green-50 gap-1"
                    onClick={() => setReviewing({ approval, action: 'approve' })}
                  >
                    <Check className="h-3.5 w-3.5" /> Approve
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    className="text-red-700 border-red-200 hover:bg-red-50 gap-1"
                    onClick={() => setReviewing({ approval, action: 'reject' })}
                  >
                    <X className="h-3.5 w-3.5" /> Reject
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )
      })}

      <Dialog open={!!reviewing} onOpenChange={(open) => !open && setReviewing(null)}>
        {reviewing && <ReviewModal approval={reviewing.approval} action={reviewing.action} onClose={() => setReviewing(null)} />}
      </Dialog>
    </div>
  )
}
