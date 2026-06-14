import { useState, useRef, useCallback, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  menuApi, templatesApi,
  type MenuGroup, type MenuItem, type MenuTemplate, type TemplateItemIn
} from '@/api/services'
import { useAuthStore } from '@/store/authStore'
import toast from 'react-hot-toast'
import {
  LayoutTemplate, GripVertical, X, Clock, CheckCircle2,
  Trash2, Zap, ChevronDown, ChevronRight, Search, Plus,
  Save, Columns2, AlignJustify, Leaf, Beef, Store
} from 'lucide-react'
import clsx from 'clsx'
import RestaurantSelector from '@/components/ui/RestaurantSelector'

// ─── Types ────────────────────────────────────────────────────────────────────

interface SlotItem {
  slotId: string
  item: MenuItem
  durationSeconds: number
}

type LayoutType = 'single' | 'two_column'

// ─── Sub-components ───────────────────────────────────────────────────────────

function MenuItemCard({ item, onDragStart }: { item: MenuItem; onDragStart: (e: React.DragEvent, item: MenuItem) => void }) {
  return (
    <div
      draggable
      onDragStart={(e) => onDragStart(e, item)}
      id={`menu-item-${item.id}`}
      className="group flex items-center gap-2.5 rounded-xl border border-white/[0.06] bg-white/[0.03] px-3 py-2.5 cursor-grab active:cursor-grabbing hover:border-violet-500/40 hover:bg-violet-500/5 transition-all duration-200 select-none"
    >
      <GripVertical className="w-3.5 h-3.5 text-zinc-600 group-hover:text-violet-400 flex-shrink-0 transition-colors" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-zinc-200 truncate">{item.name}</p>
        {item.name_local && (
          <p className="text-[11px] text-zinc-500 truncate">{item.name_local}</p>
        )}
      </div>
      <div className="flex items-center gap-1.5 flex-shrink-0">
        {item.is_veg
          ? <Leaf className="w-3 h-3 text-green-400" />
          : <Beef className="w-3 h-3 text-red-400" />}
        <span className="text-xs font-semibold text-violet-400">₹{item.price}</span>
      </div>
    </div>
  )
}

function TemplateSlot({
  slot, index, totalSlots, layout,
  onRemove, onDurationChange,
  onDragOver, onDrop,
  onSlotDragStart,
}: {
  slot: SlotItem
  index: number
  totalSlots: number
  layout: LayoutType
  onRemove: (slotId: string) => void
  onDurationChange: (slotId: string, v: number) => void
  onDragOver: (e: React.DragEvent) => void
  onDrop: (e: React.DragEvent, slotId: string) => void
  onSlotDragStart: (e: React.DragEvent, slotId: string) => void
}) {
  return (
    <div
      draggable
      onDragStart={(e) => onSlotDragStart(e, slot.slotId)}
      onDragOver={onDragOver}
      onDrop={(e) => onDrop(e, slot.slotId)}
      id={`slot-${slot.slotId}`}
      className={clsx(
        'group relative rounded-xl border transition-all duration-200 bg-white/[0.04] hover:bg-white/[0.06]',
        'border-white/[0.08] hover:border-violet-500/30',
        layout === 'two_column' ? 'p-3' : 'p-3.5'
      )}
    >
      <div className="flex items-start gap-2">
        <div className="flex-shrink-0 mt-0.5">
          <GripVertical className="w-3.5 h-3.5 text-zinc-600 group-hover:text-violet-400 cursor-grab transition-colors" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 mb-1">
            {slot.item.is_veg
              ? <Leaf className="w-3 h-3 text-green-400 flex-shrink-0" />
              : <Beef className="w-3 h-3 text-red-400 flex-shrink-0" />}
            <p className="text-sm font-semibold text-zinc-100 truncate">{slot.item.name}</p>
          </div>
          {slot.item.name_local && (
            <p className="text-[11px] text-zinc-500 truncate mb-1.5">{slot.item.name_local}</p>
          )}
          <div className="flex items-center gap-2">
            <Clock className="w-3 h-3 text-zinc-500 flex-shrink-0" />
            <input
              type="number"
              min={3}
              max={300}
              value={slot.durationSeconds}
              onChange={(e) => onDurationChange(slot.slotId, parseInt(e.target.value) || 10)}
              className="w-16 rounded-lg border border-white/[0.1] bg-white/[0.06] px-2 py-0.5 text-xs text-zinc-200 focus:border-violet-500/60 focus:outline-none focus:ring-1 focus:ring-violet-500/30 transition-all"
            />
            <span className="text-[11px] text-zinc-500">sec</span>
            <span className="ml-auto text-xs font-semibold text-violet-400">₹{slot.item.price}</span>
          </div>
        </div>
        <button
          onClick={() => onRemove(slot.slotId)}
          className="flex-shrink-0 rounded-lg p-1 text-zinc-600 hover:bg-red-500/10 hover:text-red-400 transition-all"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  )
}

