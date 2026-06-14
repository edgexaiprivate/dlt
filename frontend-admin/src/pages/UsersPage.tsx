import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import toast from 'react-hot-toast'
import { Users, Plus, Pencil, UserX, ShieldCheck, Shield, User as UserIcon } from 'lucide-react'
import { usersApi, restaurantsApi, type User } from '@/api/services'
import Modal from '@/components/ui/Modal'
import ConfirmDialog from '@/components/ui/ConfirmDialog'
import { formatDistanceToNow } from 'date-fns'

const schema = z.object({
  username: z.string().min(1),
  email: z.string().email(),
  full_name: z.string().min(1),
  password: z.string().min(8).optional().or(z.literal('')),
  role: z.enum(['super_admin', 'manager', 'staff']),
  restaurant_id: z.coerce.number().optional(),
})
type FormData = z.infer<typeof schema>

function UserFormModal({ open, onClose, user }: { open: boolean; onClose: () => void; user?: User }) {
  const qc = useQueryClient()
  const { data: restaurants = [] } = useQuery({
    queryKey: ['restaurants'],
    queryFn: () => restaurantsApi.list().then((r) => r.data),
  })
  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: user
      ? {
          username: user.username,
          email: user.email,
          full_name: user.full_name,
          password: '',
          role: user.role,
          restaurant_id: user.restaurant_id ?? undefined,
        }
      : {
          username: '',
          email: '',
          full_name: '',
          password: '',
          role: 'staff',
          restaurant_id: undefined,
        },
  })

  const mutation = useMutation({
    mutationFn: (data: FormData) => {
      const payload: any = { ...data }
      if (!payload.password) delete payload.password
      return user ? usersApi.update(user.id, payload) : usersApi.create(payload)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['users'] })
      toast.success(user ? 'User updated' : 'User created')
      onClose()
    },
    onError: (err: any) => toast.error(err.response?.data?.detail || 'Failed'),
  })

  return (
    <Modal open={open} onClose={onClose} title={user ? 'Edit User' : 'Add User'}>
      <form onSubmit={handleSubmit((d) => mutation.mutate(d))} className="space-y-4">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="label">Username *</label>
            <input {...register('username')} className="input" placeholder="johndoe" />
            {errors.username && <p className="text-red-400 text-xs mt-1">{errors.username.message}</p>}
          </div>
          <div>
            <label className="label">Role *</label>
            <select {...register('role')} className="input">
              <option value="staff">Staff</option>
              <option value="manager">Manager</option>
              <option value="super_admin">Super Admin</option>
            </select>
          </div>
        </div>
        <div>
          <label className="label">Full Name *</label>
          <input {...register('full_name')} className="input" placeholder="John Doe" />
        </div>
        <div>
          <label className="label">Email *</label>
          <input {...register('email')} type="email" className="input" placeholder="john@example.com" />
          {errors.email && <p className="text-red-400 text-xs mt-1">{errors.email.message}</p>}
        </div>
        <div>
          <label className="label">{user ? 'New Password (leave blank to keep)' : 'Password *'}</label>
          <input {...register('password')} type="password" className="input" placeholder="Min 8 characters" />
          {errors.password && <p className="text-red-400 text-xs mt-1">{errors.password.message}</p>}
        </div>
        <div>
          <label className="label">Restaurant</label>
          <select {...register('restaurant_id')} className="input">
            <option value="">None (Super Admin)</option>
            {restaurants.map((r) => (
              <option key={r.id} value={r.id}>{r.name}</option>
            ))}
          </select>
        </div>
        <div className="flex flex-col gap-3 pt-2 sm:flex-row">
          <button type="button" onClick={onClose} className="btn-secondary flex-1 justify-center">Cancel</button>
          <button type="submit" disabled={mutation.isPending} className="btn-primary flex-1 justify-center">
            {mutation.isPending ? 'Saving...' : user ? 'Update' : 'Create User'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

function RoleBadge({ role }: { role: User['role'] }) {
  const map = {
    super_admin: { label: 'Super Admin', cls: 'bg-brand-500/10 text-brand-400 border-brand-500/20', icon: ShieldCheck },
    manager: { label: 'Manager', cls: 'bg-blue-500/10 text-blue-400 border-blue-500/20', icon: Shield },
    staff: { label: 'Staff', cls: 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20', icon: UserIcon },
  }
  const { label, cls, icon: Icon } = map[role]
  return (
    <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full border ${cls}`}>
      <Icon className="w-3 h-3" />{label}
    </span>
  )
}

export default function UsersPage() {
  const [addModal, setAddModal] = useState(false)
  const [editModal, setEditModal] = useState<User | null>(null)
  const [deactivateModal, setDeactivateModal] = useState<User | null>(null)
  const qc = useQueryClient()

  const { data: users = [], isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: () => usersApi.list().then((r) => r.data),
  })

  const deactivateMutation = useMutation({
    mutationFn: (id: number) => usersApi.deactivate(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['users'] })
      toast.success('User deactivated'); setDeactivateModal(null)
    },
  })

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold text-zinc-50 sm:text-3xl">Users</h1>
          <p className="text-zinc-500 text-sm mt-1">{users.filter((u) => u.is_active).length} active</p>
        </div>
        <button onClick={() => setAddModal(true)} className="btn-primary w-full sm:w-auto">
          <Plus className="w-4 h-4" /> Add User
        </button>
      </div>

      <div className="card overflow-x-auto">
        <table className="w-full min-w-[720px] text-sm">
          <thead>
            <tr className="border-b border-white/[0.06]">
              <th className="text-left px-5 py-3.5 text-xs font-medium text-zinc-500 uppercase tracking-wide">User</th>
              <th className="text-left px-5 py-3.5 text-xs font-medium text-zinc-500 uppercase tracking-wide">Role</th>
              <th className="text-left px-5 py-3.5 text-xs font-medium text-zinc-500 uppercase tracking-wide">Last Login</th>
              <th className="text-left px-5 py-3.5 text-xs font-medium text-zinc-500 uppercase tracking-wide">Status</th>
              <th className="w-20" />
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.04]">
            {isLoading
              ? [1, 2, 3].map((i) => (
                  <tr key={i}><td colSpan={5} className="px-5 py-4"><div className="h-4 bg-white/[0.04] rounded animate-pulse w-3/4" /></td></tr>
                ))
              : users.map((user) => (
                  <tr key={user.id} className="hover:bg-white/[0.02] transition-colors group">
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-brand-500/15 border border-brand-500/20 flex items-center justify-center text-brand-400 text-sm font-bold uppercase flex-shrink-0">
                          {user.full_name[0]}
                        </div>
                        <div className="min-w-0">
                          <p className="font-medium text-zinc-200">{user.full_name}</p>
                          <p className="text-xs text-zinc-500 break-all">{user.email}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-5 py-3.5"><RoleBadge role={user.role} /></td>
                    <td className="px-5 py-3.5 text-zinc-500 text-xs">
                      {user.last_login ? formatDistanceToNow(new Date(user.last_login), { addSuffix: true }) : 'Never'}
                    </td>
                    <td className="px-5 py-3.5">
                      <span className={`text-xs px-2 py-0.5 rounded-full border ${user.is_active ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-red-500/10 text-red-400 border-red-500/20'}`}>
                        {user.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-1 sm:opacity-0 sm:transition-opacity sm:group-hover:opacity-100">
                        <button onClick={() => setEditModal(user)} className="btn-ghost p-1.5"><Pencil className="w-3.5 h-3.5" /></button>
                        {user.is_active && (
                          <button onClick={() => setDeactivateModal(user)} className="btn-ghost p-1.5 hover:text-red-400">
                            <UserX className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
            }
          </tbody>
        </table>
      </div>

      {addModal && <UserFormModal open={addModal} onClose={() => setAddModal(false)} />}
      {editModal && <UserFormModal open={!!editModal} onClose={() => setEditModal(null)} user={editModal} />}
      <ConfirmDialog
        open={!!deactivateModal}
        onClose={() => setDeactivateModal(null)}
        onConfirm={() => deactivateModal && deactivateMutation.mutate(deactivateModal.id)}
        title="Deactivate User"
        description={`Deactivate "${deactivateModal?.full_name}"? They won't be able to log in.`}
        confirmLabel="Deactivate"
        loading={deactivateMutation.isPending}
      />
    </div>
  )
}
