import { Badge } from '../ui/badge'

const DECISION_VARIANTS: Record<string, 'success' | 'destructive' | 'warning' | 'muted'> = {
  APPROVE: 'success',
  DECLINE: 'destructive',
  COUNTER_OFFER: 'warning',
}

const DOC_STATUS_VARIANTS: Record<string, 'success' | 'destructive' | 'warning' | 'muted' | 'info'> = {
  ACTIVE: 'success',
  FAILED: 'destructive',
  PROCESSING: 'warning',
  PENDING: 'info',
  REPLACED: 'muted',
  DELETED: 'muted',
}

const APPROVAL_VARIANTS: Record<string, 'success' | 'destructive' | 'warning' | 'muted'> = {
  APPROVED: 'success',
  REJECTED: 'destructive',
  PENDING: 'warning',
  AUTO_APPROVED: 'success',
}

export function DecisionBadge({ decision }: { decision: string | null }) {
  if (!decision) return <span className="text-muted-foreground text-xs">—</span>
  const variant = DECISION_VARIANTS[decision] ?? 'muted'
  return <Badge variant={variant}>{decision.replace('_', ' ')}</Badge>
}

export function RiskTierBadge({ tier }: { tier: string | null }) {
  if (!tier) return <span className="text-muted-foreground text-xs">—</span>
  const variants: Record<string, 'success' | 'info' | 'warning' | 'destructive'> = { A: 'success', B: 'info', C: 'warning', F: 'destructive' }
  return <Badge variant={variants[tier] ?? 'muted'}>Tier {tier}</Badge>
}

export function DocStatusBadge({ status }: { status: string }) {
  const variant = DOC_STATUS_VARIANTS[status] ?? 'muted'
  return <Badge variant={variant as any}>{status}</Badge>
}

export function ApprovalStatusBadge({ status }: { status: string }) {
  const variant = APPROVAL_VARIANTS[status] ?? 'muted'
  return <Badge variant={variant}>{status.replace('_', ' ')}</Badge>
}

const PIPELINE_STATUS_VARIANTS: Record<string, string> = {
  AWAITING_BANK_REVIEW: 'bg-blue-100 text-blue-800',
  DECISIONING_IN_PROGRESS: 'bg-amber-100 text-amber-800',
  AWAITING_BANK_APPROVAL: 'bg-purple-100 text-purple-800',
  BANK_DECLINED: 'bg-red-100 text-red-800',
  AWAITING_APPLICANT_RESPONSE: 'bg-indigo-100 text-indigo-800',
  AWAITING_SIGNATURE: 'bg-cyan-100 text-cyan-800',
  SIGNATURE_COMPLETE: 'bg-teal-100 text-teal-800',
  DISBURSEMENT_IN_PROGRESS: 'bg-orange-100 text-orange-800',
  DISBURSED: 'bg-green-100 text-green-800',
  CANCELLED: 'bg-gray-100 text-gray-600',
}

export function PipelineStatusBadge({ status }: { status: string }) {
  const cls = PIPELINE_STATUS_VARIANTS[status] ?? 'bg-gray-100 text-gray-600'
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold whitespace-nowrap ${cls}`}>
      {status.replace(/_/g, ' ')}
    </span>
  )
}

export function UserRoleBadge({ role }: { role: string }) {
  const colors: Record<string, string> = {
    SUPER_ADMIN: 'bg-purple-100 text-purple-800',
    CREDIT_MANAGER: 'bg-blue-100 text-blue-800',
    UNDERWRITER: 'bg-indigo-100 text-indigo-800',
    COMPLIANCE_OFFICER: 'bg-teal-100 text-teal-800',
    AUDITOR: 'bg-orange-100 text-orange-800',
    VIEWER: 'bg-gray-100 text-gray-600',
  }
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${colors[role] ?? 'bg-gray-100 text-gray-600'}`}>
      {role.replace('_', ' ')}
    </span>
  )
}