function EmptyDropZone({ layout, onDragOver, onDrop }: {
  layout: LayoutType
  onDragOver: (e: React.DragEvent) => void
  onDrop: (e: React.DragEvent, slotId: string) => void
}) {
  const [over, setOver] = useState(false)
  return (
    <div
      onDragOver={(e) => { setOver(true); onDragOver(e) }}
      onDragLeave={() => setOver(false)}
      onDrop={(e) => { setOver(false); onDrop(e, '__empty__') }}
      className={clsx(
        'flex flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed transition-all duration-300',
        layout === 'two_column' ? 'min-h-[180px]' : 'min-h-[220px]',
        over
          ? 'border-violet-500/60 bg-violet-500/10 scale-[1.01]'
          : 'border-white/[0.1] bg-white/[0.02]'
      )}
    >
      <div className={clsx(
        'flex h-12 w-12 items-center justify-center rounded-2xl transition-all',
        over ? 'bg-violet-500/20' : 'bg-white/[0.05]'
      )}>
        <Plus className={clsx('w-5 h-5 transition-colors', over ? 'text-violet-400' : 'text-zinc-600')} />
      </div>
      <p className={clsx('text-sm font-medium transition-colors', over ? 'text-violet-300' : 'text-zinc-500')}>
        {over ? 'Release to drop' : 'Drag menu items here'}
      </p>
    </div>
  )
}

// ─── Saved Template Card ──────────────────────────────────────────────────────

