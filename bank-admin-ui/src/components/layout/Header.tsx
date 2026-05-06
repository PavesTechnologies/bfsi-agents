import { useNavigate } from 'react-router-dom'
import { LogOut, User } from 'lucide-react'
import { Button } from '../ui/button'
import { useAuthStore } from '@/store/authStore'
import { authApi } from '@/api/auth'

export default function Header({ title }: { title?: string }) {
  const navigate = useNavigate()
  const { refreshToken, logout } = useAuthStore()

  const handleLogout = async () => {
    if (refreshToken) {
      try { await authApi.logout(refreshToken) } catch { /* best-effort */ }
    }
    logout()
    navigate('/login')
  }

  return (
    <header className="flex h-16 items-center justify-between border-b bg-white px-6">
      <h1 className="text-lg font-semibold text-gray-900">{title ?? 'Bank Admin Portal'}</h1>
      <Button variant="ghost" size="sm" onClick={handleLogout} className="gap-2 text-gray-600">
        <LogOut className="h-4 w-4" />
        Sign out
      </Button>
    </header>
  )
}
