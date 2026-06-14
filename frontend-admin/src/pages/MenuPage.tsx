import { useEffect, useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import toast from 'react-hot-toast'
import {
  Plus, Pencil, Trash2, ChevronRight, ChevronDown, UtensilsCrossed,
  Leaf, Drumstick, Star, Eye, EyeOff, GripVertical, Image,
  RefreshCw, CheckCircle2, Clock, XCircle,
  Layers, Tag, Package, BookOpen, Tv, Search, X,
  Store, AlertCircle, Zap, ToggleLeft, ToggleRight
} from 'lucide-react'
import {
  menuApi,
  restaurantsApi,
  type MenuGroup,
  type MenuSubGroup,
  type MenuItem,
  type Restaurant,
} from '@/api/services'
import { useAuthStore } from '@/store/authStore'
import Modal from '@/components/ui/Modal'
import ConfirmDialog from '@/components/ui/ConfirmDialog'
import RestaurantSelector from '@/components/ui/RestaurantSelector'

import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from '@dnd-kit/core'
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'

// ─── Sortable Wrapper Component ───────────────────────────────────────────────
interface SortableItemProps {
  id: number
  children: (props: {
    ref: (node: HTMLElement | null) => void
    style: React.CSSProperties
    dragHandleProps: any
  }) => React.ReactNode
}

function SortableItem({ id, children }: SortableItemProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id })

  const style: React.CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
    position: 'relative',
  }

  return <>{children({ ref: setNodeRef, style, dragHandleProps: { ...attributes, ...listeners } })}</>
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
function StatusBadge({ status }: { status: MenuItem['status'] }) {
  if (status === 'available')
    return (
      <span className="badge-available flex items-center gap-1">
        <CheckCircle2 className="w-3 h-3" /> Available
      </span>
    )
  if (status === 'today_special')
    return (
      <span className="badge-special flex items-center gap-1">
        <Star className="w-3 h-3" /> Special
      </span>
    )
  return (
    <span className="badge-unavailable flex items-center gap-1">
      <XCircle className="w-3 h-3" /> Off
    </span>
  )
}

