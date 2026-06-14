import { NavLink, useNavigate } from 'react-router-dom'
import { Tv2, LayoutDashboard, UtensilsCrossed, Monitor, Users, Building2, LogOut, ChevronRight, LayoutTemplate } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import toast from 'react-hot-toast'
import clsx from 'clsx'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard', end: true },
  { to: '/menu', icon: UtensilsCrossed, label: 'Menu Manager' },
  { to: '/templates', icon: LayoutTemplate, label: 'Templates' },
  { to: '/devices', icon: Monitor, label: 'Devices' },
  { to: '/restaurants', icon: Building2, label: 'Restaurants', roles: ['super_admin'] },
  { to: '/users', icon: Users, label: 'Users', roles: ['super_admin', 'manager'] },
]

export default function Sidebar() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    toast.success('Logged out')
    navigate('/login')
  }

  const visibleItems = navItems.filter(
    (item) => !item.roles || (user && item.roles.includes(user.role))
  )

  return (
    <aside className="sticky top-0 z-40 flex flex-col border-b border-white/[0.06] bg-[#0d0d0d]/95 backdrop-blur lg:h-screen lg:w-64 lg:flex-shrink-0 lg:border-b-0 lg:border-r">
      {/* Logo */}
      <div className="flex items-center gap-3 border-b border-white/[0.06] px-4 py-3 lg:px-5 lg:py-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-brand-500/30 bg-brand-500/15 shadow-glow">
          <Tv2 className="w-5 h-5 text-brand-400" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="font-display font-bold text-zinc-100 leading-none">MenuVision</p>
          <p className="text-[10px] text-zinc-500 mt-0.5 tracking-widest uppercase">Admin Panel</p>
        </div>
        <button onClick={handleLogout} className="btn-ghost px-2.5 lg:hidden" title="Sign out">
          <LogOut className="h-4 w-4" />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex gap-2 overflow-x-auto px-3 py-2 lg:block lg:flex-1 lg:space-y-0.5 lg:overflow-y-auto lg:py-4">
        {visibleItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              clsx('sidebar-link group flex-shrink-0 lg:shrink', isActive && 'active')
            }
          >
            <item.icon className="w-4 h-4 flex-shrink-0" />
            <span className="flex-1 whitespace-nowrap">{item.label}</span>
            <ChevronRight className="hidden w-3 h-3 opacity-0 transition-opacity group-hover:opacity-50 lg:block" />
          </NavLink>
        ))}
      </nav>

      {/* User footer */}
      <div className="hidden px-3 py-3 border-t border-white/[0.06] lg:block">
        <div className="flex items-center gap-3 px-3 py-2.5 rounded-xl mb-1">
          <div className="w-8 h-8 rounded-full bg-brand-500/20 border border-brand-500/30 flex items-center justify-center text-brand-400 text-sm font-bold uppercase flex-shrink-0">
            {user?.full_name?.[0] ?? 'U'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-zinc-200 truncate">{user?.full_name}</p>
            <p className="text-[11px] text-zinc-500 capitalize truncate">
              {user?.role.replace('_', ' ')}
            </p>
          </div>
        </div>
        <button onClick={handleLogout} className="btn-ghost w-full text-red-400 hover:text-red-300 hover:bg-red-500/10">
          <LogOut className="w-4 h-4" />
          Sign Out
        </button>
      </div>
    </aside>
  )
}
