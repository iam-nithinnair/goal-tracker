import { ArrowRight, Plus } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { DateNav } from '../components/DateNav'
import { DayLog } from '../components/DayLog'
import { Button, EmptyState, Spinner } from '../components/ui'
import { errorMessage } from '../lib/api'
import { formatRange, phaseOf, todayIn, daysBetween, minISO } from '../lib/dates'
import { useChallenge, useChallenges, useProfile } from '../lib/queries'
import type { Challenge } from '../lib/types'

export function HomePage() {
  const { data: profile } = useProfile()
  const challenges = useChallenges()
  const today = todayIn(profile?.timezone ?? Intl.DateTimeFormat().resolvedOptions().timeZone)
  const [picked, setPicked] = useState<string | null>(null)
  const date = picked ?? today

  const active = (challenges.data ?? []).filter((c) => c.status === 'active')
  const running = active.filter((c) => phaseOf(c, today) !== 'upcoming')
  const upcoming = active.filter((c) => phaseOf(c, today) === 'upcoming')

  if (challenges.isLoading) return <Spinner label="Loading" />
  if (challenges.isError) return <p className="text-no">{errorMessage(challenges.error)}</p>

  return (
    <div className="grid gap-8">
      <div>
        <h1 className="text-3xl font-semibold">
          {greeting()}
          {profile?.display_name ? `, ${profile.display_name}` : ''}
        </h1>
        <p className="mt-1.5 text-soft">Check in on your goals. It takes a few taps.</p>
      </div>

      {running.length > 0 && <DateNav date={date} today={today} onChange={setPicked} />}

      {active.length === 0 ? (
        <EmptyState
          title="No active challenge yet"
          hint="Create a challenge, pick your daily goals, and start logging."
          action={
            <Link to="/challenges/new">
              <Button variant="primary">
                <Plus className="size-4" aria-hidden /> New challenge
              </Button>
            </Link>
          }
        />
      ) : (
        <div className="grid gap-5">
          {running.map((c) => (
            <ChallengeDayCard key={c.id} challenge={c} date={date} today={today} />
          ))}
          {upcoming.map((c) => (
            <div key={c.id} className="card flex items-center justify-between gap-4 px-5 py-4">
              <div>
                <h2 className="font-semibold">{c.name}</h2>
                <p className="text-sm text-soft">Starts {formatRange(c.start_date, c.end_date)}</p>
              </div>
              <Link to={`/challenges/${c.id}?tab=goals`} className="text-sm text-accent">
                Review goals
              </Link>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function ChallengeDayCard({
  challenge,
  date,
  today,
}: {
  challenge: Challenge
  date: string
  today: string
}) {
  const detail = useChallenge(challenge.id)
  const finished = phaseOf(challenge, today) === 'finished'
  const total = daysBetween(challenge.start_date, challenge.end_date) + 1
  const dayNumber = Math.max(1, daysBetween(challenge.start_date, minISO(date, challenge.end_date)) + 1)

  return (
    <section className="card p-5 sm:p-6">
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold">{challenge.name}</h2>
          <p className="mt-0.5 text-sm text-soft">
            {finished
              ? `Finished · ${formatRange(challenge.start_date, challenge.end_date)}`
              : `Day ${Math.min(dayNumber, total)} of ${total}`}
          </p>
        </div>
        <Link
          to={`/challenges/${challenge.id}`}
          className="inline-flex items-center gap-1 text-sm text-soft transition-colors hover:text-ink"
        >
          Open <ArrowRight className="size-3.5" aria-hidden />
        </Link>
      </div>
      {detail.isLoading && <Spinner />}
      {detail.isError && <p className="text-sm text-no">{errorMessage(detail.error)}</p>}
      {detail.data && <DayLog challenge={detail.data} date={date} />}
    </section>
  )
}

function greeting(): string {
  const h = new Date().getHours()
  if (h < 5) return 'Still up'
  if (h < 12) return 'Good morning'
  if (h < 18) return 'Good afternoon'
  return 'Good evening'
}
