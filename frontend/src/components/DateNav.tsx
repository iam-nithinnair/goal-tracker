import { ChevronLeft, ChevronRight } from 'lucide-react'
import { addDays, formatDay, maxISO } from '../lib/dates'
import { Button } from './ui'

/** Day picker for logging. Future days are never selectable. */
export function DateNav({
  date,
  today,
  min,
  onChange,
}: {
  date: string
  today: string
  /** earliest selectable day (e.g. the challenge start); optional */
  min?: string
  onChange: (next: string) => void
}) {
  const earliest = min ? maxISO(min, '0001-01-01') : undefined
  const canPrev = !earliest || date > earliest
  const canNext = date < today
  const isToday = date === today

  return (
    <div className="flex flex-wrap items-center gap-2">
      <Button
        variant="secondary"
        className="size-10 !p-0"
        aria-label="Previous day"
        disabled={!canPrev}
        onClick={() => onChange(addDays(date, -1))}
      >
        <ChevronLeft className="size-4" aria-hidden />
      </Button>

      <label className="relative">
        <span className="sr-only">Pick a day</span>
        <input
          type="date"
          className="field !w-auto min-w-[10.5rem] !py-2"
          value={date}
          min={earliest}
          max={today}
          onChange={(e) => e.target.value && onChange(e.target.value)}
        />
      </label>

      <Button
        variant="secondary"
        className="size-10 !p-0"
        aria-label="Next day"
        disabled={!canNext}
        onClick={() => onChange(addDays(date, 1))}
      >
        <ChevronRight className="size-4" aria-hidden />
      </Button>

      <div className="ml-1 text-sm text-soft">
        {isToday ? <span className="font-medium text-ink">Today</span> : formatDay(date)}
      </div>

      {!isToday && (
        <Button variant="ghost" className="ml-auto !py-2" onClick={() => onChange(today)}>
          Jump to today
        </Button>
      )}
    </div>
  )
}