function SessionPill({ session }: { session: MenuItem['session'] }) {
  if (session === 'all_day') return null
  const colors: Record<string, string> = {
    breakfast: 'bg-sky-500/10 text-sky-400 border-sky-500/20',
    lunch: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    dinner: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  }
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full border capitalize ${colors[session] ?? ''}`}>
      <Clock className="w-2.5 h-2.5 inline mr-1" />
      {session}
    </span>
  )
}


// ─── Group Form ────────────────────────────────────────────────────────────────
const groupSchema = z.object({
  name: z.string().min(1, 'Name required'),
  name_local: z.string().optional(),
  instruction: z.string().optional(),
  image_url: z.string().url('Must be a valid URL').optional().or(z.literal('')),
  sequence: z.coerce.number().default(0),
  is_active: z.boolean().default(true),
})
type GroupForm = z.infer<typeof groupSchema>

function GroupFormModal({
  open,
  onClose,
  restaurantId,
  group,
}: {
  open: boolean
  onClose: () => void
  restaurantId: number
  group?: MenuGroup
}) {
  const qc = useQueryClient()
  const {
    register,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors },
  } = useForm<GroupForm>({
    resolver: zodResolver(groupSchema),
    defaultValues: group
      ? {
          name: group.name,
          name_local: group.name_local ?? '',
          instruction: group.instruction ?? '',
          image_url: group.image_url ?? '',
          sequence: group.sequence,
          is_active: group.is_active,
        }
      : { sequence: 0, is_active: true },
  })

  const imageUrl = watch('image_url')
  const isActive = watch('is_active')

  const mutation = useMutation({
    mutationFn: (data: GroupForm) => {
      const payload = {
        ...data,
        image_url: data.image_url || null,
        name_local: data.name_local || null,
        instruction: data.instruction || null,
      }
      return group
        ? menuApi.updateGroup(group.id, payload)
        : menuApi.createGroup(restaurantId, payload)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['menu-groups'] })
      toast.success(group ? 'Category updated' : 'Category created')
      reset()
      onClose()
    },
    onError: () => toast.error('Failed to save category'),
  })

  return (
    <Modal open={open} onClose={onClose} title={group ? 'Edit Category' : 'Add Category'}>
      <form onSubmit={handleSubmit((d) => mutation.mutate(d))} className="space-y-4">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="label">Category Name *</label>
            <input {...register('name')} className="input" placeholder="e.g. South Indian" />
            {errors.name && <p className="text-red-400 text-xs mt-1">{errors.name.message}</p>}
          </div>
          <div>
            <label className="label">Local Language Name</label>
            <input {...register('name_local')} className="input" placeholder="e.g. தென்னிந்திய" />
          </div>
        </div>

        <div>
          <label className="label">Instruction / Tag</label>
          <input
            {...register('instruction')}
            className="input"
            placeholder="e.g. Pure Veg | GST Included"
          />
        </div>

        <div>
          <label className="label">
            <Image className="w-3.5 h-3.5 inline mr-1" />
            Category Image URL
          </label>
          <input
            {...register('image_url')}
            className="input"
            placeholder="https://example.com/image.jpg"
          />
          {errors.image_url && (
            <p className="text-red-400 text-xs mt-1">{errors.image_url.message}</p>
          )}
          {imageUrl && !errors.image_url && (
            <div className="mt-2 rounded-xl overflow-hidden border border-white/10 h-24">
              <img
                src={imageUrl}
                alt="preview"
                className="w-full h-full object-cover"
                onError={(e) => (e.currentTarget.style.display = 'none')}
              />
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="label">Display Order</label>
            <input {...register('sequence')} type="number" className="input" placeholder="0" />
          </div>
          <div>
            <label className="label">Visibility</label>
            <button
              type="button"
              onClick={() => setValue('is_active', !isActive)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium border transition-all w-full justify-center ${
                isActive
                  ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-400'
                  : 'bg-zinc-700/30 border-white/10 text-zinc-500'
              }`}
            >
              {isActive ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
              {isActive ? 'Visible' : 'Hidden'}
            </button>
          </div>
        </div>

        <div className="flex flex-col gap-3 pt-2 sm:flex-row">
          <button type="button" onClick={onClose} className="btn-secondary flex-1 justify-center">
            Cancel
          </button>
          <button
            type="submit"
            disabled={mutation.isPending}
            className="btn-primary flex-1 justify-center"
          >
            {mutation.isPending ? 'Saving...' : group ? 'Update' : 'Create'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

// ─── SubGroup Form ─────────────────────────────────────────────────────────────
const subGroupSchema = z.object({
  name: z.string().min(1, 'Name required'),
  name_local: z.string().optional(),
  sequence: z.coerce.number().default(0),
  is_active: z.boolean().default(true),
})
type SubGroupForm = z.infer<typeof subGroupSchema>

function SubGroupFormModal({
  open,
  onClose,
  groupId,
  subGroup,
}: {
  open: boolean
  onClose: () => void
  groupId: number
  subGroup?: MenuSubGroup
}) {
  const qc = useQueryClient()
  const {
    register,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors },
  } = useForm<SubGroupForm>({
    resolver: zodResolver(subGroupSchema),
    defaultValues: subGroup
      ? {
          name: subGroup.name,
          name_local: subGroup.name_local ?? '',
          sequence: subGroup.sequence,
          is_active: subGroup.is_active,
        }
      : { sequence: 0, is_active: true },
  })

  const isActive = watch('is_active')

  const mutation = useMutation({
    mutationFn: (data: SubGroupForm) => {
      const payload = { ...data, name_local: data.name_local || null }
      return subGroup
        ? menuApi.updateSubGroup(subGroup.id, payload)
        : menuApi.createSubGroup(groupId, payload)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['menu-subgroups'] })
      toast.success(subGroup ? 'Sub-category updated' : 'Sub-category created')
      reset()
      onClose()
    },
    onError: () => toast.error('Failed to save sub-category'),
  })

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={subGroup ? 'Edit Sub-Category' : 'Add Sub-Category'}
      size="sm"
    >
      <form onSubmit={handleSubmit((d) => mutation.mutate(d))} className="space-y-4">
        <div>
          <label className="label">Name *</label>
          <input {...register('name')} className="input" placeholder="e.g. Dosa, Idli..." />
          {errors.name && <p className="text-red-400 text-xs mt-1">{errors.name.message}</p>}
        </div>
        <div>
          <label className="label">Local Name</label>
          <input {...register('name_local')} className="input" placeholder="Local language" />
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="label">Display Order</label>
            <input {...register('sequence')} type="number" className="input" />
          </div>
          <div>
            <label className="label">Visibility</label>
            <button
              type="button"
              onClick={() => setValue('is_active', !isActive)}
              className={`flex items-center gap-2 px-3 py-2.5 rounded-xl text-sm font-medium border transition-all w-full justify-center ${
                isActive
                  ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-400'
                  : 'bg-zinc-700/30 border-white/10 text-zinc-500'
              }`}
            >
              {isActive ? <ToggleRight className="w-4 h-4" /> : <ToggleLeft className="w-4 h-4" />}
              {isActive ? 'Active' : 'Hidden'}
            </button>
          </div>
        </div>
        <div className="flex flex-col gap-3 pt-2 sm:flex-row">
          <button type="button" onClick={onClose} className="btn-secondary flex-1 justify-center">
            Cancel
          </button>
          <button
            type="submit"
            disabled={mutation.isPending}
            className="btn-primary flex-1 justify-center"
          >
            {mutation.isPending ? 'Saving...' : subGroup ? 'Update' : 'Create'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

// ─── Item Form ─────────────────────────────────────────────────────────────────
const itemSchema = z.object({
  name: z.string().min(1, 'Name required'),
  name_local: z.string().optional(),
  price: z.coerce.number().min(0, 'Price must be >= 0'),
  description: z.string().optional(),
  image_url: z.string().url('Must be a valid URL').optional().or(z.literal('')),
  is_veg: z.boolean().default(true),
  status: z.enum(['available', 'not_available', 'today_special']).default('available'),
  session: z.enum(['breakfast', 'lunch', 'dinner', 'all_day']).default('all_day'),
  sequence: z.coerce.number().default(0),
})
type ItemForm = z.infer<typeof itemSchema>

function ItemFormModal({
  open,
  onClose,
  subGroupId,
  item,
}: {
  open: boolean
  onClose: () => void
  subGroupId: number
  item?: MenuItem
}) {
  const qc = useQueryClient()
  const {
    register,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors },
  } = useForm<ItemForm>({
    resolver: zodResolver(itemSchema),
    defaultValues: item
      ? {
          name: item.name,
          name_local: item.name_local ?? '',
          price: item.price,
          description: item.description ?? '',
          image_url: item.image_url ?? '',
          is_veg: item.is_veg,
          status: item.status,
          session: item.session,
          sequence: item.sequence,
        }
      : { is_veg: true, status: 'available', session: 'all_day', sequence: 0 },
  })
  const isVeg = watch('is_veg')
  const imageUrl = watch('image_url')

  const mutation = useMutation({
    mutationFn: (data: ItemForm) => {
      const payload = {
        ...data,
        name_local: data.name_local || null,
        description: data.description || null,
        image_url: data.image_url || null,
      }
      return item
        ? menuApi.updateItem(item.id, payload)
        : menuApi.createItem(subGroupId, payload)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['menu-items'] })
      toast.success(item ? 'Item updated' : 'Item added')
      reset()
      onClose()
    },
    onError: () => toast.error('Failed to save item'),
  })

  return (
    <Modal open={open} onClose={onClose} title={item ? 'Edit Item' : 'Add Menu Item'} size="lg">
      <form onSubmit={handleSubmit((d) => mutation.mutate(d))} className="space-y-4">
        {/* Names */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="label">Item Name *</label>
            <input {...register('name')} className="input" placeholder="e.g. Masala Dosa" />
            {errors.name && <p className="text-red-400 text-xs mt-1">{errors.name.message}</p>}
          </div>
          <div>
            <label className="label">Local Name</label>
            <input {...register('name_local')} className="input" placeholder="Local language" />
          </div>
        </div>

        {/* Price + Order */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="label">Price (₹) *</label>
            <input
              {...register('price')}
              type="number"
              step="0.50"
              className="input"
              placeholder="0.00"
            />
            {errors.price && <p className="text-red-400 text-xs mt-1">{errors.price.message}</p>}
          </div>
          <div>
            <label className="label">Display Order</label>
            <input {...register('sequence')} type="number" className="input" />
          </div>
        </div>

        {/* Description */}
        <div>
          <label className="label">Description</label>
          <textarea
            {...register('description')}
            className="input h-16 resize-none"
            placeholder="Optional description..."
          />
        </div>

        {/* Image URL */}
        <div>
          <label className="label">
            <Image className="w-3.5 h-3.5 inline mr-1" />
            Item Image URL
          </label>
          <input
            {...register('image_url')}
            className="input"
            placeholder="https://example.com/item.jpg"
          />
          {errors.image_url && (
            <p className="text-red-400 text-xs mt-1">{errors.image_url.message}</p>
          )}
          {imageUrl && !errors.image_url && (
            <div className="mt-2 rounded-xl overflow-hidden border border-white/10 h-20">
              <img
                src={imageUrl}
                alt="preview"
                className="w-full h-full object-cover"
                onError={(e) => (e.currentTarget.style.display = 'none')}
              />
            </div>
          )}
        </div>

        {/* Session + Status */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="label">Session</label>
            <select {...register('session')} className="input">
              <option value="all_day">All Day</option>
              <option value="breakfast">Breakfast</option>
              <option value="lunch">Lunch</option>
              <option value="dinner">Dinner</option>
            </select>
          </div>
          <div>
            <label className="label">Status</label>
            <select {...register('status')} className="input">
              <option value="available">Available</option>
              <option value="today_special">Today's Special</option>
              <option value="not_available">Not Available</option>
            </select>
          </div>
        </div>

        {/* Veg / Non-veg */}
        <div>
          <label className="label">Type</label>
          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => setValue('is_veg', true)}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium border transition-all ${
                isVeg
                  ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-400'
                  : 'border-white/10 text-zinc-500 hover:border-white/20'
              }`}
            >
              <Leaf className="w-4 h-4" /> Veg
            </button>
            <button
              type="button"
              onClick={() => setValue('is_veg', false)}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium border transition-all ${
                !isVeg
                  ? 'bg-red-500/15 border-red-500/40 text-red-400'
                  : 'border-white/10 text-zinc-500 hover:border-white/20'
              }`}
            >
              <Drumstick className="w-4 h-4" /> Non-Veg
            </button>
          </div>
        </div>

        <div className="flex flex-col gap-3 pt-2 sm:flex-row">
          <button type="button" onClick={onClose} className="btn-secondary flex-1 justify-center">
            Cancel
          </button>
          <button
            type="submit"
            disabled={mutation.isPending}
            className="btn-primary flex-1 justify-center"
          >
            {mutation.isPending ? 'Saving...' : item ? 'Update Item' : 'Add Item'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

// ─── Item Row ──────────────────────────────────────────────────────────────────
function ItemRow({
  item,
  onEdit,
  onDelete,
  subGroupId,
  searchQuery,
  dragHandleProps,
}: {
  item: MenuItem
  onEdit: () => void
  onDelete: () => void
  subGroupId: number
  searchQuery: string
  dragHandleProps?: any
}) {
  const qc = useQueryClient()

  const quickStatusCycle = useMutation({
    mutationFn: ({ id, status }: { id: number; status: MenuItem['status'] }) =>
      menuApi.updateItem(id, { status }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['menu-items', subGroupId] }),
    onError: () => toast.error('Failed to update status'),
  })

  const nextStatus: Record<MenuItem['status'], MenuItem['status']> = {
    available: 'today_special',
    today_special: 'not_available',
    not_available: 'available',
  }

  // Highlight search matches
  const highlight = (text: string) => {
    if (!searchQuery) return text
    const idx = text.toLowerCase().indexOf(searchQuery.toLowerCase())
    if (idx === -1) return text
    return (
      <>
        {text.slice(0, idx)}
        <mark className="bg-orange-500/30 text-orange-200 rounded px-0.5">
          {text.slice(idx, idx + searchQuery.length)}
        </mark>
        {text.slice(idx + searchQuery.length)}
      </>
    )
  }

  return (
    <div className="flex flex-wrap items-start gap-3 rounded-xl border border-white/[0.04] bg-white/[0.02] px-3 py-2.5 transition-all hover:border-white/[0.1] hover:bg-white/[0.04] sm:flex-nowrap sm:items-center group">
      <GripVertical
        {...dragHandleProps}
        className={`hidden w-4 flex-shrink-0 cursor-grab text-zinc-700 hover:text-zinc-400 sm:block active:cursor-grabbing ${
          searchQuery ? 'opacity-30 pointer-events-none' : ''
        }`}
      />

      {/* Veg indicator */}
      <div
        className={`w-3.5 h-3.5 rounded-sm border-2 flex-shrink-0 ${
          item.is_veg
            ? 'border-emerald-500 bg-emerald-500/20'
            : 'border-red-500 bg-red-500/20'
        }`}
      />

      {/* Image thumbnail */}
      {item.image_url ? (
        <div className="w-8 h-8 rounded-lg overflow-hidden border border-white/10 flex-shrink-0">
          <img src={item.image_url} alt={item.name} className="w-full h-full object-cover" />
        </div>
      ) : (
        <div className="w-8 h-8 rounded-lg border border-white/[0.06] flex-shrink-0 flex items-center justify-center bg-white/[0.02]">
          <UtensilsCrossed className="w-3.5 h-3.5 text-zinc-700" />
        </div>
      )}

      {/* Name + description */}
      <div className="min-w-[9rem] flex-1">
        <div className="flex flex-wrap items-center gap-1.5">
          <p className="text-sm font-medium text-zinc-200 truncate">{highlight(item.name)}</p>
          {item.name_local && <span className="text-xs text-zinc-600">{item.name_local}</span>}
        </div>
        {item.description && (
          <p className="text-xs text-zinc-600 truncate mt-0.5">{item.description}</p>
        )}
      </div>

      {/* Metadata */}
      <div className="ml-auto flex w-full flex-wrap items-center justify-end gap-2 sm:w-auto sm:flex-shrink-0 sm:flex-nowrap">
        <SessionPill session={item.session} />

        {/* Clickable status badge cycles status */}
        <button
          onClick={() =>
            quickStatusCycle.mutate({ id: item.id, status: nextStatus[item.status] })
          }
          title="Click to cycle status"
          className="transition-opacity hover:opacity-80"
          disabled={quickStatusCycle.isPending}
        >
          <StatusBadge status={item.status} />
        </button>

        <span className="w-16 text-right text-sm font-semibold text-orange-400">
          ₹{item.price}
        </span>

        <div className="flex items-center gap-1 sm:opacity-0 sm:transition-opacity sm:group-hover:opacity-100">
          <button onClick={onEdit} className="btn-ghost p-1.5" title="Edit item">
            <Pencil className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={onDelete}
            className="btn-ghost p-1.5 hover:text-red-400"
            title="Delete item"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  )
}

// ─── Sub Group Section ─────────────────────────────────────────────────────────
function SubGroupSection({
  subGroup,
  onEditSubGroup,
  onDeleteSubGroup,
  searchQuery,
  onItemCountChange,
  pendingReorders,
  setPendingReorders,
  dragHandleProps,
}: {
  subGroup: MenuSubGroup
  onEditSubGroup: () => void
  onDeleteSubGroup: () => void
  searchQuery: string
  onItemCountChange?: (count: number) => void
  pendingReorders: any
  setPendingReorders: React.Dispatch<React.SetStateAction<any>>
  dragHandleProps?: any
}) {
  const [expanded, setExpanded] = useState(true)
  const [addItem, setAddItem] = useState(false)
  const [editItem, setEditItem] = useState<MenuItem | null>(null)
  const [deleteItem, setDeleteItem] = useState<MenuItem | null>(null)
  const qc = useQueryClient()

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  )

  const { data: items = [] } = useQuery<MenuItem[]>({
    queryKey: ['menu-items', subGroup.id],
    queryFn: () => menuApi.listItems(subGroup.id).then((r) => r.data),
  })

  useEffect(() => {
    onItemCountChange?.(items.length)
  }, [items.length, onItemCountChange])

  const deleteMutation = useMutation({
    mutationFn: (id: number) => menuApi.deleteItem(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['menu-items', subGroup.id] })
      toast.success('Item deleted')
      setDeleteItem(null)
    },
    onError: () => toast.error('Failed to delete item'),
  })

  const toggleActiveMutation = useMutation({
    mutationFn: () => menuApi.updateSubGroup(subGroup.id, { is_active: !subGroup.is_active }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['menu-subgroups'] })
      toast.success(subGroup.is_active ? 'Sub-category hidden' : 'Sub-category shown')
    },
  })

  // Filter items by search
  const filteredItems = useMemo(() => {
    if (!searchQuery) return items
    return items.filter(
      (i) =>
        i.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (i.name_local?.toLowerCase().includes(searchQuery.toLowerCase()) ?? false) ||
        (i.description?.toLowerCase().includes(searchQuery.toLowerCase()) ?? false)
    )
  }, [items, searchQuery])

  // Respect local drag reordering
  const orderedItems = useMemo(() => {
    const pending = pendingReorders.items?.[subGroup.id]
    if (pending) {
      return [...items].sort((a, b) => pending.indexOf(a.id) - pending.indexOf(b.id))
    }
    return filteredItems
  }, [items, filteredItems, pendingReorders.items, subGroup.id])

  function handleDragEndItems(event: DragEndEvent) {
    const { active, over } = event
    if (!over || active.id === over.id) return
    if (searchQuery) return

    const oldIndex = orderedItems.findIndex((i) => i.id === active.id)
    const newIndex = orderedItems.findIndex((i) => i.id === over.id)

    const newOrder = arrayMove(orderedItems, oldIndex, newIndex).map((i) => i.id)

    setPendingReorders((prev: any) => ({
      ...prev,
      items: {
        ...prev.items,
        [subGroup.id]: newOrder,
      },
    }))
  }

  // Hide section entirely if searching and no matches
  if (searchQuery && filteredItems.length === 0) return null

  const availableCount = items.filter((i) => i.status === 'available').length
  const specialCount = items.filter((i) => i.status === 'today_special').length

  return (
    <div className="border-l border-white/[0.06] pl-3 sm:ml-4 sm:pl-4">
      {/* Sub-group header */}
      <div
        className={`flex flex-wrap items-center gap-2 py-2 group/sg rounded-lg hover:bg-white/[0.02] px-1 transition-all ${
          !subGroup.is_active ? 'opacity-50' : ''
        }`}
      >
        <GripVertical
          {...dragHandleProps}
          className={`hidden w-3.5 h-3.5 cursor-grab text-zinc-700 hover:text-zinc-400 sm:block active:cursor-grabbing ${
            searchQuery ? 'opacity-30 pointer-events-none' : ''
          }`}
        />
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex min-w-[12rem] flex-1 flex-wrap items-center gap-2 text-left"
        >
          {expanded ? (
            <ChevronDown className="w-4 h-4 text-zinc-500" />
          ) : (
            <ChevronRight className="w-4 h-4 text-zinc-500" />
          )}
          <Tag className="w-3.5 h-3.5 text-zinc-600 flex-shrink-0" />
          <span className="text-sm font-medium text-zinc-300">{subGroup.name}</span>
          {subGroup.name_local && (
            <span className="text-xs text-zinc-600">{subGroup.name_local}</span>
          )}
          <span className="text-xs text-zinc-600 ml-1">({items.length})</span>
          {!subGroup.is_active && (
            <span className="text-xs px-1.5 py-0.5 rounded-full bg-zinc-700/40 text-zinc-500 border border-zinc-600/30">
              hidden
            </span>
          )}
          {specialCount > 0 && (
            <span className="text-xs px-1.5 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
              {specialCount} special
            </span>
          )}
          {availableCount > 0 && (
            <span className="text-xs px-1.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              {availableCount} live
            </span>
          )}
        </button>
        <div className="ml-auto flex items-center gap-1 sm:opacity-0 sm:transition-opacity sm:group-hover/sg:opacity-100">
          <button
            onClick={() => setAddItem(true)}
            className="btn-ghost p-1.5 text-orange-400 hover:text-orange-300"
            title="Add item"
          >
            <Plus className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => toggleActiveMutation.mutate()}
            className={`btn-ghost p-1.5 ${subGroup.is_active ? 'text-emerald-400' : 'text-zinc-500'}`}
            title={subGroup.is_active ? 'Hide sub-category' : 'Show sub-category'}
          >
            {subGroup.is_active ? (
              <Eye className="w-3.5 h-3.5" />
            ) : (
              <EyeOff className="w-3.5 h-3.5" />
            )}
          </button>
          <button onClick={onEditSubGroup} className="btn-ghost p-1.5" title="Edit sub-category">
            <Pencil className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={onDeleteSubGroup}
            className="btn-ghost p-1.5 hover:text-red-400"
            title="Delete sub-category"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Items */}
      {expanded && (
        <div className="space-y-1.5 pb-2">
          <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEndItems}>
            <SortableContext items={orderedItems.map((i) => i.id)} strategy={verticalListSortingStrategy}>
              {orderedItems.map((item) => (
                <SortableItem key={item.id} id={item.id}>
                  {({ ref, style, dragHandleProps: itemDragHandleProps }) => (
                    <div ref={ref} style={style}>
                      <ItemRow
                        item={item}
                        subGroupId={subGroup.id}
                        searchQuery={searchQuery}
                        onEdit={() => setEditItem(item)}
                        onDelete={() => setDeleteItem(item)}
                        dragHandleProps={itemDragHandleProps}
                      />
                    </div>
                  )}
                </SortableItem>
              ))}
            </SortableContext>
          </DndContext>
          {!searchQuery && (
            <button
              onClick={() => setAddItem(true)}
              className="flex w-full items-center justify-center gap-2 rounded-xl border border-dashed border-white/10 px-4 py-2 text-sm text-zinc-600 transition-all hover:border-orange-500/30 hover:text-zinc-400"
            >
              <Plus className="w-4 h-4" /> Add item to {subGroup.name}
            </button>
          )}
        </div>
      )}

      {addItem && (
        <ItemFormModal
          open={addItem}
          onClose={() => setAddItem(false)}
          subGroupId={subGroup.id}
        />
      )}
      {editItem && (
        <ItemFormModal
          open={!!editItem}
          onClose={() => setEditItem(null)}
          subGroupId={subGroup.id}
          item={editItem}
        />
      )}
      <ConfirmDialog
        open={!!deleteItem}
        onClose={() => setDeleteItem(null)}
        onConfirm={() => deleteItem && deleteMutation.mutate(deleteItem.id)}
        title="Delete Item"
        description={`Are you sure you want to delete "${deleteItem?.name}"?`}
        loading={deleteMutation.isPending}
      />
    </div>
  )
}

