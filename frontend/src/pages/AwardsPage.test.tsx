import { fireEvent, render, screen, within } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AwardsPage } from './AwardsPage'

const useBadges = vi.fn()
vi.mock('../lib/queries', () => ({
  useBadges: (...a: unknown[]) => useBadges(...a),
  useChallenges: () => ({ data: [{ id: 'c1', name: 'Winter Arc' }] }),
  useStars: () => ({
    data: { total_stars: 3, by_challenge: [{ challenge_id: 'c1', name: 'Winter Arc', stars: 3, badges: 2 }] },
  }),
}))

const earned = {
  code: 'FIRST_LOG',
  name: 'First check-in',
  description: 'Log your first goal.',
  stars: 1,
  earned_on: '2026-10-06',
  earned: [{ challenge_id: 'c1', challenge_name: 'Winter Arc', earned_on: '2026-10-06' }],
}
const locked = {
  code: 'STREAK_30',
  name: 'Month of habit',
  description: 'Score 80% or more for 30 days in a row.',
  stars: 10,
  earned_on: null,
  earned: [],
}

describe('AwardsPage', () => {
  beforeEach(() => useBadges.mockReset())

  it('separates earned from locked and says how to earn the locked ones', () => {
    useBadges.mockReturnValue({ data: [earned, locked], isLoading: false, isError: false })
    render(<AwardsPage />)
    const earnedList = screen.getByRole('region', { name: /Earned/ })
    expect(within(earnedList).getByText('First check-in')).toBeInTheDocument()
    expect(within(earnedList).getByText(/Winter Arc, /)).toBeInTheDocument()
    const lockedList = screen.getByRole('region', { name: /Still to earn/ })
    expect(within(lockedList).getByText('Month of habit')).toBeInTheDocument()
    expect(within(lockedList).getByText('Score 80% or more for 30 days in a row.')).toBeInTheDocument()
    expect(within(lockedList).getByText('Locked')).toBeInTheDocument()
  })

  it('shows the total stars and asks for the challenge filter', () => {
    useBadges.mockReturnValue({ data: [earned], isLoading: false, isError: false })
    render(<AwardsPage />)
    expect(screen.getByLabelText('3 stars')).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('Filter by challenge'), { target: { value: 'c1' } })
    expect(useBadges).toHaveBeenLastCalledWith('c1')
  })

  it('has an empty state before anything is earned', () => {
    useBadges.mockReturnValue({ data: [locked], isLoading: false, isError: false })
    render(<AwardsPage />)
    expect(screen.getByText('Nothing earned yet')).toBeInTheDocument()
  })
})
