import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { Spinner } from '../components/ui'
import { useAuth } from './AuthProvider'

/** Signed-out visitors are sent to /login and returned to where they were headed afterwards. */
export function ProtectedRoute() {
  const { session, loading, recovering } = useAuth()
  const location = useLocation()

  if (loading) {
    return (
      <div className="grid min-h-dvh place-items-center">
        <Spinner label="Loading" />
      </div>
    )
  }
  if (!session) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  if (recovering && location.pathname !== '/reset-password') {
    return <Navigate to="/reset-password" replace />
  }
  return <Outlet />
}

/** Login/register pages bounce signed-in users to the app. */
export function PublicOnlyRoute() {
  const { session, loading, recovering } = useAuth()
  if (loading) return null
  if (session && !recovering) return <Navigate to="/" replace />
  return <Outlet />
}
