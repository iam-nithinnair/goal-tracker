import { Flame, Star } from 'lucide-react'
import { formatDay, formatRange } from '../lib/dates'
import { pct } from '../lib/format'
import type { SharedView } from '../lib/types'
import { DashboardContent } from './DashboardView'

/** The read-only picture of someone's challenge: the same for a public link and for a friend. */
export function SharedSummary({ view }: { view: SharedView }) {
  return (
    <div className="grid gap-8">
      <div>
        <p className="text-sm text-soft">{view.display_name}'s challenge</p>
        <h1 className="mt-1 text-3xl font-semibold">{view.challenge_name}</h1>
        <p className="mt-1.5 text-sm text-soft">{formatRange(view.start_date, view.end_date)}</p>
      </div>

      <section aria-label="Highlights" className="grid grid-cols-3 gap-3">
        <Tile label="Completion" value={pct(view.completion)} />
        <Tile
          label="Day streak"
          value={String(view.streaks.current)}
          hint={`best ${view.streaks.longest}`}
          icon={<Flame className="size-4 text-accent-strong" aria-hidden />}
        />
        <Tile
          label="Stars"
          value={String(view.stars)}
          icon={<Star className="size-4 text-accent-strong" aria-hidden />}
        />
      </section>

      <section aria-labelledby="badges-h">
        <h2 id="badges-h" className="mb-3 text-base font-semibold">
          Badges <span className="text-faint">({view.badges.length})</span>
        </h2>
        {view.badges.length === 0 ? (
          <p className="text-sm text-soft">No badges earned yet.</p>
        ) : (
          <ul className="flex flex-wrap gap-2">
            {view.badges.map((b) => (
              <li
                key={b.code}
                className="flex items-center gap-1.5 rounded-full border border-line bg-raised px-3 py-1.5 text-sm"
                title={`Earned ${formatDay(b.earned_on, { weekday: undefined, year: 'numeric' })}`}
              >
                <Star className="size-3.5 text-accent-strong" aria-hidden />
                {b.name}
                <span className="text-xs text-faint">{b.stars}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      {view.dashboard && <DashboardContent data={view.dashboard} />}
    </div>
  )
}

function Tile({
  label,
  value,
  hint,
  icon,
}: {
  label: string
  value: string
  hint?: string
  icon?: React.ReactNode
}) {
  return (
    <div className="card p-4">
      <div className="flex items-center gap-1.5 text-xs text-faint">
        {icon}
        {label}
      </div>
      <div className="mt-1 text-3xl font-semibold tabular-nums">{value}</div>
      {hint && <div className="mt-0.5 text-xs text-soft">{hint}</div>}
    </div>
  )
}
