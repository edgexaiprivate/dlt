import { useQuery } from '@tanstack/react-query'
import { Store } from 'lucide-react'
import { restaurantsApi } from '@/api/services'

export default function RestaurantSelector({
  value,
  onChange,
}: {
  value: number | null
  onChange: (id: number) => void
}) {
  const { data: restaurants = [], isLoading } = useQuery({
    queryKey: ['restaurants'],
    queryFn: () => restaurantsApi.list().then((r) => r.data),
  })

  return (
    <div className="card flex flex-col gap-4 p-4 sm:flex-row sm:items-center">
      <div className="w-10 h-10 rounded-xl bg-orange-500/10 flex items-center justify-center flex-shrink-0">
        <Store className="w-5 h-5 text-orange-400" />
      </div>
      <div className="w-full min-w-0 flex-1">
        <p className="text-xs text-zinc-500 mb-1 font-medium tracking-wide">SELECT RESTAURANT</p>
        {isLoading ? (
          <div className="h-8 bg-white/5 rounded-lg animate-pulse" />
        ) : (
          <select
            value={value ?? ''}
            onChange={(e) => onChange(Number(e.target.value))}
            className="input py-1.5 text-sm"
          >
            <option value="">-- Pick a restaurant --</option>
            {restaurants.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name}
              </option>
            ))}
          </select>
        )}
      </div>
    </div>
  )
}
