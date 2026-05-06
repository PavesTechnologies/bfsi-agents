import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import AppShell from './components/layout/AppShell'
import LoginPage from './pages/auth/LoginPage'
import DashboardPage from './pages/dashboard/DashboardPage'
import ApplicationListPage from './pages/applications/ApplicationListPage'
import ApplicationDetailPage from './pages/applications/ApplicationDetailPage'
import RulesListPage from './pages/rules/RulesListPage'
import PendingApprovalsPage from './pages/rules/PendingApprovalsPage'
import DocumentsPage from './pages/documents/DocumentsPage'
import UsersPage from './pages/users/UsersPage'
import AuditLogPage from './pages/audit/AuditLogPage'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.accessToken)
  return token ? <>{children}</> : <Navigate to="/login" replace />
}

export function AppRouter() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="applications" element={<ApplicationListPage />} />
        <Route path="applications/:id" element={<ApplicationDetailPage />} />
        <Route path="rules" element={<RulesListPage />} />
        <Route path="rules/pending" element={<PendingApprovalsPage />} />
        <Route path="documents" element={<DocumentsPage />} />
        <Route path="users" element={<UsersPage />} />
        <Route path="audit" element={<AuditLogPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
