import { useQuery } from '@tanstack/react-query'
import { UtensilsCrossed, Monitor, Building2, Wifi, WifiOff, TrendingUp, ChefHat, Clock } from 'lucide-react'
import { menuApi, devicesApi, restaurantsApi } from '@/api/services'
import { useAuthStore } from '@/store/authStore'

function StatCard({ icon: Icon, label, value, sub, color = 'brand' }: {
  icon: any; label: string; value: string | number; sub?: string; color?: string
}) {
  const colors: Record<string, string> = {
    brand: 'bg-brand-500/10 text-brand-400 border-brand-500/20',
    emerald: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    blue: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    amber: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    red: 'bg-red-500/10 text-red-400 border-red-500/20',
  }
  return (
    <div className="stat-card">
      <div className={`w-11 h-11 rounded-xl flex items-center justify-center border flex-shrink-0 ${colors[color]}`}>
        <Icon className="w-5 h-5" />
      </div>
      <div>
        <p className="text-2xl font-bold text-zinc-100">{value}</p>
        <p className="text-sm text-zinc-400">{label}</p>
        {sub && <p className="text-xs text-zinc-600 mt-0.5">{sub}</p>}
      </div>
    </div>
  )
}

export default function DashboardPage() {
  const { user } = useAuthStore()
  const restaurantId = user?.restaurant_id

  const { data: restaurants = [] } = useQuery({
    queryKey: ['restaurants'],
    queryFn: () => restaurantsApi.list().then((r) => r.data),
  })

  const { data: devices = [] } = useQuery({
    queryKey: ['devices'],
    queryFn: () => devicesApi.list().then((r) => r.data),
  })

  const { data: groups = [] } = useQuery({
    queryKey: ['menu-groups', restaurantId],
    queryFn: () => menuApi.listGroups(restaurantId!).then((r) => r.data),
    enabled: !!restaurantId,
  })

  const activeDevices = devices.filter((d) => d.status === 'active').length
  const offlineDevices = devices.filter((d) => d.status !== 'active').length
  const totalGroups = groups.length

  const now = new Date()
  const hour = now.getHours()
  const session = hour < 11 ? 'Breakfast' : hour < 15 ? 'Lunch' : 'Dinner'
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening'

  return (
    <div className="space-y-6 lg:space-y-8">
      {/* Header */}
      <div>
        <h1 className="font-display text-2xl font-bold text-zinc-50 sm:text-3xl">
          {greeting}, {user?.full_name?.split(' ')[0]} 👋
        </h1>
        <p className="text-zinc-500 mt-1 text-sm">
          Current session: <span className="text-brand-400 font-medium">{session}</span> · {now.toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long' })}
        </p>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard icon={Building2} label="Restaurants" value={restaurants.length} color="blue" />
        <StatCard icon={UtensilsCrossed} label="Menu Categories" value={totalGroups} color="brand" />
        <StatCard icon={Monitor} label="Active Screens" value={activeDevices} sub={`${offlineDevices} offline`} color="emerald" />
        <StatCard icon={Clock} label="Active Session" value={session} sub="Auto-detected" color="amber" />
      </div>

      {/* Device status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card p-4 sm:p-6">
          <div className="flex items-center justify-between gap-3 mb-5">
            <h2 className="font-semibold text-zinc-100">Connected Devices</h2>
            <span className="text-xs text-zinc-500">{devices.length} total</span>
          </div>
          {devices.length === 0 ? (
            <div className="text-center py-10 text-zinc-600">
              <Monitor className="w-10 h-10 mx-auto mb-2 opacity-30" />
              <p className="text-sm">No devices registered yet</p>
            </div>
          ) : (
            <div className="space-y-2">
              {devices.slice(0, 6).map((device) => (
                <div key={device.id} className="flex items-center gap-3 p-3 rounded-xl bg-white/[0.03] border border-white/[0.05]">
                  <div className={`w-2 h-2 rounded-full flex-shrink-0 ${device.status === 'active' ? 'bg-emerald-400 animate-pulse' : 'bg-zinc-600'}`} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-zinc-200 truncate">{device.name}</p>
                    <p className="text-xs text-zinc-500">Display #{device.display_number}</p>
                  </div>
                  {device.status === 'active'
                    ? <Wifi className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                    : <WifiOff className="w-4 h-4 text-zinc-600 flex-shrink-0" />
                  }
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="card p-4 sm:p-6">
          <div className="flex items-center justify-between gap-3 mb-5">
            <h2 className="font-semibold text-zinc-100">Menu Overview</h2>
            <span className="text-xs text-zinc-500">{groups.reduce((acc, g) => acc + (g.sub_groups?.length ?? 0), 0)} sub-categories</span>
          </div>
          {groups.length === 0 ? (
            <div className="text-center py-10 text-zinc-600">
              <ChefHat className="w-10 h-10 mx-auto mb-2 opacity-30" />
              <p className="text-sm">No menu groups yet</p>
            </div>
          ) : (
            <div className="space-y-2">
              {groups.map((group) => (
                <div key={group.id} className="flex items-center gap-3 p-3 rounded-xl bg-white/[0.03] border border-white/[0.05]">
                  <div className="w-8 h-8 rounded-lg bg-brand-500/10 border border-brand-500/20 flex items-center justify-center flex-shrink-0">
                    <UtensilsCrossed className="w-4 h-4 text-brand-400" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-zinc-200">{group.name}</p>
                    {group.instruction && <p className="text-xs text-zinc-500 truncate">{group.instruction}</p>}
                  </div>
                  <span className={`text-xs px-2 py-0.5 rounded-full border ${group.is_active ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-zinc-500/10 text-zinc-500 border-zinc-500/20'}`}>
                    {group.is_active ? 'Active' : 'Hidden'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Quick publish */}
      {restaurantId && (
        <div className="card border-brand-500/20 bg-brand-500/5 p-4 sm:p-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="font-semibold text-zinc-100 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-brand-400" />
                Push to All Screens
              </h2>
              <p className="text-sm text-zinc-500 mt-1">
                Instantly broadcast your current menu to all connected TV displays.
              </p>
            </div>
            <PublishButton restaurantId={restaurantId} />
          </div>
        </div>
      )}
    </div>
  )
}

function PublishButton({ restaurantId }: { restaurantId: number }) {
  const [loading, setLoading] = useState(false)
  const handlePublish = async () => {
    setLoading(true)
    try {
      await menuApi.publish(restaurantId)
      toast.success('Menu published to all screens!', { icon: '📺' })
    } catch {
      toast.error('Publish failed')
    } finally {
      setLoading(false)
    }
  }
  return (
    <button onClick={handlePublish} disabled={loading} className="btn-primary w-full flex-shrink-0 sm:w-auto">
      {loading ? 'Publishing...' : '📺 Publish Now'}
    </button>
  )
}

// Add missing imports at top level
import { useState } from 'react'
import toast from 'react-hot-toast'