// ─── Group Section ────────────────────────────────────────────────────────────
function GroupSection({
  group,
  restaurantId,
  searchQuery,
  pendingReorders,
  setPendingReorders,
  dragHandleProps,
}: {
  group: MenuGroup
  restaurantId: number
  searchQuery: string
  pendingReorders: any
  setPendingReorders: React.Dispatch<React.SetStateAction<any>>
  dragHandleProps?: any
}) {
  const [expanded, setExpanded] = useState(true)
  const [editGroup, setEditGroup] = useState(false)
  const [deleteGroup, setDeleteGroup] = useState(false)
  const [addSubGroup, setAddSubGroup] = useState(false)
  const [editSubGroup, setEditSubGroup] = useState<MenuSubGroup | null>(null)
  const [deleteSubGroup, setDeleteSubGroup] = useState<MenuSubGroup | null>(null)
  const qc = useQueryClient()

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  )

  const { data: subGroups = [] } = useQuery({
    queryKey: ['menu-subgroups', group.id],
    queryFn: () => menuApi.listSubGroups(group.id).then((r) => r.data),
    enabled: expanded,
  })

  const deleteGroupMutation = useMutation({
    mutationFn: () => menuApi.deleteGroup(group.id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['menu-groups'] })
      toast.success('Category deleted')
      setDeleteGroup(false)
    },
    onError: () => toast.error('Failed to delete category'),
  })

  const deleteSubGroupMutation = useMutation({
    mutationFn: (id: number) => menuApi.deleteSubGroup(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['menu-subgroups', group.id] })
      toast.success('Sub-category deleted')
      setDeleteSubGroup(null)
    },
    onError: () => toast.error('Failed to delete sub-category'),
  })

  const toggleActive = useMutation({
    mutationFn: () => menuApi.updateGroup(group.id, { is_active: !group.is_active }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['menu-groups'] })
      toast.success(group.is_active ? 'Category hidden' : 'Category shown')
    },
  })

  // Respect local drag reordering
  const orderedSubGroups = useMemo(() => {
    const pending = pendingReorders.subgroups?.[group.id]
    if (pending) {
      return [...subGroups].sort((a, b) => pending.indexOf(a.id) - pending.indexOf(b.id))
    }
    return subGroups
  }, [subGroups, pendingReorders.subgroups, group.id])

  function handleDragEndSubGroups(event: DragEndEvent) {
    const { active, over } = event
    if (!over || active.id === over.id) return
    if (searchQuery) return

    const oldIndex = orderedSubGroups.findIndex((sg) => sg.id === active.id)
    const newIndex = orderedSubGroups.findIndex((sg) => sg.id === over.id)

    const newOrder = arrayMove(orderedSubGroups, oldIndex, newIndex).map((sg) => sg.id)

    setPendingReorders((prev: any) => ({
      ...prev,
      subgroups: {
        ...prev.subgroups,
        [group.id]: newOrder,
      },
    }))
  }

  // Filter groups by name when searching
  const nameMatch =
    !searchQuery || group.name.toLowerCase().includes(searchQuery.toLowerCase())

  // If searching and group name doesn't match, still show if sub-sections have matches
  // (SubGroupSection handles filtering internally)

  return (
    <div className={`card p-0 overflow-hidden transition-all ${!group.is_active ? 'opacity-60' : ''}`}>
      {/* Category banner */}
      {group.image_url && (
        <div className="relative h-20 overflow-hidden">
          <img
            src={group.image_url}
            alt={group.name}
            className="w-full h-full object-cover opacity-60"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-[#141414] via-[#141414]/60 to-transparent" />
        </div>
      )}

      {/* Group header */}
      <div
        className={`flex flex-wrap items-center gap-3 border-b border-white/[0.06] p-3 sm:p-4 ${
          group.image_url ? '-mt-10 relative z-10' : ''
        }`}
      >
        <GripVertical
          {...dragHandleProps}
          className={`hidden w-4 h-4 cursor-grab text-zinc-600 hover:text-zinc-400 sm:block active:cursor-grabbing ${
            searchQuery ? 'opacity-30 pointer-events-none' : ''
          }`}
        />
        <div
          className={`w-1 h-8 rounded-full flex-shrink-0 ${group.is_active ? 'bg-orange-500' : 'bg-zinc-700'}`}
        />
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex min-w-[12rem] flex-1 flex-wrap items-center gap-2 text-left"
        >
          {expanded ? (
            <ChevronDown className="w-4 h-4 text-zinc-400" />
          ) : (
            <ChevronRight className="w-4 h-4 text-zinc-400" />
          )}
          <span className="font-semibold text-zinc-100">{group.name}</span>
          {group.name_local && <span className="text-sm text-zinc-500">{group.name_local}</span>}
          {group.instruction && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
              {group.instruction}
            </span>
          )}
          {!group.is_active && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-zinc-700/40 text-zinc-500 border border-zinc-600/30">
              Hidden
            </span>
          )}
          <span className="text-xs text-zinc-600 ml-1">
            {subGroups.length} sub-{subGroups.length === 1 ? 'category' : 'categories'}
          </span>
        </button>
        <div className="ml-auto flex items-center gap-1">
          <button
            onClick={() => toggleActive.mutate()}
            className={`btn-ghost p-1.5 ${group.is_active ? 'text-emerald-400' : 'text-zinc-600'}`}
            title={group.is_active ? 'Hide category' : 'Show category'}
          >
            {group.is_active ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
          </button>
          <button
            onClick={() => setAddSubGroup(true)}
            className="btn-ghost p-1.5 text-orange-400"
            title="Add sub-category"
          >
            <Plus className="w-4 h-4" />
          </button>
          <button onClick={() => setEditGroup(true)} className="btn-ghost p-1.5" title="Edit">
            <Pencil className="w-4 h-4" />
          </button>
          <button
            onClick={() => setDeleteGroup(true)}
            className="btn-ghost p-1.5 hover:text-red-400"
            title="Delete"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Sub-groups */}
      {expanded && (
        <div className="space-y-1 p-2 sm:p-3">
          {subGroups.length === 0 ? (
            <p className="text-xs text-zinc-600 px-4 py-3 text-center">
              No sub-categories yet. Add one to start adding items.
            </p>
          ) : (
            <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEndSubGroups}>
              <SortableContext items={orderedSubGroups.map((sg) => sg.id)} strategy={verticalListSortingStrategy}>
                {orderedSubGroups.map((sg) => (
                  <SortableItem key={sg.id} id={sg.id}>
                    {({ ref, style, dragHandleProps: sgDragHandleProps }) => (
                      <div ref={ref} style={style}>
                        <SubGroupSection
                          subGroup={sg}
                          searchQuery={searchQuery}
                          onEditSubGroup={() => setEditSubGroup(sg)}
                          onDeleteSubGroup={() => setDeleteSubGroup(sg)}
                          pendingReorders={pendingReorders}
                          setPendingReorders={setPendingReorders}
                          dragHandleProps={sgDragHandleProps}
                        />
                      </div>
                    )}
                  </SortableItem>
                ))}
              </SortableContext>
            </DndContext>
          )}
          {!searchQuery && (
            <button
              onClick={() => setAddSubGroup(true)}
              className="mt-2 flex w-full items-center justify-center gap-2 rounded-xl border border-dashed border-white/10 px-4 py-2.5 text-sm text-zinc-600 transition-all hover:border-orange-500/30 hover:text-zinc-400"
            >
              <Plus className="w-4 h-4" /> Add sub-category to {group.name}
            </button>
          )}
        </div>
      )}

      {/* Modals */}
      {editGroup && (
        <GroupFormModal
          open={editGroup}
          onClose={() => setEditGroup(false)}
          restaurantId={restaurantId}
          group={group}
        />
      )}
      {addSubGroup && (
        <SubGroupFormModal
          open={addSubGroup}
          onClose={() => setAddSubGroup(false)}
          groupId={group.id}
        />
      )}
      {editSubGroup && (
        <SubGroupFormModal
          open={!!editSubGroup}
          onClose={() => setEditSubGroup(null)}
          groupId={group.id}
          subGroup={editSubGroup}
        />
      )}
      <ConfirmDialog
        open={deleteGroup}
        onClose={() => setDeleteGroup(false)}
        onConfirm={() => deleteGroupMutation.mutate()}
        title="Delete Category"
        description={`This will delete "${group.name}" and all its sub-categories and items. This cannot be undone.`}
        loading={deleteGroupMutation.isPending}
      />
      <ConfirmDialog
        open={!!deleteSubGroup}
        onClose={() => setDeleteSubGroup(null)}
        onConfirm={() => deleteSubGroup && deleteSubGroupMutation.mutate(deleteSubGroup.id)}
        title="Delete Sub-Category"
        description={`Delete "${deleteSubGroup?.name}" and all items inside it?`}
        loading={deleteSubGroupMutation.isPending}
      />
    </div>
  )
}

