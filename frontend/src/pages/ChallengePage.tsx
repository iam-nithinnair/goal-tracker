import clsx from 'clsx'
import { useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { ChallengeSettings } from '../components/ChallengeSettings'
import { DateNav } from '../components/DateNav'
import { DayLog } from '../components/DayLog'
import { GoalsManager } from '../components/GoalsManager'
import { GridView } from '../components/GridView'
import { EmptyState, Spinner } from '../components/ui'
import { ApiError, errorMessage } from '../lib/api'
import { daysBetween, formatRange, minISO, phaseOf, todayIn } from '../lib/dates'
import { useChallenge, useProfile } from '../lib/queries'

const TABS = [
  { id: 'log', label: 'Log' },
  { id: 'grid', label: 'Grid' },
  { id: 'goals', label: 'Goals' },
  { id: 'settings', label: 'Settings' },
] as const
type TabId = (typeof TABS)[number]['id']

export function ChallengePage() {
  const { id } = useParams()
  const [params, setParams] = useSearchParams()
  const { data: profile } = useProfile()
  const { data: challenge, isLoading, isError, error } = useChallenge(id)
  const [picked, setPicked] = useState<string | null>(null)

  const today = todayIn(profile?.timezone ?? Intl.DateTimeFormat().resolvedOptions().timeZone)
  const tab = (TABS.find((t) => t.id === params.get('tab'))?.id ?? 'log') as TabId

  if (isLoading) return <Spinner label="Loading challenge" />
  if (isError || !challenge) {
    const missing = error instanceof ApiError && error.status === 404
    return (
      <EmptyState
        title={missing ? "We couldn't find that challenge" : 'Something went wrong'}
        hint={missing ? 'It may have been deleted.' : errorMessage(error)}
        action={
          <Link to="/challenges" className="text-sm text-accent">
            Back to challenges
          </Link>
        }
      />
    )
  }

  const phase = phaseOf(challenge, today)
  const latest = minISO(today, challenge.end_date)
  const date = picked && picked <= latest ? picked : latest
  const totalDays = daysBetween(challenge.start_date, challenge.end_date) + 1

  return (
    <div className="grid gap-7">
      <div>
        <Link to="/challenges" className="text-sm text-soft hover:text-ink">
          ← Challenges
        </Link>
        <div className="mt-3 flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="text-3xl font-semibold">{challenge.name}</h1>
            <p className="mt-1.5 text-sm text-soft">
              {formatRange(challenge.start_date, challenge.end_date)} · {totalDays} days
              {challenge.status === 'archived' && ' · Archived'}
              {phase === 'upcoming' && ' · Not started'}
              {phase === 'finished' && ' · Finished'}
            </p>
          </div>
        </div>
      </div>

      <nav aria-label="Challenge sections" className="-mx-1 flex gap-1 overflow-x-auto overflow-y-hidden border-b border-line px-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setParams(t.id === 'log' ? {} : { tab: t.id }, { replace: true })}
            aria-current={tab === t.id ? 'page' : undefined}
            className={clsx(
              '-mb-px border-b-2 px-4 py-2.5 text-sm font-medium transition-colors',
              tab === t.id
                ? 'border-accent text-ink'
                : 'border-transparent text-soft hover:text-ink',
            )}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {tab === 'log' && (
        <section className="grid gap-5">
          {phase === 'upcoming' ? (
            <p className="rounded-xl border border-line bg-raised/60 px-4 py-3 text-sm text-soft">
              This challenge starts on {challenge.start_date}. You can set up goals now and start logging then.
            </p>
          ) : (
            <>
              <DateNav date={date} today={latest} min={challenge.start_date} onChange={setPicked} />
              <div className="card p-5 sm:p-6">
                <DayLog challenge={challenge} date={date} />
              </div>
            </>
          )}
        </section>
      )}
      {tab === 'grid' && <GridView challenge={challenge} today={today} />}
      {tab === 'goals' && <GoalsManager challenge={challenge} today={today} />}
      {tab === 'settings' && (
        <ChallengeSettings
          key={`${challenge.name}|${challenge.start_date}|${challenge.end_date}`}
          challenge={challenge}
        />
      )}
    </div>
  )
}
