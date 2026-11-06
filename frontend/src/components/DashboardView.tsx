import clsx from 'clsx'
import { useMemo, useState, type ReactNode } from 'react'
import { errorMessage } from '../lib/api'
import { pct } from '../lib/format'
import { monthLabel } from '../lib/dates'
import { useDashboard } from '../lib/queries'
import type { ChallengeDetail, Dashboard } from '../lib/types'
import { EmptyState, ErrorNote, Spinner } from './ui'

const month = (key: string) => monthLabel(`${key}-01`)

export function DashboardView({ challenge }: { challenge: ChallengeDetail }) {
  const { data, isLoading, isError, error } = useDashboard(challenge.id)

  if (isLoading) return <Spinner label="Loading dashboard" />
  if (isError || !data) return <ErrorNote>{errorMessage(error)}</ErrorNote>
  if (data.kpis.days_in === 0) {
    return (
      <EmptyState
        title="Nothing to show yet"
        hint="Log your first day and your numbers appear here."
      />
    )
  }
  return <DashboardContent data={data} />
}

export function DashboardContent({ data }: { data: Dashboard }) {
  const names = useMemo(() => new Map(data.goals.map((g) => [g.goal_id, g.name])), [data.goals])
  const k = data.kpis
  const scores = data.days.flatMap((d) => (d.score == null ? [] : [d.score]))
  const total = {
    avg: scores.length ? scores.reduce((a, b) => a + b, 0) / scores.length : null,
    best: scores.length ? Math.max(...scores) : null,
  }
  const startedMonths = data.months.filter((m) => m.days > 0)

  return (
    <div className="grid gap-8">
      <section aria-label="Key numbers" className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <Kpi label="Overall completion" value={pct(k.overall_completion)} accent />
        <Kpi label="Days in" value={`${k.days_in}`} hint={`of ${k.total_days}`} />
        <Kpi label="Days left" value={`${k.days_left}`} />
        <Kpi label="Goals completed" value={`${k.goals_completed}`} hint={`${k.missed} missed · ${k.na} N/A`} />
        <Kpi label="Day streak" value={`${data.streaks.current}`} hint={`best ${data.streaks.longest}`} />
        <Kpi label="Perfect days" value={`${k.perfect_days}`} hint="every goal done" />
      </section>

      <Panel title="By goal">
        <GoalTable data={data} />
      </Panel>

      <Panel title="By month">
        <Table
          head={['Month', 'Days', 'Done', 'Missed', 'N/A', 'Completion', 'Perfect', 'Avg day', 'Best day']}
          rows={startedMonths.map((m) => [
            month(m.month),
            m.days,
            m.done,
            m.missed,
            m.na,
            pct(m.completion),
            m.perfect_days,
            pct(m.avg_daily_score),
            pct(m.best_day),
          ])}
          total={[
            'Total',
            k.days_in,
            k.goals_completed,
            k.missed,
            k.na,
            pct(k.overall_completion),
            k.perfect_days,
            pct(total.avg),
            pct(total.best),
          ]}
        />
      </Panel>

      <Panel title="Each goal, month by month">
        <div className="grid gap-6">
          {startedMonths.map((m) => {
            const rows = data.goal_months.filter((r) => r.month === m.month)
            return (
              <div key={m.month}>
                <h4 className="mb-2 text-sm font-medium text-soft">{month(m.month)}</h4>
                <Table
                  head={['Goal', 'Done', 'Missed', 'N/A', 'Completion']}
                  rows={rows.map((r) => [names.get(r.goal_id) ?? '', r.done, r.missed, r.na, pct(r.completion)])}
                  total={['Total', m.done, m.missed, m.na, pct(m.completion)]}
                />
              </div>
            )
          })}
        </div>
      </Panel>

      <Panel title="By week">
        <WeekChart data={data} />
        <Table
          head={['Week', 'Dates', 'Goals hit', 'Possible', 'Completion']}
          rows={data.weeks
            .filter((w) => w.possible > 0)
            .map((w) => [`Week ${w.week}`, `${w.from.slice(5)} to ${w.to.slice(5)}`, w.done, w.possible, pct(w.completion)])}
        />
      </Panel>
    </div>
  )
}

// ---------------------------------------------------------------- pieces
function Kpi({ label, value, hint, accent }: { label: string; value: string; hint?: string; accent?: boolean }) {
  return (
    <div className="card p-4">
      <div className="text-xs text-faint">{label}</div>
      <div className={clsx('mt-1 text-3xl font-semibold tabular-nums', accent && 'text-accent-strong')}>{value}</div>
      {hint && <div className="mt-0.5 text-xs text-soft">{hint}</div>}
    </div>
  )
}

function Panel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="card p-5 sm:p-6">
      <h3 className="mb-4 text-base font-semibold">{title}</h3>
      {children}
    </section>
  )
}

