import { act, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { useToasts } from '../lib/toast'
import { ToastProvider } from './Toasts'

const badge = { code: 'FIRST_PERFECT_DAY', name: 'Perfect day', description: 'Every goal done.', stars: 2 }

function Unlock({ times = 1 }: { times?: number }) {
  const { push } = useToasts()
  return (
    <button type="button" onClick={() => Array.from({ length: times }).forEach(() => push(badge))}>
      unlock
    </button>
  )
}

describe('ToastProvider', () => {
  beforeEach(() => vi.useFakeTimers())
  afterEach(() => vi.useRealTimers())

  it('announces an unlock in a polite live region, with its stars', () => {
    render(
      <ToastProvider>
        <Unlock />
      </ToastProvider>,
    )
    fireEvent.click(screen.getByText('unlock'))
    const region = screen.getByRole('status')
    expect(region).toHaveAttribute('aria-live', 'polite')
    expect(region).toHaveTextContent('Unlocked: Perfect day')
    expect(region).toHaveTextContent('+2 stars')
  })

  it('can be dismissed', () => {
    render(
      <ToastProvider>
        <Unlock />
      </ToastProvider>,
    )
    fireEvent.click(screen.getByText('unlock'))
    fireEvent.click(screen.getByRole('button', { name: 'Dismiss Perfect day' }))
    expect(screen.queryByText(/Unlocked/)).not.toBeInTheDocument()
  })

  it('goes away on its own', () => {
    render(
      <ToastProvider>
        <Unlock />
      </ToastProvider>,
    )
    fireEvent.click(screen.getByText('unlock'))
    expect(screen.getByText(/Unlocked/)).toBeInTheDocument()
    act(() => {
      vi.advanceTimersByTime(7500)
    })
    expect(screen.queryByText(/Unlocked/)).not.toBeInTheDocument()
  })

  it('does nothing without a provider, so isolated components still work', () => {
    render(<Unlock />)
    fireEvent.click(screen.getByText('unlock'))
    expect(screen.queryByText(/Unlocked/)).not.toBeInTheDocument()
  })
})
