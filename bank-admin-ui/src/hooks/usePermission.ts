import { useAuthStore } from '../store/authStore'

type Permission =
  | 'view_applications'
  | 'export_applications'
  | 'view_rules'
  | 'edit_low_risk_rules'
  | 'edit_high_risk_rules'
  | 'approve_rule_changes'
  | 'view_documents'
  | 'upload_documents'
  | 'replace_documents'
  | 'delete_documents'
  | 'manage_users'
  | 'view_audit_logs'

const ROLE_PERMISSIONS: Record<string, Permission[]> = {
  SUPER_ADMIN: [
    'view_applications', 'export_applications',
    'view_rules', 'edit_low_risk_rules', 'edit_high_risk_rules', 'approve_rule_changes',
    'view_documents', 'upload_documents', 'replace_documents', 'delete_documents',
    'manage_users', 'view_audit_logs',
  ],
  CREDIT_MANAGER: [
    'view_applications', 'view_rules', 'edit_low_risk_rules',
    'view_documents', 'upload_documents',
  ],
  UNDERWRITER: ['view_applications', 'view_rules', 'view_documents'],
  COMPLIANCE_OFFICER: [
    'view_applications', 'export_applications', 'view_rules',
    'view_documents', 'upload_documents', 'replace_documents', 'view_audit_logs',
  ],
  AUDITOR: ['view_applications', 'export_applications', 'view_rules', 'view_documents', 'view_audit_logs'],
  VIEWER: ['view_applications', 'view_rules', 'view_documents'],
}

export function usePermission(permission: Permission): boolean {
  const user = useAuthStore((s) => s.user)
  const role = user?.role?.name ?? 'VIEWER'
  return ROLE_PERMISSIONS[role]?.includes(permission) ?? false
}

export function useRole(): string {
  const user = useAuthStore((s) => s.user)
  return user?.role?.name ?? 'VIEWER'
}
