import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './auth/AuthProvider'
import { ProtectedRoute, PublicOnlyRoute } from './auth/ProtectedRoute'
import { AppLayout } from './components/AppLayout'
import { ToastProvider } from './components/Toasts'
import { ApiError } from './lib/api'
import { AwardsPage } from './pages/AwardsPage'
import { ChallengePage } from './pages/ChallengePage'
import { ChallengesPage } from './pages/ChallengesPage'
import { FriendsPage } from './pages/FriendsPage'
import { HomePage } from './pages/HomePage'
import { NewChallengePage } from './pages/NewChallengePage'
import { SettingsPage } from './pages/SettingsPage'
import { PublicSharePage, SharedPage } from './pages/SharedPages'
import { ForgotPasswordPage, LoginPage, RegisterPage, ResetPasswordPage } from './pages/auth'

export function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 15_000,
        refetchOnWindowFocus: false,
        retry: (count, err) => {
          // never retry client errors (bad request, not found, unauthorised)
          if (err instanceof ApiError && err.status >= 400 && err.status < 500) return false
          return count < 2
        },
      },
    },
  })
}

const queryClient = makeQueryClient()

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<PublicOnlyRoute />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      </Route>

      {/* a public link opens for anyone, signed in or not */}
      <Route path="/s/:token" element={<PublicSharePage />} />

      <Route element={<ProtectedRoute />}>
        {/* reached through the emailed recovery link, which signs the user in */}
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        <Route element={<AppLayout />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/challenges" element={<ChallengesPage />} />
          <Route path="/challenges/new" element={<NewChallengePage />} />
          <Route path="/challenges/:id" element={<ChallengePage />} />
          <Route path="/awards" element={<AwardsPage />} />
          <Route path="/friends" element={<FriendsPage />} />
          <Route path="/shared/:id" element={<SharedPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <ToastProvider>
            <AppRoutes />
          </ToastProvider>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