// ─── Full Menu Preview ────────────────────────────────────────────────────────
function FullMenuPreview({
  restaurantId,
  onClose,
}: {
  restaurantId: number
  onClose: () => void
}) {
  const { data, isLoading } = useQuery({
    queryKey: ['full-menu', restaurantId],
    queryFn: () => menuApi.fullMenu(restaurantId).then((r) => r.data),
  })

  const totalItems = useMemo(() => {
    if (!data) return 0
    return (data as { groups: (MenuGroup & { sub_groups?: (MenuSubGroup & { items?: MenuItem[] })[] })[] }).groups?.reduce(
      (acc, g) => acc + (g.sub_groups?.reduce((a, sg) => a + (sg.items?.length ?? 0), 0) ?? 0),
      0
    ) ?? 0
  }, [data])

  return (
    <Modal open onClose={onClose} title="Full Menu Preview" size="lg">
      {isLoading ? (
        <div className="flex items-center justify-center py-16">
          <RefreshCw className="w-6 h-6 text-zinc-500 animate-spin" />
        </div>
      ) : !data ? (
        <div className="text-center py-8">
          <AlertCircle className="w-10 h-10 mx-auto mb-3 text-zinc-600" />
          <p className="text-zinc-500">No menu data available.</p>
        </div>
      ) : (
        <>
          {/* Summary bar */}
          <div className="mb-4 flex flex-wrap items-center gap-3 rounded-xl border border-white/[0.06] bg-white/[0.03] p-3">
            <span className="text-xs text-zinc-500">
              <span className="text-orange-400 font-semibold">
                {(data as { groups: MenuGroup[] }).groups?.length ?? 0}
              </span>{' '}
              categories
            </span>
            <span className="text-zinc-700">·</span>
            <span className="text-xs text-zinc-500">
              <span className="text-sky-400 font-semibold">{totalItems}</span> items total
            </span>
            {data.published_at && (
              <>
                <span className="text-zinc-700">·</span>
                <span className="text-xs text-zinc-600">
                  Last published: {new Date(data.published_at).toLocaleString()}
                </span>
              </>
            )}
          </div>

          <div className="space-y-6 max-h-[60vh] overflow-y-auto pr-1">
            {(data as { groups: (MenuGroup & { sub_groups?: (MenuSubGroup & { items?: MenuItem[] })[] })[] }).groups?.map((group) => (
              <div key={group.id}>
                <div className="mb-3 flex flex-wrap items-center gap-2">
                  <div className="w-1 h-5 rounded-full bg-orange-500" />
                  <h3 className="font-semibold text-zinc-100">{group.name}</h3>
                  {group.instruction && (
                    <span className="text-xs text-amber-400 border border-amber-500/20 px-2 py-0.5 rounded-full bg-amber-500/10">
                      {group.instruction}
                    </span>
                  )}
                  <span className="ml-auto text-xs text-zinc-600">
                    {group.sub_groups?.reduce((a, sg) => a + (sg.items?.length ?? 0), 0) ?? 0} items
                  </span>
                </div>
                {group.sub_groups?.map((sg) => (
                  <div key={sg.id} className="mb-4 sm:ml-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Tag className="w-3 h-3 text-zinc-600" />
                      <p className="text-sm text-zinc-400 font-medium">{sg.name}</p>
                      <span className="text-xs text-zinc-600">({sg.items?.length ?? 0})</span>
                    </div>
                    <div className="space-y-1.5">
                      {sg.items?.map((item) => (
                        <div
                          key={item.id}
                          className="flex flex-wrap items-center gap-3 rounded-xl border border-white/[0.04] bg-white/[0.02] px-3 py-2 sm:flex-nowrap"
                        >
                          <div
                            className={`w-3 h-3 rounded-sm border-2 flex-shrink-0 ${
                              item.is_veg
                                ? 'border-emerald-500 bg-emerald-500/20'
                                : 'border-red-500 bg-red-500/20'
                            }`}
                          />
                          {item.image_url && (
                            <img
                              src={item.image_url}
                              alt={item.name}
                              className="w-8 h-8 rounded-lg object-cover border border-white/10"
                            />
                          )}
                          <div className="min-w-[9rem] flex-1">
                            <p className="text-sm text-zinc-200">{item.name}</p>
                            {item.description && (
                              <p className="text-xs text-zinc-600 truncate">{item.description}</p>
                            )}
                          </div>
                          <SessionPill session={item.session} />
                          <StatusBadge status={item.status} />
                          <span className="text-sm font-semibold text-orange-400">
                            ₹{item.price}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </>
      )}
    </Modal>
  )
}

// ─── Stats Bar ────────────────────────────────────────────────────────────────
function StatsBar({
  groups,
  restaurantId,
}: {
  groups: MenuGroup[]
  restaurantId: number
}) {
  const allSubGroupsQuery = useQuery({
    queryKey: ['all-subgroups-count', restaurantId],
    queryFn: async () => {
      const results = await Promise.all(
        groups.map((g) => menuApi.listSubGroups(g.id).then((r) => r.data))
      )
      return results.flat()
    },
    enabled: groups.length > 0,
  })

  const allItemsQuery = useQuery({
    queryKey: ['all-items-count', restaurantId],
    queryFn: async () => {
      const subGroups = allSubGroupsQuery.data ?? []
      if (subGroups.length === 0) return []
      const results = await Promise.all(
        subGroups.map((sg) => menuApi.listItems(sg.id).then((r) => r.data))
      )
      return results.flat()
    },
    enabled: (allSubGroupsQuery.data?.length ?? 0) > 0,
  })

  const activeGroups = groups.filter((g) => g.is_active).length
  const totalItems = allItemsQuery.data?.length ?? null
  const availableItems = allItemsQuery.data?.filter((i) => i.status === 'available').length ?? null
  const specialItems = allItemsQuery.data?.filter((i) => i.status === 'today_special').length ?? null

  const stats = [
    {
      icon: <Layers className="w-4 h-4" />,
      label: 'Categories',
      value: groups.length,
      sub: `${activeGroups} active`,
      color: 'text-orange-400',
      bg: 'bg-orange-500/10',
    },
    {
      icon: <Tag className="w-4 h-4" />,
      label: 'Sub-Categories',
      value: allSubGroupsQuery.data?.length ?? '—',
      sub: 'across all groups',
      color: 'text-sky-400',
      bg: 'bg-sky-500/10',
    },
    {
      icon: <Package className="w-4 h-4" />,
      label: 'Total Items',
      value: totalItems !== null ? totalItems : '—',
      sub: availableItems !== null ? `${availableItems} available · ${specialItems} special` : 'on the menu',
      color: 'text-emerald-400',
      bg: 'bg-emerald-500/10',
    },
  ]

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
      {stats.map((stat) => (
        <div key={stat.label} className="card flex items-center gap-3 p-4">
          <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${stat.bg}`}>
            <span className={stat.color}>{stat.icon}</span>
          </div>
          <div className="min-w-0">
            <p className={`text-lg font-bold ${stat.color}`}>{stat.value}</p>
            <p className="text-xs text-zinc-500">{stat.label}</p>
            <p className="text-xs text-zinc-600 mt-0.5">{stat.sub}</p>
          </div>
        </div>
      ))}
    </div>
  )
}

// ─── Main Page ─────────────────────────────────────────────────────────────────
export default function MenuPage() {
  const { user } = useAuthStore()
  const isSuperAdmin = user?.role === 'super_admin'

  // Super admins pick a restaurant; others use their own
  const [selectedRestaurantId, setSelectedRestaurantId] = useState<number | null>(null)
  const restaurantId = isSuperAdmin ? selectedRestaurantId : (user?.restaurant_id ?? null)

  const [addGroup, setAddGroup] = useState(false)
  const [publishing, setPublishing] = useState(false)
  const [showPreview, setShowPreview] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const qc = useQueryClient()

  // Track unsaved drag reorders across all levels
  const [pendingReorders, setPendingReorders] = useState<{
    groups?: number[]
    subgroups?: Record<number, number[]>
    items?: Record<number, number[]>
  }>({})

  const hasChanges = useMemo(() => {
    return (
      !!pendingReorders.groups ||
      Object.keys(pendingReorders.subgroups || {}).length > 0 ||
      Object.keys(pendingReorders.items || {}).length > 0
    )
  }, [pendingReorders])

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  )

  const { data: groups = [], isLoading, refetch } = useQuery({
    queryKey: ['menu-groups', restaurantId],
    queryFn: () => menuApi.listGroups(restaurantId!).then((r) => r.data),
    enabled: !!restaurantId,
  })

  const handlePublish = async () => {
    if (!restaurantId) return
    setPublishing(true)
    try {
      const res = await menuApi.publish(restaurantId)
      toast.success(`✅ ${res.data.message}`, { duration: 4000 })
    } catch {
      toast.error('Publish failed — check backend connection')
    } finally {
      setPublishing(false)
    }
  }

  // Filter groups by search query (also show if any children match — handled in subgroups)
  const filteredGroups = useMemo(() => {
    if (!searchQuery) return groups
    return groups.filter((g) =>
      g.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (g.name_local?.toLowerCase().includes(searchQuery.toLowerCase()) ?? false) ||
      (g.instruction?.toLowerCase().includes(searchQuery.toLowerCase()) ?? false)
    )
  }, [groups, searchQuery])

  // Respect local drag reordering
  const orderedGroups = useMemo(() => {
    if (pendingReorders.groups) {
      return [...groups].sort((a, b) => pendingReorders.groups!.indexOf(a.id) - pendingReorders.groups!.indexOf(b.id))
    }
    return filteredGroups
  }, [groups, pendingReorders.groups, filteredGroups])

  function handleDragEndGroups(event: DragEndEvent) {
    const { active, over } = event
    if (!over || active.id === over.id) return
    if (searchQuery) return

    const oldIndex = orderedGroups.findIndex((g) => g.id === active.id)
    const newIndex = orderedGroups.findIndex((g) => g.id === over.id)

    const newOrder = arrayMove(orderedGroups, oldIndex, newIndex).map((g) => g.id)

    setPendingReorders((prev) => ({
      ...prev,
      groups: newOrder,
    }))
  }

  const [isSavingOrder, setIsSavingOrder] = useState(false)

  const handleSaveOrder = async () => {
    setIsSavingOrder(true)
    try {
      const promises: Promise<any>[] = []

      // 1. Save Category Order
      if (pendingReorders.groups) {
         promises.push(menuApi.reorderGroups(pendingReorders.groups))
      }

      // 2. Save Subcategory Orders
      if (pendingReorders.subgroups) {
        Object.values(pendingReorders.subgroups).forEach((subgroupIds) => {
          promises.push(menuApi.reorderSubGroups(subgroupIds))
        })
      }

      // 3. Save Item Orders
      if (pendingReorders.items) {
        Object.values(pendingReorders.items).forEach((itemIds) => {
          promises.push(menuApi.reorderItems(itemIds))
        })
      }

      await Promise.all(promises)
      toast.success('🎉 Menu structure updated successfully!')

      // Invalidate react-query cache keys to fetch fresh database order
      qc.invalidateQueries({ queryKey: ['menu-groups'] })
      qc.invalidateQueries({ queryKey: ['menu-subgroups'] })
      qc.invalidateQueries({ queryKey: ['menu-items'] })

      // Reset dirty state
      setPendingReorders({})
    } catch (error) {
       console.error(error)
       toast.error('Failed to save menu ordering. Please try again.')
    } finally {
       setIsSavingOrder(false)
    }
  }

  // No restaurant — super admin needs to pick one
  if (isSuperAdmin && !selectedRestaurantId) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="font-display text-2xl font-bold text-zinc-50 sm:text-3xl">Menu Manager</h1>
          <p className="text-zinc-500 text-sm mt-1">Select a restaurant to manage its menu</p>
        </div>
        <RestaurantSelector value={selectedRestaurantId} onChange={setSelectedRestaurantId} />
        <div className="card p-6 text-center sm:p-16">
          <Store className="w-16 h-16 mx-auto mb-4 text-zinc-700" />
          <h2 className="text-xl font-semibold text-zinc-400 mb-2">No restaurant selected</h2>
          <p className="text-zinc-600 text-sm">
            Pick a restaurant above to view and manage its menu.
          </p>
        </div>
      </div>
    )
  }

  if (!restaurantId) {
    return (
      <div className="flex items-center justify-center h-64 text-zinc-500">
        <div className="text-center">
          <UtensilsCrossed className="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p>No restaurant associated with your account.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold text-zinc-50 sm:text-3xl">Menu Manager</h1>
          <p className="text-zinc-500 text-sm mt-1">
            {groups.length} {groups.length === 1 ? 'category' : 'categories'} ·{' '}
            {groups.filter((g) => g.is_active).length} active
          </p>
        </div>
        <div className="grid w-full grid-cols-2 gap-2 sm:flex sm:w-auto sm:flex-wrap sm:items-center sm:justify-end">
          <button
            onClick={() => refetch()}
            className="btn-ghost p-2.5"
            title="Refresh menu data"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <button onClick={() => setShowPreview(true)} className="btn-secondary">
            <BookOpen className="w-4 h-4" /> Preview Menu
          </button>
          <button onClick={() => setAddGroup(true)} className="btn-secondary">
            <Plus className="w-4 h-4" /> Add Category
          </button>
          <button
            onClick={handlePublish}
            disabled={publishing}
            className="btn-primary"
            title="Push current menu to all connected TV screens"
          >
            {publishing ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" /> Publishing...
              </>
            ) : (
              <>
                <Tv className="w-4 h-4" /> Publish to TVs
              </>
            )}
          </button>
        </div>
      </div>

      {/* ── Super Admin Restaurant Selector ── */}
      {isSuperAdmin && (
        <RestaurantSelector value={selectedRestaurantId} onChange={setSelectedRestaurantId} />
      )}

      {/* ── Stats ── */}
      {!isLoading && groups.length > 0 && (
        <StatsBar groups={groups} restaurantId={restaurantId} />
      )}

      {/* ── Search bar ── */}
      {groups.length > 0 && (
        <div className="relative">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500 pointer-events-none" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search items, categories, sub-categories..."
            className="input pl-10 pr-10"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      )}

      {/* ── Quick Actions Banner ── */}
      {!isLoading && groups.length > 0 && !searchQuery && (
        <div className="flex items-center gap-3 p-3 rounded-xl bg-orange-500/5 border border-orange-500/10">
          <Zap className="w-4 h-4 text-orange-400 flex-shrink-0" />
          <p className="text-xs text-zinc-400">
            <span className="text-orange-400 font-medium">Tip:</span> Click any status badge (Available / Special / Off) on an item to instantly cycle its status without opening the editor.
          </p>
        </div>
      )}

      {/* ── Groups list ── */}
      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="card h-20 animate-pulse opacity-40" />
          ))}
        </div>
      ) : groups.length === 0 ? (
        <div className="card p-6 text-center sm:p-16">
          <UtensilsCrossed className="w-16 h-16 mx-auto mb-4 text-zinc-700" />
          <h2 className="text-xl font-semibold text-zinc-400 mb-2">No menu categories yet</h2>
          <p className="text-zinc-600 text-sm mb-6">
            Start building your menu by adding categories like "South Indian", "Beverages" etc.
          </p>
          <button onClick={() => setAddGroup(true)} className="btn-primary mx-auto">
            <Plus className="w-4 h-4" /> Add First Category
          </button>
        </div>
      ) : filteredGroups.length === 0 ? (
        <div className="card p-6 text-center sm:p-12">
          <Search className="w-12 h-12 mx-auto mb-4 text-zinc-700" />
          <p className="text-zinc-400 font-medium mb-1">No results for "{searchQuery}"</p>
          <p className="text-zinc-600 text-sm">Try a different search term.</p>
          <button
            onClick={() => setSearchQuery('')}
            className="btn-secondary mt-4 mx-auto"
          >
            <X className="w-4 h-4" /> Clear Search
          </button>
        </div>
      ) : (
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEndGroups}>
          <SortableContext items={orderedGroups.map((g) => g.id)} strategy={verticalListSortingStrategy}>
            <div className="space-y-4">
              {orderedGroups.map((group) => (
                <SortableItem key={group.id} id={group.id}>
                  {({ ref, style, dragHandleProps: groupDragHandleProps }) => (
                    <div ref={ref} style={style}>
                      <GroupSection
                        group={group}
                        restaurantId={restaurantId}
                        searchQuery={searchQuery}
                        pendingReorders={pendingReorders}
                        setPendingReorders={setPendingReorders}
                        dragHandleProps={groupDragHandleProps}
                      />
                    </div>
                  )}
                </SortableItem>
              ))}
            </div>
          </SortableContext>
        </DndContext>
      )}

      {/* ── Modals ── */}
      {addGroup && (
        <GroupFormModal
          open={addGroup}
          onClose={() => setAddGroup(false)}
          restaurantId={restaurantId}
        />
      )}
      {showPreview && (
        <FullMenuPreview restaurantId={restaurantId} onClose={() => setShowPreview(false)} />
      )}

      {/* Floating Save Banner */}
      {hasChanges && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 w-[90%] max-w-lg bg-zinc-950/95 backdrop-blur-md border border-white/10 px-6 py-4 rounded-2xl shadow-2xl flex items-center justify-between animate-in slide-in-from-bottom-4 duration-300">
          <div className="flex items-center gap-3">
            <div className="w-2.5 h-2.5 rounded-full bg-amber-500 animate-pulse" />
            <div>
              <p className="text-sm font-semibold text-zinc-100">Unsaved Order Changes</p>
              <p className="text-xs text-zinc-400">Rearrange categories, subcategories, or items.</p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPendingReorders({})}
              disabled={isSavingOrder}
              className="px-3.5 py-1.5 rounded-xl text-xs font-semibold text-zinc-400 hover:text-zinc-200 transition-colors"
            >
              Discard
            </button>
            
            <button
              onClick={handleSaveOrder}
              disabled={isSavingOrder}
              className="flex items-center gap-1.5 bg-orange-500 hover:bg-orange-600 disabled:bg-orange-600/50 text-white px-4 py-2 rounded-xl text-xs font-bold transition-all shadow-md active:scale-95"
            >
              {isSavingOrder ? (
                <>
                  <RefreshCw className="w-3 h-3 animate-spin" /> Saving...
                </>
              ) : (
                'Save Changes'
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
