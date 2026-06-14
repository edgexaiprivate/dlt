import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import toast from 'react-hot-toast'
import { Monitor, Plus, Wifi, WifiOff, Pencil, Trash2, Clock } from 'lucide-react'
import { devicesApi, restaurantsApi, type Device } from '@/api/services'
import { useAuthStore } from '@/store/authStore'
import Modal from '@/components/ui/Modal'
import ConfirmDialog from '@/components/ui/ConfirmDialog'
import { formatDistanceToNow } from 'date-fns'

const deviceSchema = z.object({
  name: z.string().min(1, 'Name required'),
  display_number: z.coerce.number().min(1),
  mac_address: z.string().trim().transform((v) => v || undefined).optional().superRefine((val, ctx) => {
    if (val && !/^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$/.test(val)) {
      ctx.addIssue({ code: z.ZodIssueCode.custom, message: 'Invalid MAC (XX:XX:XX:XX:XX:XX)' })
    }
  }),
  branch_id: z.coerce.number().min(1, 'Branch required'),
  screen_size_inch: z.coerce.number().optional(),
  theme_id: z.coerce.number().default(1),
  active_session: z.enum(['breakfast', 'lunch', 'dinner', 'all_day']).default('all_day'),
})
type DeviceForm = z.infer<typeof deviceSchema>

