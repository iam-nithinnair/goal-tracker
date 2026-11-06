import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { FriendsPage } from './FriendsPage'

const sendMutate = vi.fn()
const answerMutate = vi.fn()
const removeMutate = vi.fn()
const state = {
  data: { friends: [] as unknown[], incoming: [] as unknown[] },
  sent: undefined as undefined | { message: string },
  shared: [] as unknown[],
}

vi.mock('../lib/sharing', () => ({
  useFriends: () => ({ data: state.data, isLoading: false, isError: false }),
  useSharedWithMe: () => ({ data: state.shared, isLoading: false }),
  useSendFriendRequest: () => ({
    mutate: sendMutate,
    isPending: false,
    isError: false,
    isSuccess: Boolean(state.sent),
    data: state.sent,
  }),
  useAnswerRequest: () => ({ mutate: answerMutate, isPending: false, isError: false }),
  useRemoveFriend: () => ({ mutate: removeMutate, isPending: false }),
}))

const show = () =>
  render(
    <MemoryRouter>
      <FriendsPage />
    </MemoryRouter>,
  )

describe('FriendsPage', () => {
  beforeEach(() => {
    sendMutate.mockReset()
    answerMutate.mockReset()
    removeMutate.mockReset()
    state.data = { friends: [], incoming: [] }
    state.sent = undefined
    state.shared = []
  })

  it('explains how to add a friend when there are none', () => {
    show()
    expect(screen.getByText('No friends yet')).toBeInTheDocument()
    expect(screen.getByText('Nothing has been shared with you yet.')).toBeInTheDocument()
  })

  it('sends a request by email and shows the server\'s neutral answer', () => {
    state.sent = { message: 'If that person has an account, they will see your request.' }
    show()
    fireEvent.change(screen.getByLabelText('Their email'), { target: { value: ' bob@example.com ' } })
    fireEvent.click(screen.getByRole('button', { name: 'Send request' }))
    expect(sendMutate.mock.calls[0][0]).toBe('bob@example.com')
    expect(screen.getByRole('status')).toHaveTextContent('If that person has an account')
  })

  it('accepts and declines incoming requests', () => {
    state.data = { friends: [], incoming: [{ id: 'r1', display_name: 'Bob', created_at: '2026-11-01T00:00:00Z' }] }
    show()
    fireEvent.click(screen.getByRole('button', { name: 'Accept' }))
    expect(answerMutate).toHaveBeenCalledWith({ id: 'r1', accept: true })
    fireEvent.click(screen.getByRole('button', { name: 'Decline' }))
    expect(answerMutate).toHaveBeenLastCalledWith({ id: 'r1', accept: false })
  })

  it('asks before removing a friend', () => {
    state.data = { friends: [{ user_id: 'u1', display_name: 'Bob', since: null }], incoming: [] }
    show()
    fireEvent.click(screen.getByRole('button', { name: 'Remove friend' }))
    expect(removeMutate).not.toHaveBeenCalled() // first click only asks
    expect(screen.getByText(/stops any sharing/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Remove' }))
    expect(removeMutate.mock.calls[0][0]).toBe('u1')
  })

  it('lists what friends shared and links to the read-only view', () => {
    state.shared = [
      {
        challenge_id: 'c9',
        name: 'Winter Arc',
        start_date: '2026-10-06',
        end_date: '2026-12-31',
        owner_display_name: 'Alice',
        shared_at: '2026-11-02T00:00:00Z',
      },
    ]
    show()
    expect(screen.getByRole('link', { name: /Winter Arc/ })).toHaveAttribute('href', '/shared/c9')
  })
})
