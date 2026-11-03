import clsx from 'clsx'
import { LogOut } from 'lucide-react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthProvider'
import { useProfile } from '../lib/queries'
import { Logo } from './ui'

const links = [
  { to: '/', label: 'Today', end: true },
  { to: '/challenges', label: 'Challenges', end: false },
]

export function AppLayout() {
  const { signOut } = useAuth()
  const { data: profile } = useProfile()
  const navigate = useNavigate()
  const initial = (profile?.display_name ?? '?').trim().charAt(0).toUpperCase()

  return (
    <div className="mx-auto flex min-h-dvh w-full max-w-5xl flex-col px-4 sm:px-6">
      <header className="sticky top-0 z-20 -mx-4 border-b border-line/70 bg-canvas/80 px-4 backdrop-blur-xl sm:-mx-6 sm:px-6">
        <div className="flex h-16 items-center gap-6">
          <NavLink to="/" aria-label="Streak home">
            <Logo />
          </NavLink>

          <nav aria-label="Main" className="hidden items-center gap-1 sm:flex">
            {links.map((l) => (
              <NavItem key={l.to} {...l} />
            ))}
          </nav>

          <div className="ml-auto flex items-center gap-2">
            <NavLink
              to="/settings"
              aria-label="Profile and settings"
              className="grid size-9 place-items-center rounded-full border border-line-strong text-sm font-semibold text-ink transition-colors hover:border-accent"
              style={{ background: `${profile?.avatar_color ?? '#7c8cff'}26` }}
            >
              {initial}
            </NavLink>
            <button
              type="button"
              onClick={async () => {
                await signOut()
                navigate('/login', { replace: true })
              }}
              className="grid size-9 place-items-center rounded-full text-soft transition-colors hover:bg-white/5 hover:text-ink"
              aria-label="Log out"
              title="Log out"
            >
              <LogOut className="size-[1.05rem]" aria-hidden />
            </button>
          </div>
        </div>
        <nav aria-label="Main (mobile)" className="flex gap-1 pb-2 sm:hidden">
          {links.map((l) => (
            <NavItem key={l.to} {...l} />
          ))}
        </nav>
      </header>

      <main className="flex-1 py-8 sm:py-10">
        <Outlet />
      </main>
    </div>
  )
}

function NavItem({ to, label, end }: { to: string; label: string; end: boolean }) {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        clsx(
          'rounded-lg px-3 py-1.5 text-sm font-medium transition-colors',
          isActive ? 'bg-white/[0.07] text-ink' : 'text-soft hover:text-ink',
        )
      }
    >
      {label}
    </NavLink>
  )
}