function DeviceFormModal({ open, onClose, device }: { open: boolean; onClose: () => void; device?: Device }) {
  const { user } = useAuthStore()
  const qc = useQueryClient()

  const { data: restaurants = [] } = useQuery({
    queryKey: ['restaurants'],
    queryFn: () => restaurantsApi.list().then((r) => r.data),
  })

  const [selectedRestaurant, setSelectedRestaurant] = useState(user?.restaurant_id ?? restaurants[0]?.id)
  const { data: branches = [] } = useQuery({
    queryKey: ['branches', selectedRestaurant],
    queryFn: () => restaurantsApi.branches(selectedRestaurant!).then((r) => r.data),
    enabled: !!selectedRestaurant,
  })

  const initialValues: DeviceForm = device
    ? {
        name: device.name,
        display_number: device.display_number,
        branch_id: device.branch_id,
        mac_address: device.mac_address,
        screen_size_inch: device.screen_size_inch ?? undefined,
        theme_id: device.theme_id,
        active_session: device.active_session,
      }
    : {
        name: '',
        display_number: 1,
        branch_id: selectedRestaurant ?? 0,
        theme_id: 1,
        active_session: 'all_day',
      }

  const { register, handleSubmit, formState: { errors } } = useForm<DeviceForm>({
    resolver: zodResolver(deviceSchema),
    defaultValues: initialValues,
  })

  const mutation = useMutation({
    mutationFn: (data: DeviceForm) =>
      device
        ? devicesApi.update(device.id, data)
        : devicesApi.create({
            ...data,
            ...(data.mac_address ? { mac_address: data.mac_address.toUpperCase() } : {}),
          }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['devices'] })
      toast.success(device ? 'Device updated' : 'Device registered')
      onClose()
    },
    onError: (err: any) => toast.error(err.response?.data?.detail || 'Failed to save device'),
  })

  return (
    <Modal open={open} onClose={onClose} title={device ? 'Edit Device' : 'Register New Device'}>
      <form onSubmit={handleSubmit((d) => mutation.mutate(d))} className="space-y-4">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="label">Device Name *</label>
            <input {...register('name')} className="input" placeholder="e.g. Main Hall TV 1" />
            {errors.name && <p className="text-red-400 text-xs mt-1">{errors.name.message}</p>}
          </div>
          <div>
            <label className="label">Display Number *</label>
            <input {...register('display_number')} type="number" className="input" placeholder="1" />
          </div>
        </div>

        <div>
          <label className="label">MAC Address (optional)</label>
          <input {...register('mac_address')} className="input font-mono" placeholder="AA:BB:CC:DD:EE:FF" />
          {errors.mac_address && <p className="text-red-400 text-xs mt-1">{errors.mac_address.message}</p>}
          <p className="text-xs text-zinc-600 mt-1">Leave blank for testing; otherwise use Android TV Settings → Network</p>
        </div>

        <div>
          <label className="label">Branch *</label>
          <select {...register('branch_id')} className="input">
            <option value="">Select branch...</option>
            {branches.map((b) => (
              <option key={b.id} value={b.id}>{b.name} {b.location ? `— ${b.location}` : ''}</option>
            ))}
          </select>
          {errors.branch_id && <p className="text-red-400 text-xs mt-1">{errors.branch_id.message}</p>}
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="label">Screen Size (inches)</label>
            <select {...register('screen_size_inch')} className="input">
              <option value="">Unknown</option>
              {[32, 43, 50, 55, 65, 75, 86].map((s) => (
                <option key={s} value={s}>{s}"</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Active Session</label>
            <select {...register('active_session')} className="input">
              <option value="all_day">All Day</option>
              <option value="breakfast">Breakfast Only</option>
              <option value="lunch">Lunch Only</option>
              <option value="dinner">Dinner Only</option>
            </select>
          </div>
        </div>

        <div>
          <label className="label">Theme</label>
          <select {...register('theme_id')} className="input">
            <option value={1}>Theme 1 — Classic Dark</option>
            <option value={2}>Theme 2 — Vibrant Orange</option>
            <option value={3}>Theme 3 — Minimal Light</option>
          </select>
        </div>

        <div className="flex flex-col gap-3 pt-2 sm:flex-row">
          <button type="button" onClick={onClose} className="btn-secondary flex-1 justify-center">Cancel</button>
          <button type="submit" disabled={mutation.isPending} className="btn-primary flex-1 justify-center">
            {mutation.isPending ? 'Saving...' : device ? 'Update Device' : 'Register Device'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

function DeviceCard({ device, onEdit, onDelete }: { device: Device; onEdit: () => void; onDelete: () => void }) {
  const isOnline = device.status === 'active'
  const lastSeen = device.last_seen
    ? formatDistanceToNow(new Date(device.last_seen), { addSuffix: true })
    : 'Never connected'

  return (
    <div className="card p-5 hover:border-white/[0.10] transition-all group">
      <div className="flex items-start justify-between gap-3 mb-4">
        <div className="w-12 h-12 rounded-xl bg-white/[0.04] border border-white/[0.08] flex items-center justify-center">
          <Monitor className={`w-6 h-6 ${isOnline ? 'text-emerald-400' : 'text-zinc-600'}`} />
        </div>
        <div className="flex items-center gap-1 sm:opacity-0 sm:transition-opacity sm:group-hover:opacity-100">
          <button onClick={onEdit} className="btn-ghost p-1.5"><Pencil className="w-4 h-4" /></button>
          <button onClick={onDelete} className="btn-ghost p-1.5 hover:text-red-400"><Trash2 className="w-4 h-4" /></button>
        </div>
      </div>

      <div className="space-y-1 mb-4">
        <h3 className="font-semibold text-zinc-100 break-words">{device.name}</h3>
        <p className="text-xs text-zinc-500 font-mono break-all">{device.mac_address || 'No MAC address'}</p>
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs mb-3">
        <div className="bg-white/[0.03] rounded-lg p-2">
          <p className="text-zinc-600">Display</p>
          <p className="text-zinc-300 font-medium">#{device.display_number}</p>
        </div>
        <div className="bg-white/[0.03] rounded-lg p-2">
          <p className="text-zinc-600">Size</p>
          <p className="text-zinc-300 font-medium">{device.screen_size_inch ? `${device.screen_size_inch}"` : '—'}</p>
        </div>
        <div className="bg-white/[0.03] rounded-lg p-2">
          <p className="text-zinc-600">Theme</p>
          <p className="text-zinc-300 font-medium">Theme {device.theme_id}</p>
        </div>
        <div className="bg-white/[0.03] rounded-lg p-2">
          <p className="text-zinc-600">Session</p>
          <p className="text-zinc-300 font-medium capitalize">{device.active_session.replace('_', ' ')}</p>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2 pt-3 border-t border-white/[0.05]">
        {isOnline ? (
          <Wifi className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
        ) : (
          <WifiOff className="w-3.5 h-3.5 text-zinc-600 flex-shrink-0" />
        )}
        <span className={`text-xs font-medium ${isOnline ? 'text-emerald-400' : 'text-zinc-500'}`}>
          {isOnline ? 'Online' : 'Offline'}
        </span>
        <span className="text-zinc-700">·</span>
        <Clock className="w-3 h-3 text-zinc-700" />
        <span className="text-xs text-zinc-600">{lastSeen}</span>
      </div>
    </div>
  )
}

export default function DevicesPage() {
  const [addDevice, setAddDevice] = useState(false)
  const [editDevice, setEditDevice] = useState<Device | null>(null)
  const [deleteDevice, setDeleteDevice] = useState<Device | null>(null)
  const qc = useQueryClient()

  const { data: devices = [], isLoading } = useQuery({
    queryKey: ['devices'],
    queryFn: () => devicesApi.list().then((r) => r.data),
    refetchInterval: 30_000, // Poll every 30s for status
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => devicesApi.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['devices'] })
      toast.success('Device removed'); setDeleteDevice(null)
    },
  })

  const onlineCount = devices.filter((d) => d.status === 'active').length

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold text-zinc-50 sm:text-3xl">Devices</h1>
          <p className="text-zinc-500 text-sm mt-1">
            {onlineCount} online · {devices.length - onlineCount} offline · {devices.length} total
          </p>
        </div>
        <button onClick={() => setAddDevice(true)} className="btn-primary w-full sm:w-auto">
          <Plus className="w-4 h-4" /> Register Device
        </button>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="card h-48 animate-pulse opacity-40" />
          ))}
        </div>
      ) : devices.length === 0 ? (
        <div className="card p-6 text-center sm:p-16">
          <Monitor className="w-16 h-16 mx-auto mb-4 text-zinc-700" />
          <h2 className="text-xl font-semibold text-zinc-400 mb-2">No devices registered</h2>
          <p className="text-zinc-600 text-sm mb-6">Register your Android TV devices to push menus to them.</p>
          <button onClick={() => setAddDevice(true)} className="btn-primary mx-auto">
            <Plus className="w-4 h-4" /> Register First Device
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {devices.map((device) => (
            <DeviceCard
              key={device.id}
              device={device}
              onEdit={() => setEditDevice(device)}
              onDelete={() => setDeleteDevice(device)}
            />
          ))}
        </div>
      )}

      {addDevice && <DeviceFormModal open={addDevice} onClose={() => setAddDevice(false)} />}
      {editDevice && <DeviceFormModal open={!!editDevice} onClose={() => setEditDevice(null)} device={editDevice} />}
      <ConfirmDialog
        open={!!deleteDevice}
        onClose={() => setDeleteDevice(null)}
        onConfirm={() => deleteDevice && deleteMutation.mutate(deleteDevice.id)}
        title="Remove Device"
        description={`Remove "${deleteDevice?.name}" from the system?`}
        loading={deleteMutation.isPending}
      />
    </div>
  )
}
