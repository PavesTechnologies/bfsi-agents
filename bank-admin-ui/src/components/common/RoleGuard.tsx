import { usePermission } from '@/hooks/usePermission'

type Permission =
  | 'view_applications' | 'export_applications'
  | 'view_rules' | 'edit_low_risk_rules' | 'edit_high_risk_rules' | 'approve_rule_changes'
  | 'view_documents' | 'upload_documents' | 'replace_documents' | 'delete_documents'
  | 'manage_users' | 'view_audit_logs'

interface RoleGuardProps {
  permission: Permission
  children: React.ReactNode
  fallback?: React.ReactNode
}

export function RoleGuard({ permission, children, fallback = null }: RoleGuardProps) {
  const allowed = usePermission(permission)
  return allowed ? <>{children}</> : <>{fallback}</>
}
