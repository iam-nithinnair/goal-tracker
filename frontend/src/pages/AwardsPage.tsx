import clsx from 'clsx'
import { Lock, Star } from 'lucide-react'
import { useState } from 'react'
import { EmptyState, ErrorNote, Spinner } from '../components/ui'
import { errorMessage } from '../lib/api'
import { formatDay } from '../lib/dates'
import { useBadges, useChallenges, useStars } from '../lib/queries'
import type { BadgeStatus } from '../lib/types'

export function AwardsPage() {
  const [challengeId, setChallengeId] = useState('')
  const challenges = useChallenges()
  const badges = useBadges(challengeId || undefined)
  const stars = useStars()

  const earned = (badges.data ?? []).filter((b) => b.earned_on)
  const locked = (badges.data ?? []).filter((b) => !b.earned_on)
  const shown = challengeId
    ? (stars.data?.by_challenge.find((c) => c.challenge_id === challengeId)?.stars ?? 0)
    : (stars.data?.total_stars ?? 0)

  return (
    <div className="grid gap-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold">Awards</h1>
          <p className="mt-1.5 text-sm text-soft">Badges you have earned, and how to earn the rest.</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-2xl font-semibold tabular-nums">
            <Star className="size-5 text-accent-strong" aria-hidden />
            <span aria-label={`${shown} stars`}>{shown}</span>
          </div>
          <label className="text-sm text-soft">
            <span className="sr-only">Filter by challenge</span>
            <select className="field w-auto" value={challengeId} onChange={(e) => setChallengeId(e.target.value)}>
              <option value="">All challenges</option>
              {(challenges.data ?? []).map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </label>
        </div>
      </div>

      {badges.isLoading && <Spinner label="Loading awards" />}
      {badges.isError && <ErrorNote>{errorMessage(badges.error)}</ErrorNote>}

      {badges.data && (
        <>
          <section aria-labelledby="earned-h">
            <h2 id="earned-h" className="mb-3 text-base font-semibold">
              Earned <span className="text-faint">({earned.length})</span>
            </h2>
            {earned.length === 0 ? (
              <EmptyState title="Nothing earned yet" hint="Log a goal to unlock your first badge." />
            ) : (
              <ul className="grid gap-3 sm:grid-cols-2">
                {earned.map((b) => (
                  <BadgeCard key={b.code} badge={b} />
                ))}
              </ul>
            )}
          </section>

          {locked.length > 0 && (
            <section aria-labelledby="locked-h">
              <h2 id="locked-h" className="mb-3 text-base font-semibold">
                Still to earn <span className="text-faint">({locked.length})</span>
              </h2>
              <ul className="grid gap-3 sm:grid-cols-2">
                {locked.map((b) => (
                  <BadgeCard key={b.code} badge={b} />
                ))}
              </ul>
            </section>
          )}
        </>
      )}
    </div>
  )
}

function BadgeCard({ badge }: { badge: BadgeStatus }) {
  const unlocked = badge.earned_on !== null
  return (
    <li className={clsx('card flex gap-4 p-4', !unlocked && 'opacity-60')}>
      <span
        className={clsx(
          'grid size-11 shrink-0 place-items-center rounded-full',
          unlocked ? 'bg-accent/15 text-accent-strong' : 'bg-line text-faint',
        )}
      >
        {unlocked ? <Star className="size-5" aria-hidden /> : <Lock className="size-4" aria-hidden />}
      </span>
      <div className="min-w-0">
        <p className="font-medium">
          {badge.name}
          <span className="ml-2 text-xs text-faint">
            {badge.stars} {badge.stars === 1 ? 'star' : 'stars'}
          </span>
        </p>
        <p className="mt-0.5 text-sm text-soft">{badge.description}</p>
        {unlocked ? (
          <p className="mt-1.5 text-xs text-faint">
            {badge.earned
              .map((e) => `${e.challenge_name}, ${formatDay(e.earned_on, { weekday: undefined, year: 'numeric' })}`)
              .join(' · ')}
          </p>
        ) : (
          <p className="mt-1.5 text-xs text-faint">Locked</p>
        )}
      </div>
    </li>
  )
}
