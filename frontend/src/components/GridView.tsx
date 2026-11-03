import clsx from 'clsx'
import { Fragment, useMemo } from 'react'
import { errorMessage } from '../lib/api'
import { eachDay, formatDay, goalActiveOn, minISO, monthLabel } from '../lib/dates'
import { useEntries, useSetEntry } from '../lib/queries'
import type { ChallengeDetail, Status } from '../lib/types'
import { ErrorNote, Spinner, STATUS_META } from './ui'

const NEXT: Record<string, Status | null> = { none: 'yes', yes: 'no', no: 'na', na: null }

/** Date-by-goal grid (like the original sheet). Click a cell to cycle: blank → Yes → No → N/A → blank. */
export function GridView({ challenge, today }: { challenge: ChallengeDetail; today: string }) {
  const entries = useEntries(challenge.id)
  const setEntry = useSetEntry(challenge.id)

  const last = minISO(today, challenge.end_date)
  const days = useMemo(
    () => (last >= challenge.start_date ? eachDay(challenge.start_date, last).reverse() : []),
    [challenge.start_date, last],
  )
  const map = useMemo(() => {
    const m = new Map<string, Status>()
    for (const e of entries.data ?? []) m.set(`${e.goal_id}|${e.entry_date}`, e.status)
    return m
  }, [entries.data])

  if (entries.isLoading) return <Spinner label="Loading the grid" />
  if (days.length === 0) {
    return <p className="text-sm text-soft">The challenge hasn't started yet, so there's nothing to log.</p>
  }
  if (challenge.goals.length === 0) {
    return <p className="text-sm text-soft">Add some goals first, then they'll show up here.</p>
  }

  const cols = challenge.goals

  return (
    <div className="grid gap-3">
      {setEntry.isError && <ErrorNote>{errorMessage(setEntry.error)}</ErrorNote>}
      <div className="card max-h-[70dvh] overflow-auto">
        <table className="min-w-full border-separate border-spacing-0 text-sm">
          <thead>
            <tr>
              <th className="sticky left-0 top-0 z-30 border-b border-r border-line bg-surface px-3 py-2.5 text-left text-xs font-medium text-soft">
                Date
              </th>
              {cols.map((g) => (
                <th
                  key={g.id}
                  scope="col"
                  className="sticky top-0 z-20 min-w-[5.5rem] max-w-[7rem] border-b border-line bg-surface px-2 py-2.5 text-left align-bottom text-[0.7rem] font-medium leading-tight text-soft"
                  title={g.name}
                >
                  <span className="line-clamp-3">{g.name}</span>
                  {g.active_to && <span className="mt-1 block text-[0.6rem] text-faint">retired</span>}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {days.map((d, i) => {
              const newMonth = i === 0 || d.slice(0, 7) !== days[i - 1].slice(0, 7)
              return (
                <Fragment key={d}>
                  {newMonth && (
                    <tr>
                      <th
                        colSpan={cols.length + 1}
                        scope="colgroup"
                        className="sticky left-0 bg-raised/70 px-3 py-1.5 text-left text-[0.7rem] font-semibold uppercase tracking-wider text-faint"
                      >
                        {monthLabel(d)}
                      </th>
                    </tr>
                  )}
                  <tr className={d === today ? 'bg-accent/[0.06]' : undefined}>
                    <th
                      scope="row"
                      className="sticky left-0 z-10 whitespace-nowrap border-b border-r border-line bg-surface px-3 py-1.5 text-left text-xs font-medium text-soft"
                    >
                      {formatDay(d)}
                    </th>
                    {cols.map((g) => {
                      const active = goalActiveOn(g, d)
                      const status = map.get(`${g.id}|${d}`) ?? null
                      return (
                        <td key={g.id} className="border-b border-line/60 p-1 text-center">
                          {active ? (
                            <Cell
                              status={status}
                              label={`${g.name}, ${formatDay(d)}`}
                              onClick={() =>
                                setEntry.mutate({ goalId: g.id, date: d, status: NEXT[status ?? 'none'] })
                              }
                            />
                          ) : (
                            <span className="block text-faint/40" aria-label="Goal not active on this day">
                              ·
                            </span>
                          )}
                        </td>
                      )
                    })}
                  </tr>
                </Fragment>
              )
            })}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-faint">Tap a cell to cycle: blank → Yes → No → N/A → blank.</p>
    </div>
  )
}

function Cell({
  status,
  label,
  onClick,
}: {
  status: Status | null
  label: string
  onClick: () => void
}) {
  const meta = status ? STATUS_META[status] : null
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={`${label}: ${meta ? meta.short : 'not logged'}. Activate to change.`}
      className={clsx(
        'mx-auto grid size-9 place-items-center rounded-lg border text-xs font-semibold transition-colors',
        meta ? meta.on : 'border-transparent text-faint/50 hover:border-line-strong hover:bg-raised',
      )}
    >
      {meta ? <meta.Icon className="size-3.5" aria-hidden /> : <span aria-hidden>·</span>}
    </button>
  )
}
