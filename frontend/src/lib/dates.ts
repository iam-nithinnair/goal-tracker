/** Dates are plain 'YYYY-MM-DD' strings everywhere (never timestamps), like the database. */

export function toISO(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

/** Parse 'YYYY-MM-DD' as a local calendar date (no timezone shifting). */
export function parseISO(s: string): Date {
  const [y, m, d] = s.split('-').map(Number)
  return new Date(y, m - 1, d)
}

/** Today's date in a given IANA timezone, as 'YYYY-MM-DD'. */
export function todayIn(timeZone: string, now: Date = new Date()): string {
  try {
    // en-CA formats as YYYY-MM-DD
    return new Intl.DateTimeFormat('en-CA', {
      timeZone,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    }).format(now)
  } catch {
    return toISO(now)
  }
}

export function addDays(iso: string, n: number): string {
  const d = parseISO(iso)
  d.setDate(d.getDate() + n)
  return toISO(d)
}

export function daysBetween(a: string, b: string): number {
  return Math.round((parseISO(b).getTime() - parseISO(a).getTime()) / 86_400_000)
}

export function minISO(a: string, b: string): string {
  return a <= b ? a : b
}

export function maxISO(a: string, b: string): string {
  return a >= b ? a : b
}

/** Every date from start to end inclusive, ascending. */
export function eachDay(start: string, end: string): string[] {
  const out: string[] = []
  for (let d = start; d <= end; d = addDays(d, 1)) out.push(d)
  return out
}

export function formatDay(iso: string, opts: Intl.DateTimeFormatOptions = {}): string {
  return parseISO(iso).toLocaleDateString(undefined, {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    ...opts,
  })
}

export function formatRange(start: string, end: string): string {
  const o: Intl.DateTimeFormatOptions = { day: 'numeric', month: 'short', year: 'numeric' }
  return `${parseISO(start).toLocaleDateString(undefined, o)} – ${parseISO(end).toLocaleDateString(undefined, o)}`
}

export function monthLabel(iso: string): string {
  return parseISO(iso).toLocaleDateString(undefined, { month: 'long', year: 'numeric' })
}

/** A goal counts only between active_from and active_to (inclusive). */
export function goalActiveOn(
  goal: { active_from: string; active_to: string | null },
  day: string,
): boolean {
  return day >= goal.active_from && (goal.active_to === null || day <= goal.active_to)
}

export type ChallengePhase = 'upcoming' | 'running' | 'finished'

export function phaseOf(c: { start_date: string; end_date: string }, today: string): ChallengePhase {
  if (today < c.start_date) return 'upcoming'
  if (today > c.end_date) return 'finished'
  return 'running'
}
