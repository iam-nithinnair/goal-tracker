import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { ChallengeDetail } from '../lib/types'
import { SharePanel } from './SharePanel'

vi.mock('../lib/queries', () => ({ useProfile: () => ({ data: { display_name: 'Alice' } }) }))

const createMutate = vi.fn()
const revokeMutate = vi.fn()
const toggleMutate = vi.fn()
const state = {
  links: [] as unknown[],
  friends: [] as unknown[],
  shares: [] as unknown[],
}

vi.mock('../lib/sharing', () => ({
  useShareLinks: () => ({ data: state.links, isLoading: false, isError: false }),
  useCreateShareLink: () => ({ mutate: createMutate, isPending: false, isError: false }),
  useRevokeShareLink: () => ({ mutate: revokeMutate, isPending: false }),
  useFriends: () => ({ data: { friends: state.friends, incoming: [] }, isLoading: false, isError: false }),
  useChallengeShares: () => ({ data: state.shares }),
  useToggleShare: () => ({ mutate: toggleMutate, isPending: false, isError: false }),
}))

const challenge = { id: 'c1', name: 'Winter Arc' } as ChallengeDetail
const show = () =>
  render(
    <MemoryRouter>
      <SharePanel challenge={challenge} />
    </MemoryRouter>,
  )

const day = (offset: number) => new Date(Date.now() + offset * 86_400_000).toISOString()

describe('SharePanel', () => {
  beforeEach(() => {
    createMutate.mockReset()
    revokeMutate.mockReset()
    toggleMutate.mockReset()
    state.links = []
    state.friends = []
    state.shares = []
  })

  it('creates a link with the chosen scope and expiry, then shows it once with a copy button', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined)
    Object.assign(navigator, { clipboard: { writeText } })
    createMutate.mockImplementation((_v, opts) =>
      opts.onSuccess({ id: 'l1', scope: 'dashboard', token: 'tok123', path: '/s/tok123' }),
    )
    show()

    fireEvent.click(screen.getByLabelText(/Full dashboard/))
    fireEvent.change(screen.getByLabelText('Expires'), { target: { value: '7' } })
    fireEvent.click(screen.getByRole('button', { name: 'Create link' }))

    const sent = createMutate.mock.calls[0][0]
    expect(sent.scope).toBe('dashboard')
    expect(new Date(sent.expires_at).getTime()).toBeGreaterThan(Date.now() + 6 * 86_400_000)

    expect(screen.getByLabelText('Share link')).toHaveValue(`${window.location.origin}/s/tok123`)
    expect(screen.getByText(/not shown again/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Copy link' }))
    await waitFor(() => expect(writeText).toHaveBeenCalledWith(`${window.location.origin}/s/tok123`))
    expect(await screen.findByText('Copied')).toBeInTheDocument()
  })

  it('"never" sends no expiry', () => {
    show()
    fireEvent.click(screen.getByRole('button', { name: 'Create link' }))
    expect(createMutate.mock.calls[0][0]).toEqual({ scope: 'achievements' })
  })

  it('lets you revoke an active link but not an expired or revoked one', () => {
    state.links = [
      { id: 'a', scope: 'dashboard', created_at: day(-1), expires_at: null, revoked_at: null },
      { id: 'b', scope: 'achievements', created_at: day(-9), expires_at: day(-2), revoked_at: null },
      { id: 'c', scope: 'achievements', created_at: day(-9), expires_at: null, revoked_at: day(-3) },
    ]
    show()
    const items = screen.getAllByRole('listitem').filter((li) => li.textContent?.includes('made'))
    expect(items).toHaveLength(3)
    expect(within(items[0]).getByRole('button', { name: 'Revoke' })).toBeInTheDocument()
    expect(within(items[1]).queryByRole('button')).not.toBeInTheDocument()
    expect(items[1]).toHaveTextContent('expired')
    expect(items[2]).toHaveTextContent('revoked')

    fireEvent.click(within(items[0]).getByRole('button', { name: 'Revoke' }))
    expect(revokeMutate).toHaveBeenCalledWith('a')
  })

  it('shares with a friend by ticking their box, and unshares by unticking', () => {
    state.friends = [{ user_id: 'u1', display_name: 'Bob', since: null }]
    state.shares = [{ friend_id: 'u1', display_name: 'Bob' }]
    show()
    const box = screen.getByRole('checkbox', { name: 'Share with Bob' })
    expect(box).toBeChecked()
    fireEvent.click(box)
    expect(toggleMutate).toHaveBeenCalledWith({ friendId: 'u1', share: false })
  })

  it('says which name shared pages will show, and links to where to change it', () => {
    show()
    expect(screen.getByText('Alice')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Change it in Settings' })).toHaveAttribute('href', '/settings')
  })

  it('points to the friends page when there are none', () => {
    show()
    expect(screen.getByRole('link', { name: 'Add one' })).toHaveAttribute('href', '/friends')
  })
})
