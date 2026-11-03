import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const state: { session: unknown; loading: boolean; recovering: boolean } = {
  session: null,
  loading: false,
  recovering: false,
}
vi.mock('./AuthProvider', () => ({ useAuth: () => state }))

import { ProtectedRoute, PublicOnlyRoute } from './ProtectedRoute'

function app(start: string) {
  return render(
    <MemoryRouter initialEntries={[start]}>
      <Routes>
        <Route element={<PublicOnlyRoute />}>
          <Route path="/login" element={<p>login page</p>} />
        </Route>
        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<p>private home</p>} />
          <Route path="/reset-password" element={<p>reset page</p>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  )
}

describe('route guards', () => {
  beforeEach(() => Object.assign(state, { session: null, loading: false, recovering: false }))

  it('sends signed-out visitors to /login', () => {
    app('/')
    expect(screen.getByText('login page')).toBeInTheDocument()
    expect(screen.queryByText('private home')).not.toBeInTheDocument()
  })

  it('shows a loading state instead of flashing the login page while the session loads', () => {
    state.loading = true
    app('/')
    expect(screen.getByRole('status')).toBeInTheDocument()
    expect(screen.queryByText('login page')).not.toBeInTheDocument()
  })

  it('lets signed-in users in', () => {
    state.session = { access_token: 't' }
    app('/')
    expect(screen.getByText('private home')).toBeInTheDocument()
  })

  it('bounces signed-in users away from /login', () => {
    state.session = { access_token: 't' }
    app('/login')
    expect(screen.getByText('private home')).toBeInTheDocument()
  })

  it('keeps a password-recovery session on the reset page', () => {
    state.session = { access_token: 't' }
    state.recovering = true
    app('/')
    expect(screen.getByText('reset page')).toBeInTheDocument()
  })
})
