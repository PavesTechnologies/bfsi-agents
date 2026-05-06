import { NavLink } from 'react-router-dom'
import { LayoutDashboard, FileText, Scale, BookOpen, Users, ScrollText, ClipboardCheck } from 'lucide-react'
import { cn } from '@/lib/utils'
import { usePermission } from '@/hooks/usePermission'
import { useAuthStore } from '@/store/authStore'
import { UserRoleBadge } from '../common/StatusBadge'

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard, permission: null },
  { to: '/applications', label: 'Applications', icon: FileText, permission: 'view_applications' as const },
  { to: '/rules', label: 'Decision Rules', icon: Scale, permission: 'view_rules' as const },
  { to: '/documents', label: 'RAG Documents', icon: BookOpen, permission: 'view_documents' as const },
  { to: '/users', label: 'Users', icon: Users, permission: 'manage_users' as const },
  { to: '/audit', label: 'Audit Log', icon: ScrollText, permission: 'view_audit_logs' as const },
]

export default function Sidebar() {
  const user = useAuthStore((s) => s.user)
  const canViewRules = usePermission('view_rules')
  const canViewDocs = usePermission('view_documents')
  const canManageUsers = usePermission('manage_users')
  const canViewAudit = usePermission('view_audit_logs')
  const canApprovePending = usePermission('approve_rule_changes')

  const permMap: Record<string, boolean> = {
    view_applications: true,
    view_rules: canViewRules,
    view_documents: canViewDocs,
    manage_users: canManageUsers,
    view_audit_logs: canViewAudit,
  }

  return (
    <aside className="flex h-full w-60 flex-col border-r bg-white">
      {/* Logo */}
      <div className="flex h-16 items-center border-b px-6">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-white font-bold text-sm">B</div>
          <span className="font-semibold text-gray-900">Bank Admin</span>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
        {navItems.map(({ to, label, icon: Icon, permission }) => {
          if (permission && !permMap[permission]) return null
          return (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                  isActive ? 'bg-primary/10 text-primary' : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900',
                )
              }
            >
              <Icon className="h-4 w-4 shrink-0" />
              {label}
            </NavLink>
          )
        })}

        {canApprovePending && (
          <NavLink
            to="/rules/pending"
            className={({ isActive }) =>
              cn('flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors', isActive ? 'bg-primary/10 text-primary' : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900')
            }
          >
            <ClipboardCheck className="h-4 w-4 shrink-0" />
            Pending Approvals
          </NavLink>
        )}
      </nav>

      {/* User info */}
      {user && (
        <div className="border-t p-4">
          <p className="text-sm font-medium text-gray-900 truncate">{user.full_name || user.email}</p>
          <p className="text-xs text-gray-500 truncate mb-1">{user.email}</p>
          <UserRoleBadge role={user.role.name} />
        </div>
      )}
    </aside>
  )
}
