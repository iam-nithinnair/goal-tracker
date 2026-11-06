import { fireEvent, render, screen, within } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { ChallengeDetail, Dashboard } from '../lib/types'
import { DashboardView } from './DashboardView'

const useDashboard = vi.fn()
vi.mock('../lib/queries', () => ({ useDashboard: (...a: unknown[]) => useDashboard(...a) }))

const challenge = { id: 'c1' } as ChallengeDetail

const base: Dashboard = {
  as_of: '2026-10-28',
  streaks: { current: 2, longest: 5, perfect_current: 0, perfect_longest: 0 },
  kpis: {
    total_days: 87,
    days_in: 22,
    days_left: 65,
    overall_completion: 0.533,
    perfect_days: 0,
    goals_completed: 113,
    missed: 99,
    na: 8,
  },
  goals: [
    { goal_id: 'a', name: 'Read 10 min', done: 3, missed: 19, na: 0, completion: 0.136, retired: false },
    { goal_id: 'b', name: 'Cut sugar', done: 18, missed: 4, na: 0, completion: 0.818, retired: false },
    { goal_id: 'c', name: 'Meditate', done: 0, missed: 0, na: 0, completion: null, retired: true },
  ],
  months: [
    { month: '2026-10', days: 22, done: 113, missed: 99, na: 8, completion: 0.533, perfect_days: 0, avg_daily_score: 0.527, best_day: 0.9 },
    { month: '2026-11', days: 0, done: 0, missed: 0, na: 0, completion: null, perfect_days: 0, avg_daily_score: null, best_day: null },
  ],
  goal_months: [
    { goal_id: 'a', month: '2026-10', done: 3, missed: 19, na: 0, completion: 0.136 },
    { goal_id: 'b', month: '2026-10', done: 18, missed: 4, na: 0, completion: 0.818 },
  ],
  weeks: [{ week: 1, from: '2026-10-06', to: '2026-10-12', done: 43, possible: 68, completion: 0.632 }],
  days: [{ date: '2026-10-06', done: 9, missed: 1, na: 0, applicable: 10, pending: 0, score: 0.9 }],
}

const show = (data: Dashboard) => {
  useDashboard.mockReturnValue({ data, isLoading: false, isError: false })
  return render(<DashboardView challenge={challenge} />)
}

describe('DashboardView', () => {
  beforeEach(() => useDashboard.mockReset())

  it('shows the key numbers from the API', () => {
    show(base)
    const kpis = screen.getByRole('region', { name: 'Key numbers' })
    expect(within(kpis).getByText('53%')).toBeInTheDocument()
    expect(within(kpis).getByText('113')).toBeInTheDocument()
    expect(within(kpis).getByText('65')).toBeInTheDocument()
    expect(within(kpis).getByText('best 5')).toBeInTheDocument()
  })

  it('tags a retired goal and shows "-" when there is nothing to score', () => {
    show(base)
    const row = screen.getByText('Meditate').closest('tr')!
    expect(within(row).getByText('retired')).toBeInTheDocument()
    expect(within(row).getByText('-')).toBeInTheDocument()
  })

  it('lists only months that have started, with a total row', () => {
    show(base)
    expect(screen.queryByText('Nov 2026')).not.toBeInTheDocument()
    const total = screen.getAllByText('Total')[0].closest('tr')!
    expect(within(total).getByText('113')).toBeInTheDocument()
    expect(within(total).getByText('53%')).toBeInTheDocument()
  })

  it('sorts the goal table when a heading is clicked', () => {
    show(base)
    const goalNames = () =>
      screen
        .getAllByRole('row')
        .map((r) => r.textContent ?? '')
        .filter((t) => /^(Read 10 min|Cut sugar|Meditate)/.test(t))
        .map((t) => t.split(/\d|-/)[0].replace('retired', ''))
    fireEvent.click(screen.getByRole('button', { name: 'Completion' }))
    expect(goalNames()[0]).toBe('Meditate') // null sorts lowest, ascending first
    fireEvent.click(screen.getByRole('button', { name: /Completion/ }))
    expect(goalNames()[0]).toBe('Cut sugar')
  })

  it('shows the empty state before the first logged day', () => {
    show({ ...base, kpis: { ...base.kpis, days_in: 0 } })
    expect(screen.getByText('Nothing to show yet')).toBeInTheDocument()
  })

  it('shows an error without crashing', () => {
    useDashboard.mockReturnValue({ data: undefined, isLoading: false, isError: true, error: new Error('boom') })
    render(<DashboardView challenge={challenge} />)
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })
})
