import { useMemo } from 'react'
import { goalActiveOn } from '../lib/dates'
import { errorMessage } from '../lib/api'
import { useEntries, useSetEntry } from '../lib/queries'
import type { ChallengeDetail, Status } from '../lib/types'
import { ErrorNote, Spinner, StatusControl } from './ui'

/** Log one day for one challenge: each active goal gets a Yes / No / N/A control. */
export function DayLog({ challenge, date }: { challenge: ChallengeDetail; date: string }) {
  const entries = useEntries(challenge.id)
  const setEntry = useSetEntry(challenge.id)

  const byGoal = useMemo(() => {
    const m = new Map<string, Status>()
    for (const e of entries.data ?? []) if (e.entry_date === date) m.set(e.goal_id, e.status)
    return m
  }, [entries.data, date])

  const outside = date < challenge.start_date || date > challenge.end_date
  const goals = challenge.goals.filter((g) => goalActiveOn(g, date))
  const logged = goals.filter((g) => byGoal.has(g.id)).length

  if (outside) {
    return (
      <p className="rounded-xl border border-line bg-raised/60 px-4 py-3 text-sm text-soft">
        This day is outside the challenge ({challenge.start_date} to {challenge.end_date}).
      </p>
    )
  }
  if (goals.length === 0) {
    return (
      <p className="rounded-xl border border-line bg-raised/60 px-4 py-3 text-sm text-soft">
        No goals were active on this day.
      </p>
    )
  }
  if (entries.isLoading) return <Spinner label="Loading your log" />

  return (
    <div>
      {setEntry.isError && <ErrorNote>{errorMessage(setEntry.error)}</ErrorNote>}
      {entries.isError && <ErrorNote>{errorMessage(entries.error)}</ErrorNote>}

      <div className="mb-3 flex items-center gap-3">
        <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-white/[0.06]">
          <div
            className="h-full rounded-full bg-accent transition-all"
            style={{ width: `${(logged / goals.length) * 100}%` }}
          />
        </div>
        <span className="text-xs tabular-nums text-soft">
          {logged}/{goals.length} logged
        </span>
      </div>

      <ul className="divide-y divide-line/70">
        {goals.map((g) => (
          <li key={g.id} className="flex flex-wrap items-center justify-between gap-3 py-3">
            <span className="min-w-0 flex-1 text-[0.95rem] font-medium">{g.name}</span>
            <StatusControl
              label={g.name}
              value={byGoal.get(g.id) ?? null}
              onChange={(status) => setEntry.mutate({ goalId: g.id, date, status })}
            />
          </li>
        ))}
      </ul>
    </div>
  )
}
