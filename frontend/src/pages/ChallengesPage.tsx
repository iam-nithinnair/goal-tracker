import { Plus } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Button, EmptyState, Spinner } from '../components/ui'
import { errorMessage } from '../lib/api'
import { daysBetween, formatRange, phaseOf, todayIn } from '../lib/dates'
import { useChallenges, useProfile } from '../lib/queries'
import type { Challenge } from '../lib/types'

export function ChallengesPage() {
  const { data: profile } = useProfile()
  const { data, isLoading, isError, error } = useChallenges()
  const today = todayIn(profile?.timezone ?? Intl.DateTimeFormat().resolvedOptions().timeZone)

  if (isLoading) return <Spinner label="Loading challenges" />
  if (isError) return <p className="text-no">{errorMessage(error)}</p>

  const active = (data ?? []).filter((c) => c.status === 'active')
  const archived = (data ?? []).filter((c) => c.status === 'archived')

  return (
    <div className="grid gap-8">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold">Challenges</h1>
          <p className="mt-1.5 text-soft">Time-boxed streaks with a set of daily goals.</p>
        </div>
        <Link to="/challenges/new">
          <Button variant="primary">
            <Plus className="size-4" aria-hidden /> New
          </Button>
        </Link>
      </div>

      {active.length === 0 && archived.length === 0 ? (
        <EmptyState
          title="Nothing here yet"
          hint="Start from the Winter Arc template or build your own list of goals."
          action={
            <Link to="/challenges/new">
              <Button variant="primary">Create a challenge</Button>
            </Link>
          }
        />
      ) : (
        <>
          <Section title="Active" items={active} today={today} />
          {archived.length > 0 && <Section title="Archived" items={archived} today={today} muted />}
        </>
      )}
    </div>
  )
}

function Section({
  title,
  items,
  today,
  muted,
}: {
  title: string
  items: Challenge[]
  today: string
  muted?: boolean
}) {
  if (items.length === 0) return null
  return (
    <section>
      <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-faint">{title}</h2>
      <ul className="grid gap-3 sm:grid-cols-2">
        {items.map((c) => {
          const phase = phaseOf(c, today)
          const total = daysBetween(c.start_date, c.end_date) + 1
          const pct =
            phase === 'upcoming'
              ? 0
              : Math.min(100, ((daysBetween(c.start_date, today) + 1) / total) * 100)
          return (
            <li key={c.id}>
              <Link
                to={`/challenges/${c.id}`}
                className={`card block p-5 transition-colors hover:border-line-strong ${muted ? 'opacity-70' : ''}`}
              >
                <div className="flex items-start justify-between gap-3">
                  <h3 className="font-semibold">{c.name}</h3>
                  <PhaseBadge phase={c.status === 'archived' ? 'archived' : phase} />
                </div>
                <p className="mt-1 text-sm text-soft">{formatRange(c.start_date, c.end_date)}</p>
                <div className="mt-4 h-1 overflow-hidden rounded-full bg-white/[0.06]">
                  <div className="h-full rounded-full bg-accent/80" style={{ width: `${pct}%` }} />
                </div>
                <p className="mt-2 text-xs text-faint">{total} days</p>
              </Link>
            </li>
          )
        })}
      </ul>
    </section>
  )
}

function PhaseBadge({ phase }: { phase: 'upcoming' | 'running' | 'finished' | 'archived' }) {
  const label = { upcoming: 'Upcoming', running: 'Running', finished: 'Finished', archived: 'Archived' }[phase]
  const tone =
    phase === 'running'
      ? 'border-accent/40 text-accent-strong'
      : phase === 'upcoming'
        ? 'border-warn/40 text-warn'
        : 'border-line-strong text-soft'
  return <span className={`rounded-full border px-2.5 py-0.5 text-[0.7rem] font-medium ${tone}`}>{label}</span>
}
