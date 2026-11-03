import { Check, Loader2, Minus, X } from 'lucide-react'
import clsx from 'clsx'
import {
  useEffect,
  useRef,
  type ButtonHTMLAttributes,
  type ReactNode,
} from 'react'
import type { Status } from '../lib/types'

/* ------------------------------------------------------------------ Button */
type Variant = 'primary' | 'secondary' | 'ghost' | 'danger'

export function Button({
  variant = 'secondary',
  loading,
  className,
  children,
  disabled,
  ...rest
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; loading?: boolean }) {
  const styles: Record<Variant, string> = {
    primary: 'bg-accent text-accent-ink hover:bg-accent-strong font-semibold',
    secondary: 'bg-raised text-ink border border-line hover:border-line-strong hover:bg-[#1b1e29]',
    ghost: 'text-soft hover:text-ink hover:bg-white/5',
    danger: 'bg-no/10 text-no border border-no/30 hover:bg-no/15',
  }
  return (
    <button
      {...rest}
      disabled={disabled || loading}
      className={clsx(
        'inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium',
        'transition-colors disabled:cursor-not-allowed disabled:opacity-50',
        styles[variant],
        className,
      )}
    >
      {loading && <Loader2 className="size-4 animate-spin" aria-hidden />}
      {children}
    </button>
  )
}

/* ------------------------------------------------------------------ Spinner */
export function Spinner({ label = 'Loading' }: { label?: string }) {
  return (
    <div role="status" className="inline-flex items-center gap-2 text-sm text-soft">
      <Loader2 className="size-4 animate-spin" aria-hidden />
      <span>{label}…</span>
    </div>
  )
}

/* ------------------------------------------------------------------ Notices */
export function ErrorNote({ children }: { children: ReactNode }) {
  if (!children) return null
  return (
    <p role="alert" className="rounded-xl border border-no/30 bg-no/10 px-3.5 py-2.5 text-sm text-no">
      {children}
    </p>
  )
}

export function InfoNote({ children }: { children: ReactNode }) {
  return (
    <p role="status" className="rounded-xl border border-accent/30 bg-accent/10 px-3.5 py-2.5 text-sm text-accent-strong">
      {children}
    </p>
  )
}

export function EmptyState({
  title,
  hint,
  action,
}: {
  title: string
  hint?: string
  action?: ReactNode
}) {
  return (
    <div className="card flex flex-col items-center gap-3 px-6 py-14 text-center">
      <div className="grid size-11 place-items-center rounded-2xl border border-line bg-raised text-accent">
        <Check className="size-5" aria-hidden />
      </div>
      <h3 className="text-base font-semibold">{title}</h3>
      {hint && <p className="max-w-sm text-sm text-soft">{hint}</p>}
      {action}
    </div>
  )
}

/* ------------------------------------------------------------------ Status (Yes / No / N/A) */
export const STATUS_META: Record<
  Status,
  { label: string; short: string; Icon: typeof Check; on: string; dot: string }
> = {
  yes: {
    label: 'Yes',
    short: 'Done',
    Icon: Check,
    on: 'border-yes/40 bg-yes/15 text-yes',
    dot: 'text-yes',
  },
  no: {
    label: 'No',
    short: 'Missed',
    Icon: X,
    on: 'border-no/40 bg-no/15 text-no',
    dot: 'text-no',
  },
  na: {
    label: 'N/A',
    short: 'Not available',
    Icon: Minus,
    on: 'border-na/40 bg-na/15 text-na',
    dot: 'text-na',
  },
}

const ORDER: Status[] = ['yes', 'no', 'na']

/** Three-state control. Tapping the selected option clears it (back to "not logged"). */
export function StatusControl({
  value,
  onChange,
  label,
  disabled,
}: {
  value: Status | null
  onChange: (next: Status | null) => void
  label: string
  disabled?: boolean
}) {
  return (
    <div role="group" aria-label={label} className="inline-flex gap-1.5">
      {ORDER.map((s) => {
        const meta = STATUS_META[s]
        const selected = value === s
        return (
          <button
            key={s}
            type="button"
            disabled={disabled}
            aria-pressed={selected}
            aria-label={`${meta.short}${selected ? ' (selected, tap to clear)' : ''}`}
            onClick={() => onChange(selected ? null : s)}
            className={clsx(
              'inline-flex h-10 min-w-[3.25rem] items-center justify-center gap-1 rounded-xl border px-2.5',
              'text-xs font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-40',
              selected
                ? meta.on
                : 'border-line bg-raised text-faint hover:border-line-strong hover:text-soft',
            )}
          >
            <meta.Icon className="size-3.5" aria-hidden />
            {meta.label}
          </button>
        )
      })}
    </div>
  )
}

/* ------------------------------------------------------------------ Dialog (native <dialog>) */
export function Dialog({
  open,
  onClose,
  title,
  children,
}: {
  open: boolean
  onClose: () => void
  title: string
  children: ReactNode
}) {
  const ref = useRef<HTMLDialogElement>(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    if (open && !el.open) el.showModal()
    if (!open && el.open) el.close()
  }, [open])

  return (
    <dialog
      ref={ref}
      onClose={onClose}
      onClick={(e) => {
        if (e.target === ref.current) onClose() // click on the backdrop
      }}
      aria-label={title}
      className="m-auto w-[min(26rem,calc(100vw-2rem))] rounded-2xl border border-line-strong bg-surface p-0 text-ink shadow-[var(--shadow-pop)] backdrop:bg-black/70 backdrop:backdrop-blur-sm"
    >
      {open && (
        <div className="p-6">
          <h2 className="mb-4 text-lg font-semibold">{title}</h2>
          {children}
        </div>
      )}
    </dialog>
  )
}

/* ------------------------------------------------------------------ Misc */
export function Logo({ className }: { className?: string }) {
  return (
    <span className={clsx('inline-flex items-center gap-2.5 font-semibold tracking-tight', className)}>
      <span className="grid size-8 place-items-center rounded-[0.6rem] border border-line bg-raised">
        <Check className="size-4 text-accent" strokeWidth={3} aria-hidden />
      </span>
      Streak
    </span>
  )
}

export function Field({
  label,
  hint,
  children,
}: {
  label: string
  hint?: string
  children: ReactNode
}) {
  return (
    <label className="block">
      <span className="label">{label}</span>
      {children}
      {hint && <span className="mt-1.5 block text-xs text-faint">{hint}</span>}
    </label>
  )
}
