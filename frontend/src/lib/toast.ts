import { createContext, useContext } from 'react'
import type { Badge } from './types'

export interface ToastApi {
  /** Announce a newly unlocked badge. */
  push: (badge: Badge) => void
}

/** Without a provider (tests, isolated components) unlocks are simply not shown. */
export const ToastContext = createContext<ToastApi>({ push: () => {} })

export const useToasts = () => useContext(ToastContext)
