import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import toast from 'react-hot-toast'
import { Building2, Plus, Pencil, MapPin, Globe } from 'lucide-react'
import { restaurantsApi, type Restaurant } from '@/api/services'
import Modal from '@/components/ui/Modal'

const schema = z.object({
  name: z.string().min(1, 'Name required'),
  slug: z.string().optional(),
  logo_url: z.string().url('Must be a valid URL').optional().or(z.literal('')),
})
type FormData = z.infer<typeof schema>

function RestaurantFormModal({ open, onClose, restaurant }: { open: boolean; onClose: () => void; restaurant?: Restaurant }) {
  const qc = useQueryClient()
  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: restaurant
      ? {
          name: restaurant.name,
          slug: restaurant.slug ?? '',
          logo_url: restaurant.logo_url ?? '',
        }
      : { name: '', slug: '', logo_url: '' },
  })

  const mutation = useMutation({
    mutationFn: (data: FormData) =>
      restaurant
        ? restaurantsApi.update(restaurant.id, data)
        : restaurantsApi.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['restaurants'] })
      toast.success(restaurant ? 'Restaurant updated' : 'Restaurant created')
      onClose()
    },
    onError: (err: any) => toast.error(err.response?.data?.detail || 'Failed'),
  })

  return (
    <Modal open={open} onClose={onClose} title={restaurant ? 'Edit Restaurant' : 'Add Restaurant'}>
      <form onSubmit={handleSubmit((d) => mutation.mutate(d))} className="space-y-4">
        <div>
          <label className="label">Restaurant Name *</label>
          <input {...register('name')} className="input" placeholder="Hotel Saravana Bhavan" />
          {errors.name && <p className="text-red-400 text-xs mt-1">{errors.name.message}</p>}
        </div>
        <div>
          <label className="label">Slug (URL identifier)</label>
          <input {...register('slug')} className="input font-mono" placeholder="auto-generated from name" />
        </div>
        <div>
          <label className="label">Logo URL</label>
          <input {...register('logo_url')} className="input" placeholder="https://..." />
          {errors.logo_url && <p className="text-red-400 text-xs mt-1">{errors.logo_url.message}</p>}
        </div>
        <div className="flex flex-col gap-3 pt-2 sm:flex-row">
          <button type="button" onClick={onClose} className="btn-secondary flex-1 justify-center">Cancel</button>
          <button type="submit" disabled={mutation.isPending} className="btn-primary flex-1 justify-center">
            {mutation.isPending ? 'Saving...' : restaurant ? 'Update' : 'Create'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

export default function RestaurantsPage() {
  const [addModal, setAddModal] = useState(false)
  const [editModal, setEditModal] = useState<Restaurant | null>(null)

  const { data: restaurants = [], isLoading } = useQuery({
    queryKey: ['restaurants'],
    queryFn: () => restaurantsApi.list().then((r) => r.data),
  })

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold text-zinc-50 sm:text-3xl">Restaurants</h1>
          <p className="text-zinc-500 text-sm mt-1">{restaurants.length} registered</p>
        </div>
        <button onClick={() => setAddModal(true)} className="btn-primary w-full sm:w-auto">
          <Plus className="w-4 h-4" /> Add Restaurant
        </button>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2].map((i) => <div key={i} className="card h-20 animate-pulse opacity-40" />)}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {restaurants.map((r) => (
            <div key={r.id} className="card p-5 hover:border-white/10 transition-all group">
              <div className="flex items-start justify-between mb-3">
                <div className="w-11 h-11 rounded-xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center">
                  {r.logo_url ? (
                    <img src={r.logo_url} alt={r.name} className="w-8 h-8 object-contain rounded" />
                  ) : (
                    <Building2 className="w-5 h-5 text-brand-400" />
                  )}
                </div>
                <button onClick={() => setEditModal(r)} className="btn-ghost p-1.5 sm:opacity-0 sm:transition-opacity sm:group-hover:opacity-100">
                  <Pencil className="w-4 h-4" />
                </button>
              </div>
              <h3 className="font-semibold text-zinc-100 mb-1 break-words">{r.name}</h3>
              <div className="flex items-center gap-1 text-xs text-zinc-500 mb-3">
                <Globe className="w-3 h-3" />
                <span className="font-mono break-all">{r.slug}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className={`text-xs px-2 py-0.5 rounded-full border ${r.is_active ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-zinc-500/10 text-zinc-500 border-zinc-500/20'}`}>
                  {r.is_active ? 'Active' : 'Inactive'}
                </span>
                <span className="text-xs text-zinc-600">ID: {r.id}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {addModal && <RestaurantFormModal open={addModal} onClose={() => setAddModal(false)} />}
      {editModal && <RestaurantFormModal open={!!editModal} onClose={() => setEditModal(null)} restaurant={editModal} />}
    </div>
  )
}
