import { Outlet, Navigate } from 'react-router-dom'
import Sidebar from './Sidebar'
import { useAuthStore } from '@/store/authStore'
import { Toaster } from 'react-hot-toast'

export default function AppLayout() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)

  if (!isAuthenticated) return <Navigate to="/login" replace />

  return (
    <div className="min-h-screen lg:flex">
      <Sidebar />
      <main className="min-w-0 flex-1 overflow-auto">
        <div className="mx-auto w-full max-w-[1400px] p-4 pb-8 pt-5 animate-fade-in sm:p-5 lg:p-6">
          <Outlet />
        </div>
      </main>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#1a1a1a',
            color: '#f4f4f5',
            border: '1px solid rgba(255,255,255,0.08)',
            borderRadius: '12px',
            fontSize: '13px',
          },
          success: { iconTheme: { primary: '#f97316', secondary: '#0a0a0a' } },
        }}
      />
    </div>
  )
}