type Cell = string | number

function Table({ head, rows, total }: { head: string[]; rows: Cell[][]; total?: Cell[] }) {
  const body = (cells: Cell[], key: string | number, strong = false) => (
    <tr key={key} className={clsx('border-t border-line', strong && 'font-semibold')}>
      {cells.map((c, i) => (
        <td key={i} className={clsx('px-3 py-2', i > 0 && 'text-right tabular-nums')}>
          {c}
        </td>
      ))}
    </tr>
  )
  return (
    <div className="-mx-1 overflow-x-auto px-1">
      <table className="w-full min-w-max text-sm">
        <thead>
          <tr className="text-xs text-faint">
            {head.map((h, i) => (
              <th key={h} scope="col" className={clsx('px-3 py-2 font-medium', i === 0 ? 'text-left' : 'text-right')}>
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => body(r, i))}
          {total && body(total, 'total', true)}
        </tbody>
      </table>
    </div>
  )
}

type SortKey = 'order' | 'name' | 'done' | 'missed' | 'na' | 'completion'

function GoalTable({ data }: { data: Dashboard }) {
  const [sort, setSort] = useState<{ key: SortKey; dir: 1 | -1 }>({ key: 'order', dir: 1 })
  const rows = useMemo(() => {
    const { key, dir } = sort
    if (key === 'order') return data.goals
    const pick = (g: Dashboard['goals'][number]) => (key === 'name' ? g.name.toLowerCase() : (g[key] ?? -1))
    return [...data.goals].sort((a, b) => (pick(a) < pick(b) ? -dir : pick(a) > pick(b) ? dir : 0))
  }, [data.goals, sort])

  const th = (key: SortKey, label: string, align: 'left' | 'right' = 'right') => (
    <th
      scope="col"
      aria-sort={sort.key === key ? (sort.dir === 1 ? 'ascending' : 'descending') : undefined}
      className={clsx('px-3 py-2 font-medium', align === 'left' ? 'text-left' : 'text-right')}
    >
      <button
        type="button"
        className="hover:text-ink"
        onClick={() => setSort((s) => ({ key, dir: s.key === key && s.dir === 1 ? -1 : 1 }))}
      >
        {label}
        {sort.key === key && (sort.dir === 1 ? ' ↑' : ' ↓')}
      </button>
    </th>
  )

  return (
    <div className="-mx-1 overflow-x-auto px-1">
      <table className="w-full min-w-max text-sm">
        <thead>
          <tr className="text-xs text-faint">
            {th('name', 'Goal', 'left')}
            {th('done', 'Done')}
            {th('missed', 'Missed')}
            {th('na', 'N/A')}
            {th('completion', 'Completion')}
            <th scope="col" className="w-32 px-3 py-2" aria-label="Progress" />
          </tr>
        </thead>
        <tbody>
          {rows.map((g) => (
            <tr key={g.goal_id} className="border-t border-line">
              <td className="px-3 py-2">
                {g.name}
                {g.retired && (
                  <span className="ml-2 rounded-full border border-line px-2 py-0.5 text-[11px] text-faint">retired</span>
                )}
              </td>
              <td className="px-3 py-2 text-right tabular-nums">{g.done}</td>
              <td className="px-3 py-2 text-right tabular-nums">{g.missed}</td>
              <td className="px-3 py-2 text-right tabular-nums">{g.na}</td>
              <td className="px-3 py-2 text-right tabular-nums">{pct(g.completion)}</td>
              <td className="px-3 py-2">
                <Bar value={g.completion} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-2 px-3 text-xs text-faint">Click a column heading to sort.</p>
    </div>
  )
}

function Bar({ value }: { value: number | null }) {
  return (
    <div aria-hidden className="h-1.5 w-28 overflow-hidden rounded-full bg-line">
      <div className="h-full rounded-full bg-accent" style={{ width: `${Math.round((value ?? 0) * 100)}%` }} />
    </div>
  )
}

/** The table below is the text alternative, so the bars are decorative. */
function WeekChart({ data }: { data: Dashboard }) {
  const weeks = data.weeks.filter((w) => w.possible > 0)
  if (!weeks.length) return null
  return (
    <div aria-hidden className="mb-5 flex h-28 items-end gap-2">
      {weeks.map((w) => (
        <div key={w.week} className="flex h-full flex-1 flex-col justify-end gap-1 text-center">
          <div className="text-[11px] text-soft tabular-nums">{pct(w.completion)}</div>
          <div className="rounded-t bg-accent/80" style={{ height: `${Math.round((w.completion ?? 0) * 70)}%` }} />
          <div className="text-[11px] text-faint">W{w.week}</div>
        </div>
      ))}
    </div>
  )
}
