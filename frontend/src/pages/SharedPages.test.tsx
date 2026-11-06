import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { SharedView } from '../lib/types'
import { PublicSharePage, SharedPage } from './SharedPages'

const publicShare = vi.fn()
const sharedView = vi.fn()
vi.mock('../lib/sharing', () => ({
  usePublicShare: (...a: unknown[]) => publicShare(...a),
  useSharedView: (...a: unknown[]) => sharedView(...a),
}))

const view: SharedView = {
  display_name: 'Alice',
  challenge_name: 'Winter Arc',
  start_date: '2026-10-06',
  end_date: '2026-12-31',
  completion: 0.53,
  streaks: { current: 3, longest: 6, perfect_current: 0, perfect_longest: 1 },
  stars: 5,
  badges: [{ code: 'FIRST_LOG', name: 'First check-in', stars: 1, earned_on: '2026-10-06' }],
  dashboard: null,
}

const at = (path: string, route: string, el: React.ReactNode) =>
  render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path={route} element={el} />
      </Routes>
    </MemoryRouter>,
  )

describe('PublicSharePage', () => {
  beforeEach(() => {
    publicShare.mockReset()
    sharedView.mockReset()
  })

  it('shows the owner, completion, streak, stars and badges without any login', () => {
    publicShare.mockReturnValue({ data: view, isLoading: false, isError: false })
    at('/s/tok', '/s/:token', <PublicSharePage />)
    expect(publicShare).toHaveBeenCalledWith('tok')
    expect(screen.getByText("Alice's challenge")).toBeInTheDocument()
    expect(screen.getByText('Winter Arc')).toBeInTheDocument()
    const tiles = screen.getByRole('region', { name: 'Highlights' })
    expect(tiles).toHaveTextContent('53%')
    expect(tiles).toHaveTextContent('best 6')
    expect(tiles).toHaveTextContent('5')
    expect(screen.getByText('First check-in')).toBeInTheDocument()
    expect(screen.queryByText('By goal')).not.toBeInTheDocument() // achievements scope: no tables
  })

  it('one generic message for unknown, revoked and expired links', () => {
    publicShare.mockReturnValue({ data: undefined, isLoading: false, isError: true })
    at('/s/gone', '/s/:token', <PublicSharePage />)
    expect(screen.getByText("This link isn't available")).toBeInTheDocument()
    expect(screen.getByText(/switched off or expired/)).toBeInTheDocument()
  })

  it('offers a way to start your own', () => {
    publicShare.mockReturnValue({ data: view, isLoading: false, isError: false })
    at('/s/tok', '/s/:token', <PublicSharePage />)
    expect(screen.getByRole('link', { name: /Track your own goals/ })).toHaveAttribute('href', '/register')
  })
})

describe('SharedPage (a friend)', () => {
  beforeEach(() => sharedView.mockReset())

  it('is labelled read-only and has no edit controls', () => {
    sharedView.mockReturnValue({ data: view, isLoading: false, isError: false })
    at('/shared/c1', '/shared/:id', <SharedPage />)
    expect(sharedView).toHaveBeenCalledWith('c1')
    expect(screen.getByText(/Read-only view/)).toBeInTheDocument()
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('explains when the challenge is no longer shared', () => {
    sharedView.mockReturnValue({ data: undefined, isLoading: false, isError: true })
    at('/shared/c1', '/shared/:id', <SharedPage />)
    expect(screen.getByText("This challenge isn't shared with you")).toBeInTheDocument()
  })
})