function SavedTemplateCard({ template, onActivate, onDelete, activating, deleting }: {
  template: MenuTemplate
  onActivate: () => void
  onDelete: () => void
  activating: boolean
  deleting: boolean
}) {
  return (
    <div className={clsx(
      'rounded-2xl border p-4 transition-all duration-200',
      template.is_active
        ? 'border-violet-500/50 bg-violet-500/[0.07]'
        : 'border-white/[0.06] bg-white/[0.02] hover:border-white/[0.12]'
    )}>
      <div className="flex items-start gap-3">
        <div className={clsx(
          'flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl',
          template.is_active ? 'bg-violet-500/20' : 'bg-white/[0.05]'
        )}>
          <LayoutTemplate className={clsx('w-4.5 h-4.5', template.is_active ? 'text-violet-400' : 'text-zinc-500')} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <p className="font-semibold text-zinc-100 truncate">{template.name}</p>
            {template.is_active && (
              <span className="flex items-center gap-1 rounded-full bg-violet-500/20 px-2 py-0.5 text-[10px] font-semibold text-violet-300">
                <CheckCircle2 className="w-2.5 h-2.5" /> Active
              </span>
            )}
          </div>
          <p className="text-xs text-zinc-500 mt-0.5">
            {template.items.length} item{template.items.length !== 1 ? 's' : ''}
          </p>

          {/* Item preview chips */}
          {template.items.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {template.items.slice(0, 5).map((ti) => (
                <span key={ti.id} className="rounded-lg bg-white/[0.05] px-2 py-0.5 text-[11px] text-zinc-400 border border-white/[0.06]">
                  {ti.menu_item.name}
                  <span className="text-zinc-600 ml-1">{ti.duration_second}s</span>
                </span>
              ))}
              {template.items.length > 5 && (
                <span className="rounded-lg bg-white/[0.05] px-2 py-0.5 text-[11px] text-zinc-500">
                  +{template.items.length - 5} more
                </span>
              )}
            </div>
          )}
        </div>

        <div className="flex gap-2 flex-shrink-0">
          {!template.is_active && (
            <button
              id={`activate-template-${template.id}`}
              onClick={onActivate}
              disabled={activating}
              className="flex items-center gap-1.5 rounded-xl border border-violet-500/40 bg-violet-500/10 px-3 py-1.5 text-xs font-semibold text-violet-300 hover:bg-violet-500/20 transition-all disabled:opacity-50"
            >
              <Zap className="w-3 h-3" />
              {activating ? 'Activating…' : 'Activate'}
            </button>
          )}
          <button
            id={`delete-template-${template.id}`}
            onClick={onDelete}
            disabled={deleting}
            className="flex items-center gap-1.5 rounded-xl border border-red-500/30 bg-red-500/5 px-2.5 py-1.5 text-xs font-semibold text-red-400 hover:bg-red-500/15 transition-all disabled:opacity-50"
          >
            <Trash2 className="w-3 h-3" />
          </button>
        </div>
      </div>
    </div>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function TemplatesPage() {
  const { user } = useAuthStore()
  const isSuperAdmin = user?.role === 'super_admin'
  const queryClient = useQueryClient()
  
  const [selectedRestaurantId, setSelectedRestaurantId] = useState<number | null>(null)
  const restaurantId = isSuperAdmin ? selectedRestaurantId : (user?.restaurant_id ?? null)

  // ── State ─────────────────────────────────────────────────────────────────
  const [layout, setLayout] = useState<LayoutType>('single')
  const [templateName, setTemplateName] = useState('')
  const [slots, setSlots] = useState<SlotItem[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [expandedGroups, setExpandedGroups] = useState<Set<number>>(new Set())
  const [expandedSubGroups, setExpandedSubGroups] = useState<Set<number>>(new Set())
  const [draggingMenuItemRef] = useState<{ current: MenuItem | null }>({ current: null })
  const [draggingSlotId, setDraggingSlotId] = useState<string | null>(null)
  const [dropOverSlotId, setDropOverSlotId] = useState<string | null>(null)

  const activatingRef = useRef<Record<number, boolean>>({})
  const deletingRef = useRef<Record<number, boolean>>({})

  // ── Queries ───────────────────────────────────────────────────────────────
  const { data: fullMenu, isLoading: menuLoading } = useQuery({
    queryKey: ['full-menu', restaurantId],
    queryFn: () => menuApi.fullMenu(restaurantId).then(r => r.data),
    enabled: !!restaurantId,
  })

  const { data: templates = [], isLoading: templatesLoading } = useQuery({
    queryKey: ['templates', restaurantId],
    queryFn: () => templatesApi.list(restaurantId).then(r => r.data),
    enabled: !!restaurantId,
  })

  // ── Mutations ─────────────────────────────────────────────────────────────
  const saveMutation = useMutation({
    mutationFn: (data: { name: string; items: TemplateItemIn[] }) =>
      templatesApi.create(restaurantId, { name: data.name, items: data.items }),
    onSuccess: () => {
      toast.success('Template saved!')
      queryClient.invalidateQueries({ queryKey: ['templates', restaurantId] })
      setSlots([])
      setTemplateName('')
    },
    onError: () => toast.error('Failed to save template'),
  })

  const activateMutation = useMutation({
    mutationFn: (id: number) => templatesApi.activate(id),
    onSuccess: () => {
      toast.success('Template activated!')
      queryClient.invalidateQueries({ queryKey: ['templates', restaurantId] })
    },
    onError: () => toast.error('Failed to activate template'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => templatesApi.delete(id),
    onSuccess: () => {
      toast.success('Template deleted')
      queryClient.invalidateQueries({ queryKey: ['templates', restaurantId] })
    },
    onError: () => toast.error('Failed to delete template'),
  })

  // ── Menu item drag ────────────────────────────────────────────────────────
  const handleMenuItemDragStart = useCallback((e: React.DragEvent, item: MenuItem) => {
    draggingMenuItemRef.current = item
    e.dataTransfer.effectAllowed = 'copy'
    e.dataTransfer.setData('text/plain', String(item.id))
  }, [])

  // ── Slot drag (reorder) ───────────────────────────────────────────────────
  const handleSlotDragStart = useCallback((e: React.DragEvent, slotId: string) => {
    setDraggingSlotId(slotId)
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('slot-id', slotId)
  }, [])

  // ── Drop onto slot zone ───────────────────────────────────────────────────
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = e.dataTransfer.types.includes('slot-id') ? 'move' : 'copy'
  }, [])

  const handleDrop = useCallback((e: React.DragEvent, targetSlotId: string) => {
    e.preventDefault()
    setDropOverSlotId(null)

    const slotIdData = e.dataTransfer.getData('slot-id')

    if (slotIdData && draggingSlotId) {
      // Reordering existing slot
      if (slotIdData === targetSlotId) return
      setSlots(prev => {
        const next = [...prev]
        const fromIdx = next.findIndex(s => s.slotId === slotIdData)
        const toIdx = targetSlotId === '__empty__' ? next.length : next.findIndex(s => s.slotId === targetSlotId)
        if (fromIdx === -1) return prev
        const [moved] = next.splice(fromIdx, 1)
        const insertAt = toIdx === -1 ? next.length : (fromIdx < toIdx ? toIdx - 1 : toIdx)
        next.splice(insertAt, 0, moved)
        return next
      })
      setDraggingSlotId(null)
      return
    }

    const item = draggingMenuItemRef.current
    if (!item) return
    draggingMenuItemRef.current = null

    const newSlot: SlotItem = {
      slotId: `${item.id}-${Date.now()}`,
      item,
      durationSeconds: 10,
    }

    if (targetSlotId === '__empty__') {
      setSlots(prev => [...prev, newSlot])
    } else {
      setSlots(prev => {
        const idx = prev.findIndex(s => s.slotId === targetSlotId)
        if (idx === -1) return [...prev, newSlot]
        const next = [...prev]
        next.splice(idx, 0, newSlot)
        return next
      })
    }
  }, [draggingSlotId])

  const handleRemoveSlot = useCallback((slotId: string) => {
    setSlots(prev => prev.filter(s => s.slotId !== slotId))
  }, [])

  const handleDurationChange = useCallback((slotId: string, v: number) => {
    setSlots(prev => prev.map(s => s.slotId === slotId ? { ...s, durationSeconds: v } : s))
  }, [])

  const handleSave = () => {
    if (!templateName.trim()) { toast.error('Please enter a template name'); return }
    if (slots.length === 0) { toast.error('Add at least one menu item'); return }
    saveMutation.mutate({
      name: templateName.trim(),
      items: slots.map(s => ({ item_id: s.item.id, duration_seconds: s.durationSeconds })),
    })
  }

  // ── Filtered menu items ───────────────────────────────────────────────────
  const allItems: MenuItem[] = []
  fullMenu?.groups?.forEach((g: MenuGroup) =>
    g.sub_groups?.forEach(sg => sg.items?.forEach(item => allItems.push(item)))
  )
  const filtered = searchQuery.trim()
    ? allItems.filter(i =>
      i.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (i.name_local ?? '').toLowerCase().includes(searchQuery.toLowerCase())
    )
    : null

  const toggleGroup = (id: number) =>
    setExpandedGroups(prev => { const n = new Set(prev); n.has(id) ? n.delete(id) : n.add(id); return n })
  const toggleSubGroup = (id: number) =>
    setExpandedSubGroups(prev => { const n = new Set(prev); n.has(id) ? n.delete(id) : n.add(id); return n })

  // ── Guard ─────────────────────────────────────────────────────────────────
  if (isSuperAdmin && !selectedRestaurantId) {
    return (
      <div className="space-y-6 max-w-[1400px] mx-auto p-6">
        <div>
          <h1 className="font-display text-2xl font-bold text-zinc-50 sm:text-3xl">Template Designer</h1>
          <p className="text-zinc-500 text-sm mt-1">Select a restaurant to manage its templates</p>
        </div>
        <RestaurantSelector value={selectedRestaurantId} onChange={setSelectedRestaurantId} />
        <div className="card p-6 text-center sm:p-16">
          <Store className="w-16 h-16 mx-auto mb-4 text-zinc-700" />
          <h2 className="text-xl font-semibold text-zinc-400 mb-2">No restaurant selected</h2>
          <p className="text-zinc-600 text-sm">
            Pick a restaurant above to create and manage display templates.
          </p>
        </div>
      </div>
    )
  }

  if (!restaurantId) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] gap-3">
        <LayoutTemplate className="w-10 h-10 text-zinc-600" />
        <p className="text-zinc-400 text-sm">No restaurant linked to your account.</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6 p-6 max-w-[1400px] mx-auto">
      {/* ── Header ──────────────────────────────────────────────────────── */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-violet-500/15 border border-violet-500/30">
            <LayoutTemplate className="w-5 h-5 text-violet-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-zinc-100">Template Designer</h1>
            <p className="text-xs text-zinc-500">Drag menu items to build display templates for your TV screens</p>
          </div>
        </div>
      </div>

      {isSuperAdmin && (
        <RestaurantSelector value={selectedRestaurantId} onChange={setSelectedRestaurantId} />
      )}

      {/* ── Designer ────────────────────────────────────────────────────── */}
      <div className="rounded-2xl border border-white/[0.06] bg-[#111]/60 backdrop-blur p-5 space-y-5">

        {/* Template name + layout picker */}
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs font-medium text-zinc-400 mb-1.5">Template Name</label>
            <input
              id="template-name-input"
              type="text"
              value={templateName}
              onChange={e => setTemplateName(e.target.value)}
              placeholder="e.g. Lunch Special, Weekend Menu…"
              className="w-full rounded-xl border border-white/[0.08] bg-white/[0.04] px-3.5 py-2 text-sm text-zinc-200 placeholder-zinc-600 focus:border-violet-500/60 focus:outline-none focus:ring-2 focus:ring-violet-500/20 transition-all"
            />
          </div>

          {/* Layout selector */}
          <div>
            <label className="block text-xs font-medium text-zinc-400 mb-1.5">Layout</label>
            <div className="flex gap-2">
              <button
                id="layout-single"
                onClick={() => setLayout('single')}
                className={clsx(
                  'flex items-center gap-2 rounded-xl border px-4 py-2 text-sm font-medium transition-all',
                  layout === 'single'
                    ? 'border-violet-500/60 bg-violet-500/15 text-violet-300'
                    : 'border-white/[0.08] bg-white/[0.03] text-zinc-400 hover:border-white/[0.15]'
                )}
              >
                <AlignJustify className="w-4 h-4" />
                Single Column
              </button>
              <button
                id="layout-two-column"
                onClick={() => setLayout('two_column')}
                className={clsx(
                  'flex items-center gap-2 rounded-xl border px-4 py-2 text-sm font-medium transition-all',
                  layout === 'two_column'
                    ? 'border-violet-500/60 bg-violet-500/15 text-violet-300'
                    : 'border-white/[0.08] bg-white/[0.03] text-zinc-400 hover:border-white/[0.15]'
                )}
              >
                <Columns2 className="w-4 h-4" />
                Two Column
              </button>
            </div>
          </div>
        </div>

        {/* Two-pane drag-drop area */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

          {/* ── Left: Menu Items Panel ─────────────────────────────────── */}
          <div className="flex flex-col rounded-2xl border border-white/[0.07] bg-black/20 overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3 border-b border-white/[0.06]">
              <p className="text-sm font-semibold text-zinc-300">📋 Menu Items</p>
              <span className="text-[11px] text-zinc-500">{allItems.length} items</span>
            </div>

            {/* Search */}
            <div className="px-3 py-2.5 border-b border-white/[0.04]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-zinc-500" />
                <input
                  id="menu-search-input"
                  type="text"
                  placeholder="Search items…"
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  className="w-full rounded-xl border border-white/[0.08] bg-white/[0.04] py-1.5 pl-8 pr-3 text-xs text-zinc-300 placeholder-zinc-600 focus:border-violet-500/40 focus:outline-none transition-all"
                />
              </div>
            </div>

            <div className="flex-1 overflow-y-auto max-h-[420px] space-y-1 p-3">
              {menuLoading && (
                <div className="flex items-center justify-center py-10">
                  <div className="w-5 h-5 rounded-full border-2 border-violet-500/40 border-t-violet-400 animate-spin" />
                </div>
              )}

              {/* Search results mode */}
              {filtered && filtered.map(item => (
                <MenuItemCard key={item.id} item={item} onDragStart={handleMenuItemDragStart} />
              ))}

              {/* Tree mode */}
              {!filtered && fullMenu?.groups?.map((group: MenuGroup) => (
                <div key={group.id}>
                  <button
                    onClick={() => toggleGroup(group.id)}
                    className="w-full flex items-center gap-2 rounded-xl px-2.5 py-2 text-left hover:bg-white/[0.04] transition-all"
                  >
                    {expandedGroups.has(group.id)
                      ? <ChevronDown className="w-3.5 h-3.5 text-zinc-500 flex-shrink-0" />
                      : <ChevronRight className="w-3.5 h-3.5 text-zinc-500 flex-shrink-0" />}
                    <span className="text-xs font-semibold text-zinc-300 uppercase tracking-wider">{group.name}</span>
                    <span className="ml-auto text-[10px] text-zinc-600">
                      {group.sub_groups?.reduce((acc, sg) => acc + (sg.items?.length ?? 0), 0) ?? 0} items
                    </span>
                  </button>

                  {expandedGroups.has(group.id) && group.sub_groups?.map(sg => (
                    <div key={sg.id} className="ml-4">
                      <button
                        onClick={() => toggleSubGroup(sg.id)}
                        className="w-full flex items-center gap-2 rounded-xl px-2.5 py-1.5 text-left hover:bg-white/[0.04] transition-all"
                      >
                        {expandedSubGroups.has(sg.id)
                          ? <ChevronDown className="w-3 h-3 text-zinc-600 flex-shrink-0" />
                          : <ChevronRight className="w-3 h-3 text-zinc-600 flex-shrink-0" />}
                        <span className="text-[11px] font-medium text-zinc-400">{sg.name}</span>
                        <span className="ml-auto text-[10px] text-zinc-600">{sg.items?.length ?? 0}</span>
                      </button>

                      {expandedSubGroups.has(sg.id) && (
                        <div className="ml-3 space-y-1 pb-1">
                          {sg.items?.map(item => (
                            <MenuItemCard key={item.id} item={item} onDragStart={handleMenuItemDragStart} />
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>

          {/* ── Right: Template Canvas ─────────────────────────────────── */}
          <div className="flex flex-col rounded-2xl border border-white/[0.07] bg-black/20 overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3 border-b border-white/[0.06]">
              <p className="text-sm font-semibold text-zinc-300">🎨 Template Preview</p>
              <div className="flex items-center gap-2">
                <span className="text-[11px] text-zinc-500">{slots.length} slot{slots.length !== 1 ? 's' : ''}</span>
                {slots.length > 0 && (
                  <button
                    onClick={() => setSlots([])}
                    className="text-[11px] text-red-400/60 hover:text-red-400 transition-colors"
                  >
                    Clear all
                  </button>
                )}
              </div>
            </div>

            <div className="flex-1 overflow-y-auto max-h-[420px] p-3">
              {slots.length === 0 ? (
                <EmptyDropZone
                  layout={layout}
                  onDragOver={handleDragOver}
                  onDrop={handleDrop}
                />
              ) : (
                <div className={clsx(
                  'gap-2',
                  layout === 'two_column' ? 'grid grid-cols-2' : 'flex flex-col'
                )}>
                  {slots.map((slot, idx) => (
                    <TemplateSlot
                      key={slot.slotId}
                      slot={slot}
                      index={idx}
                      totalSlots={slots.length}
                      layout={layout}
                      onRemove={handleRemoveSlot}
                      onDurationChange={handleDurationChange}
                      onDragOver={handleDragOver}
                      onDrop={handleDrop}
                      onSlotDragStart={handleSlotDragStart}
                    />
                  ))}
                  {/* Additional drop zone at the end */}
                  <div
                    onDragOver={handleDragOver}
                    onDrop={(e) => handleDrop(e, '__empty__')}
                    className={clsx(
                      'flex items-center justify-center rounded-xl border-2 border-dashed border-white/[0.06] text-zinc-700 text-xs py-3 hover:border-violet-500/30 hover:text-zinc-500 transition-all',
                      layout === 'two_column' && slots.length % 2 !== 0 ? 'col-span-2' : ''
                    )}
                  >
                    + drop more here
                  </div>
                </div>
              )}
            </div>

            {/* Save button */}
            <div className="p-3 border-t border-white/[0.06]">
              <button
                id="save-template-btn"
                onClick={handleSave}
                disabled={saveMutation.isPending || slots.length === 0 || !templateName.trim()}
                className="w-full flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-violet-600 to-purple-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-violet-500/20 hover:from-violet-500 hover:to-purple-500 disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-200"
              >
                <Save className="w-4 h-4" />
                {saveMutation.isPending ? 'Saving…' : 'Save Template'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* ── Saved Templates List ─────────────────────────────────────────── */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <h2 className="text-base font-semibold text-zinc-200">Saved Templates</h2>
          <span className="rounded-full bg-white/[0.05] border border-white/[0.08] px-2 py-0.5 text-[11px] text-zinc-400">
            {templates.length}
          </span>
        </div>

        {templatesLoading ? (
          <div className="flex items-center justify-center py-10">
            <div className="w-5 h-5 rounded-full border-2 border-violet-500/40 border-t-violet-400 animate-spin" />
          </div>
        ) : templates.length === 0 ? (
          <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-white/[0.08] py-12 gap-2">
            <LayoutTemplate className="w-8 h-8 text-zinc-700" />
            <p className="text-sm text-zinc-500">No templates yet — create one above</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {templates.map(t => (
              <SavedTemplateCard
                key={t.id}
                template={t}
                onActivate={() => activateMutation.mutate(t.id)}
                onDelete={() => deleteMutation.mutate(t.id)}
                activating={activateMutation.isPending && activateMutation.variables === t.id}
                deleting={deleteMutation.isPending && deleteMutation.variables === t.id}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
