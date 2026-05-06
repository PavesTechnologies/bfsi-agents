import { Outlet, useLocation } from 'react-router-dom'
import Sidebar from './Sidebar'
import Header from './Header'

const TITLES: Record<string, string> = {
  '/dashboard': 'Dashboard',
  '/applications': 'Applications',
  '/rules': 'Decision Rules',
  '/rules/pending': 'Pending Approvals',
  '/documents': 'RAG Documents',
  '/users': 'User Management',
  '/audit': 'Audit Log',
}

export default function AppShell() {
  const { pathname } = useLocation()
  const title = Object.entries(TITLES).find(([path]) => pathname.startsWith(path))?.[1] ?? 'Bank Admin'

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header title={title} />
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
