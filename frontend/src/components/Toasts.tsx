import { Star, X } from 'lucide-react'
import { useCallback, useMemo, useState, type ReactNode } from 'react'
import { ToastContext } from '../lib/toast'
import type { Badge } from '../lib/types'

interface Item extends Badge {
  id: number
}

/** Shows each unlocked badge once, announced politely to screen readers, and dismissible. */
export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<Item[]>([])

  const dismiss = useCallback((id: number) => setItems((cur) => cur.filter((t) => t.id !== id)), [])
  const api = useMemo(
    () => ({
      push: (badge: Badge) => {
        const id = Date.now() + Math.random()
        setItems((cur) => [...cur, { ...badge, id }])
        window.setTimeout(() => dismiss(id), 7000)
      },
    }),
    [dismiss],
  )

  return (
    <ToastContext.Provider value={api}>
      {children}
      <div
        role="status"
        aria-live="polite"
        className="pointer-events-none fixed inset-x-0 bottom-4 z-50 mx-auto flex w-full max-w-sm flex-col gap-2 px-4"
      >
        {items.map((t) => (
          <div
            key={t.id}
            className="pointer-events-auto flex items-start gap-3 rounded-2xl border border-accent/40 bg-raised p-4 shadow-2xl"
          >
            <span className="grid size-9 shrink-0 place-items-center rounded-full bg-accent/15 text-accent-strong">
              <Star className="size-4" aria-hidden />
            </span>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-semibold">Unlocked: {t.name}</p>
              <p className="mt-0.5 text-xs text-soft">
                {t.description} +{t.stars} {t.stars === 1 ? 'star' : 'stars'}
              </p>
            </div>
            <button
              type="button"
              onClick={() => dismiss(t.id)}
              aria-label={`Dismiss ${t.name}`}
              className="rounded-md p-1 text-faint hover:text-ink"
            >
              <X className="size-4" aria-hidden />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}
