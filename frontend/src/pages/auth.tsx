import { useState, type FormEvent, type ReactNode } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { supabase, supabaseConfigured } from '../lib/supabase'
import { Button, ErrorNote, Field, InfoNote, Logo } from '../components/ui'

function Shell({ title, subtitle, children }: { title: string; subtitle: string; children: ReactNode }) {
  return (
    <div className="mx-auto grid min-h-dvh w-full max-w-md content-center gap-8 px-5 py-10">
      <div className="flex flex-col items-center gap-6 text-center">
        <Logo className="text-lg" />
        <div>
          <h1 className="text-2xl font-semibold">{title}</h1>
          <p className="mt-1.5 text-sm text-soft">{subtitle}</p>
        </div>
      </div>
      <div className="card p-6 sm:p-7">{children}</div>
    </div>
  )
}

function ConfigWarning() {
  if (supabaseConfigured) return null
  return (
    <ErrorNote>
      Supabase isn't configured. Copy <code>frontend/.env.example</code> to <code>.env.local</code>{' '}
      and fill in the URL and anon key.
    </ErrorNote>
  )
}

function friendly(message: string): string {
  const m = message.toLowerCase()
  if (m.includes('invalid login')) return 'Incorrect email or password.'
  if (m.includes('email not confirmed')) return 'Please confirm your email first, then log in.'
  if (m.includes('rate limit') || m.includes('too many')) return 'Too many attempts. Please wait a moment.'
  return message
}

/* ------------------------------------------------------------------ login */
export function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const from = (location.state as { from?: string } | null)?.from ?? '/'
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setBusy(true)
    const { error: err } = await supabase.auth.signInWithPassword({ email: email.trim(), password })
    setBusy(false)
    if (err) return setError(friendly(err.message))
    navigate(from, { replace: true })
  }

  return (
    <Shell title="Welcome back" subtitle="Log in to check in on your challenges.">
      <form onSubmit={submit} className="grid gap-4" noValidate>
        <ConfigWarning />
        <ErrorNote>{error}</ErrorNote>
        <Field label="Email">
          <input
            className="field"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
          />
        </Field>
        <Field label="Password">
          <input
            className="field"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </Field>
        <Button type="submit" variant="primary" loading={busy} disabled={!email || !password}>
          Log in
        </Button>
        <div className="flex justify-between text-sm">
          <Link to="/forgot-password" className="text-soft hover:text-ink">
            Forgot password?
          </Link>
          <Link to="/register" className="text-accent hover:text-accent-strong">
            Create account
          </Link>
        </div>
      </form>
    </Shell>
  )
}

/* ------------------------------------------------------------------ register */
export function RegisterPage() {
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(e: FormEvent) {
    e.preventDefault()
    setError('')
    if (password.length < 8) return setError('Use at least 8 characters for your password.')
    setBusy(true)
    const { data, error: err } = await supabase.auth.signUp({
      email: email.trim(),
      password,
      options: { data: { display_name: name.trim() || undefined } },
    })
    setBusy(false)
    if (err) return setError(friendly(err.message))
    if (data.session) navigate('/', { replace: true })
    else setNotice('Check your inbox to confirm your email, then log in.')
  }

  return (
    <Shell title="Create your account" subtitle="Start a challenge and make it stick.">
      <form onSubmit={submit} className="grid gap-4" noValidate>
        <ConfigWarning />
        <ErrorNote>{error}</ErrorNote>
        {notice && <InfoNote>{notice}</InfoNote>}
        <Field label="Display name" hint="Shown on anything you share.">
          <input
            className="field"
            maxLength={50}
            autoComplete="nickname"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Your name"
          />
        </Field>
        <Field label="Email">
          <input
            className="field"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
          />
        </Field>
        <Field label="Password" hint="At least 8 characters.">
          <input
            className="field"
            type="password"
            autoComplete="new-password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </Field>
        <Button type="submit" variant="primary" loading={busy} disabled={!email || !password}>
          Create account
        </Button>
        <p className="text-center text-sm text-soft">
          Already have an account?{' '}
          <Link to="/login" className="text-accent hover:text-accent-strong">
            Log in
          </Link>
        </p>
      </form>
    </Shell>
  )
}

/* ------------------------------------------------------------------ forgot password */
export function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setBusy(true)
    const { error: err } = await supabase.auth.resetPasswordForEmail(email.trim(), {
      redirectTo: `${window.location.origin}/reset-password`,
    })
    setBusy(false)
    // Same answer whether or not the address has an account (no account enumeration).
    if (err && !err.message.toLowerCase().includes('not found')) return setError(friendly(err.message))
    setSent(true)
  }

  return (
    <Shell title="Reset your password" subtitle="We'll email you a link to choose a new one.">
      {sent ? (
        <div className="grid gap-4">
          <InfoNote>If that email has an account, a reset link is on its way.</InfoNote>
          <Link to="/login" className="text-center text-sm text-accent hover:text-accent-strong">
            Back to log in
          </Link>
        </div>
      ) : (
        <form onSubmit={submit} className="grid gap-4" noValidate>
          <ErrorNote>{error}</ErrorNote>
          <Field label="Email">
            <input
              className="field"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
            />
          </Field>
          <Button type="submit" variant="primary" loading={busy} disabled={!email}>
            Send reset link
          </Button>
          <Link to="/login" className="text-center text-sm text-soft hover:text-ink">
            Back to log in
          </Link>
        </form>
      )}
    </Shell>
  )
}

/* ------------------------------------------------------------------ set a new password */
export function ResetPasswordPage() {
  const navigate = useNavigate()
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(e: FormEvent) {
    e.preventDefault()
    setError('')
    if (password.length < 8) return setError('Use at least 8 characters.')
    if (password !== confirm) return setError("The two passwords don't match.")
    setBusy(true)
    const { error: err } = await supabase.auth.updateUser({ password })
    setBusy(false)
    if (err) return setError(friendly(err.message))
    navigate('/', { replace: true })
  }

  return (
    <Shell title="Choose a new password" subtitle="Then you're back in.">
      <form onSubmit={submit} className="grid gap-4" noValidate>
        <ErrorNote>{error}</ErrorNote>
        <Field label="New password" hint="At least 8 characters.">
          <input
            className="field"
            type="password"
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </Field>
        <Field label="Confirm password">
          <input
            className="field"
            type="password"
            autoComplete="new-password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
          />
        </Field>
        <Button type="submit" variant="primary" loading={busy} disabled={!password || !confirm}>
          Update password
        </Button>
      </form>
    </Shell>
  )
}
