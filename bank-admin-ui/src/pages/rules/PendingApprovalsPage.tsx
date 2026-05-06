import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { rulesApi, type PendingApproval } from '@/api/rules'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { formatDate } from '@/lib/utils'
import { Check, X } from 'lucide-react'
import { toast } from '@/components/ui/toaster'

function ReviewModal({ approval, action, onClose }: { approval: PendingApproval; action: 'approve' | 'reject'; onClose: () => void }) {
  const queryClient = useQueryClient()
  const [comment, setComment] = useState('')

  const mutation = useMutation({
    mutationFn: () => action === 'approve' ? rulesApi.approve(approval.id, comment) : rulesApi.reject(approval.id, comment),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pending-approvals'] })
      queryClient.invalidateQueries({ queryKey: ['rules'] })
      toast({ title: action === 'approve' ? 'Rule approved' : 'Rule rejected', description: `"${approval.rule_display_name}" has been ${action}d.` })
      onClose()
    },
    onError: (e: any) => toast({ title: 'Error', description: e.response?.data?.detail, variant: 'destructive' }),
  })

  return (
    <DialogContent className="max-w-md">
      <DialogHeader>
        <DialogTitle>{action === 'approve' ? 'Approve' : 'Reject'} Rule Change</DialogTitle>
      </DialogHeader>
      <div className="space-y-4">
        <div className="rounded-lg bg-gray-50 p-4 space-y-2 text-sm">
          <p><span className="text-muted-foreground">Rule:</span> <span className="font-medium">{approval.rule_display_name}</span></p>
          <p><span className="text-muted-foreground">Proposed by:</span> {approval.changed_by_name ?? approval.changed_by}</p>
          <div className="flex gap-6 pt-1">
            <div>
              <p className="text-xs text-muted-foreground">Old value</p>
              <p className="font-mono font-medium">{String(approval.old_value?.value ?? '—')}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">New value</p>
              <p className="font-mono font-medium text-primary">{String(approval.new_value?.value)}</p>
            </div>
          </div>
          {approval.change_reason && <p className="text-xs italic text-gray-600">"{approval.change_reason}"</p>}
        </div>
        <div className="space-y-1">
          <label className="text-sm font-medium">Comment {action === 'reject' && <span className="text-destructive">*</span>}</label>
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

      {pending?.map((approval) => (
        <Card key={approval.id}>
          <CardContent className="p-4">
            <div className="flex items-start justify-between gap-4">
              <div className="space-y-2 flex-1">
                <div>
                  <p className="font-medium">{approval.rule_display_name}</p>
                  <p className="text-xs font-mono text-muted-foreground">{approval.rule_key}</p>
                </div>
                <div className="flex gap-6 text-sm">
                  <div>
                    <p className="text-xs text-muted-foreground">Old value</p>
                    <p className="font-mono font-medium">{String(approval.old_value?.value ?? '—')}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">New value</p>
                    <p className="font-mono font-medium text-primary">{String(approval.new_value?.value)}</p>
                  </div>
                </div>
                <div className="text-xs text-muted-foreground">
                  Proposed by {approval.changed_by_name ?? approval.changed_by} · {formatDate(approval.created_at)}
                  {approval.change_reason && <span> · "{approval.change_reason}"</span>}
                </div>
              </div>
              <div className="flex gap-2 shrink-0">
                <Button size="sm" variant="outline" className="text-green-700 border-green-200 hover:bg-green-50 gap-1" onClick={() => setReviewing({ approval, action: 'approve' })}>
                  <Check className="h-3.5 w-3.5" /> Approve
                </Button>
                <Button size="sm" variant="outline" className="text-red-700 border-red-200 hover:bg-red-50 gap-1" onClick={() => setReviewing({ approval, action: 'reject' })}>
                  <X className="h-3.5 w-3.5" /> Reject
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}

      <Dialog open={!!reviewing} onOpenChange={(open) => !open && setReviewing(null)}>
        {reviewing && <ReviewModal approval={reviewing.approval} action={reviewing.action} onClose={() => setReviewing(null)} />}
      </Dialog>
    </div>
  )
}
