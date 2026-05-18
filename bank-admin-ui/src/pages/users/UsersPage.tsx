import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { UserPlus } from 'lucide-react'
import { usersApi, type UserCreate, type UserUpdate } from '@/api/users'
import type { UserOut } from '@/api/auth'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { UserRoleBadge } from '@/components/common/StatusBadge'
import { Badge } from '@/components/ui/badge'
import { formatDate } from '@/lib/utils'
import { toast } from '@/components/ui/toaster'

function formatApiError(err: any): string {
  const detail = err?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((d) => {
        const field = Array.isArray(d?.loc) ? d.loc.filter((p: any) => p !== 'body').join('.') : ''
        const msg = d?.msg ?? 'Invalid value'
        return field ? `${field}: ${msg}` : msg
      })
      .join('; ')
  }
  return err?.message ?? 'Something went wrong'
}

function UserModal({ user, onClose }: { user?: UserOut; onClose: () => void }) {
  const queryClient = useQueryClient()
  const { data: roles } = useQuery({ queryKey: ['roles'], queryFn: () => usersApi.roles() })
  const [form, setForm] = useState({
    email: user?.email ?? '',
    password: '',
    full_name: user?.full_name ?? '',
    role_id: user?.role.id ?? 1,
    is_active: user?.is_active ?? true,
  })

  const mutation = useMutation({
    mutationFn: () => user
      ? usersApi.update(user.id, { full_name: form.full_name, role_id: form.role_id, is_active: form.is_active })
      : usersApi.create({ email: form.email, password: form.password, full_name: form.full_name, role_id: form.role_id }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      toast({ title: user ? 'User updated' : 'User created' })
      onClose()
    },
    onError: (e: any) => toast({ title: 'Error', description: formatApiError(e), variant: 'destructive' }),
  })

  return (
    <DialogContent className="max-w-md">
      <DialogHeader><DialogTitle>{user ? 'Edit User' : 'Create User'}</DialogTitle></DialogHeader>
      <div className="space-y-4">
        {!user && (
          <>
            <div className="space-y-1">
              <Label>Email</Label>
              <Input type="email" value={form.email} onChange={(e) => setForm(f => ({ ...f, email: e.target.value }))} />
            </div>
            <div className="space-y-1">
              <Label>Password</Label>
              <Input type="password" value={form.password} onChange={(e) => setForm(f => ({ ...f, password: e.target.value }))} />
            </div>
          </>
        )}
        <div className="space-y-1">
          <Label>Full Name</Label>
          <Input value={form.full_name} onChange={(e) => setForm(f => ({ ...f, full_name: e.target.value }))} />
        </div>
        <div className="space-y-1">
          <Label>Role</Label>
          <select value={form.role_id} onChange={(e) => setForm(f => ({ ...f, role_id: Number(e.target.value) }))} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm">
            {roles?.map((r) => <option key={r.id} value={r.id}>{r.name.replace('_', ' ')}</option>)}
          </select>
        </div>
        {user && (
          <div className="flex items-center gap-2">
            <input type="checkbox" id="is_active" checked={form.is_active} onChange={(e) => setForm(f => ({ ...f, is_active: e.target.checked }))} className="h-4 w-4 rounded border-gray-300" />
            <Label htmlFor="is_active">Active</Label>
          </div>
        )}
      </div>
      <DialogFooter>
        <Button variant="outline" onClick={onClose}>Cancel</Button>
        <Button
          onClick={() => mutation.mutate()}
          disabled={
            mutation.isPending ||
            (!user && (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email) || form.password.length < 1 || !form.full_name.trim()))
          }
        >
          {mutation.isPending ? 'Saving…' : user ? 'Save Changes' : 'Create User'}
        </Button>
      </DialogFooter>
    </DialogContent>
  )
}

export default function UsersPage() {
  const [page, setPage] = useState(1)
  const [editing, setEditing] = useState<UserOut | undefined>()
  const [creating, setCreating] = useState(false)

  const { data, isLoading } = useQuery({ queryKey: ['users', page], queryFn: () => usersApi.list(page, 20) })

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button size="sm" onClick={() => setCreating(true)} className="gap-2">
          <UserPlus className="h-4 w-4" /> Invite User
        </Button>
      </div>

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex items-center justify-center h-40 text-muted-foreground">Loading…</div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50">
                  <th className="px-4 py-3 text-left font-medium text-gray-500">User</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Role</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Status</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Last Login</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Created</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-500">Actions</th>
                </tr>
              </thead>
              <tbody>
                {data?.items.map((user) => (
                  <tr key={user.id} className="border-b last:border-0">
                    <td className="px-4 py-3">
                      <p className="font-medium">{user.full_name || '—'}</p>
                      <p className="text-xs text-muted-foreground">{user.email}</p>
                    </td>
                    <td className="px-4 py-3"><UserRoleBadge role={user.role.name} /></td>
                    <td className="px-4 py-3">
                      <Badge variant={user.is_active ? 'success' : 'muted'} className="text-xs">{user.is_active ? 'Active' : 'Inactive'}</Badge>
                    </td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">{formatDate(user.last_login_at)}</td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">{formatDate(user.created_at)}</td>
                    <td className="px-4 py-3 text-right">
                      <Button variant="outline" size="sm" onClick={() => setEditing(user)}>Edit</Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>

      <Dialog open={creating || !!editing} onOpenChange={(open) => { if (!open) { setCreating(false); setEditing(undefined) } }}>
        {(creating || editing) && <UserModal user={editing} onClose={() => { setCreating(false); setEditing(undefined) }} />}
      </Dialog>
    </div>
  )
}
