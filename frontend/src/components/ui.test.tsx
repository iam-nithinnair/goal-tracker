import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { StatusControl } from './ui'

describe('StatusControl', () => {
  it('offers Yes, No and N/A with text labels (not colour alone)', () => {
    render(<StatusControl label="Cold shower" value={null} onChange={() => {}} />)
    const group = screen.getByRole('group', { name: 'Cold shower' })
    expect(group).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /done/i })).toHaveTextContent('Yes')
    expect(screen.getByRole('button', { name: /missed/i })).toHaveTextContent('No')
    expect(screen.getByRole('button', { name: /not available/i })).toHaveTextContent('N/A')
  })

  it('reports the chosen status', async () => {
    const onChange = vi.fn()
    render(<StatusControl label="Read" value={null} onChange={onChange} />)
    await userEvent.click(screen.getByRole('button', { name: /missed/i }))
    expect(onChange).toHaveBeenCalledWith('no')
  })

  it('marks the selected option and clears it when tapped again', async () => {
    const onChange = vi.fn()
    render(<StatusControl label="Read" value="yes" onChange={onChange} />)
    const yes = screen.getByRole('button', { name: /done/i })
    expect(yes).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: /missed/i })).toHaveAttribute('aria-pressed', 'false')
    await userEvent.click(yes)
    expect(onChange).toHaveBeenCalledWith(null)
  })

  it('can be switched between statuses', async () => {
    const onChange = vi.fn()
    render(<StatusControl label="Read" value="yes" onChange={onChange} />)
    await userEvent.click(screen.getByRole('button', { name: /not available/i }))
    expect(onChange).toHaveBeenCalledWith('na')
  })

  it('does nothing when disabled', async () => {
    const onChange = vi.fn()
    render(<StatusControl label="Read" value={null} onChange={onChange} disabled />)
    await userEvent.click(screen.getByRole('button', { name: /done/i }))
    expect(onChange).not.toHaveBeenCalled()
  })
})
