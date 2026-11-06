import { Check, Copy, Link2, Share2 } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { errorMessage } from '../lib/api'
import { formatDay } from '../lib/dates'
import { useProfile } from '../lib/queries'
import {
  useChallengeShares,
  useCreateShareLink,
  useFriends,
  useRevokeShareLink,
  useShareLinks,
  useToggleShare,
} from '../lib/sharing'
import type { ChallengeDetail, ShareLink, ShareLinkCreated, ShareScope } from '../lib/types'
import { Button, ErrorNote, Field, Spinner } from './ui'

const SCOPES: { id: ShareScope; label: string; hint: string }[] = [
  { id: 'achievements', label: 'Achievements only', hint: 'Completion, streak, stars and badges.' },
  { id: 'dashboard', label: 'Full dashboard', hint: 'Everything above plus the goal, month and week tables.' },
]
const EXPIRY = [
  { id: 'never', label: 'Never expires', days: 0 },
  { id: '7', label: 'In 7 days', days: 7 },
  { id: '30', label: 'In 30 days', days: 30 },
]

function linkState(l: ShareLink): 'revoked' | 'expired' | 'active' {
  if (l.revoked_at) return 'revoked'
  if (l.expires_at && new Date(l.expires_at) <= new Date()) return 'expired'
  return 'active'
}

export function SharePanel({ challenge }: { challenge: ChallengeDetail }) {
  const { data: profile } = useProfile()
  return (
    <div className="grid gap-6">
      {profile && (
        <p className="rounded-xl border border-line bg-raised/60 px-4 py-3 text-sm text-soft">
          People you share with see your display name, <strong className="text-ink">{profile.display_name}</strong>.{' '}
          <Link to="/settings" className="text-accent">
            Change it in Settings
          </Link>{' '}
          if you'd rather not show that.
        </p>
      )}
      <PublicLinks challengeId={challenge.id} challengeName={challenge.name} />
      <WithFriends challengeId={challenge.id} />
    </div>
  )
}

// ---------------------------------------------------------------- public links
function PublicLinks({ challengeId, challengeName }: { challengeId: string; challengeName: string }) {
  const links = useShareLinks(challengeId)
  const create = useCreateShareLink(challengeId)
  const revoke = useRevokeShareLink(challengeId)
  const [scope, setScope] = useState<ShareScope>('achievements')
  const [expiry, setExpiry] = useState('never')
  const [fresh, setFresh] = useState<ShareLinkCreated | null>(null)

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    const days = EXPIRY.find((x) => x.id === expiry)?.days ?? 0
    create.mutate(
      { scope, ...(days ? { expires_at: new Date(Date.now() + days * 86_400_000).toISOString() } : {}) },
      { onSuccess: setFresh },
    )
  }

  return (
    <section className="card p-5 sm:p-6" aria-labelledby="public-h">
      <h3 id="public-h" className="flex items-center gap-2 text-base font-semibold">
        <Link2 className="size-4 text-accent" aria-hidden /> Public link
      </h3>
      <p className="mt-1 text-sm text-soft">
        Anyone with the link can see it without an account. They never see your email or notes, and you can
        switch it off at any time.
      </p>

      <form onSubmit={submit} className="mt-4 grid gap-4">
        <ErrorNote>{create.isError ? errorMessage(create.error) : ''}</ErrorNote>
        <fieldset>
          <legend className="label">What to show</legend>
          <div className="grid gap-2 sm:grid-cols-2">
            {SCOPES.map((s) => (
              <label
                key={s.id}
                className={`flex cursor-pointer gap-3 rounded-xl border p-3 text-sm ${
                  scope === s.id ? 'border-accent bg-accent/10' : 'border-line hover:border-line-strong'
                }`}
              >
                <input
                  type="radio"
                  name="scope"
                  className="mt-1"
                  checked={scope === s.id}
                  onChange={() => setScope(s.id)}
                />
                <span>
                  <span className="block font-medium">{s.label}</span>
                  <span className="text-xs text-soft">{s.hint}</span>
                </span>
              </label>
            ))}
          </div>
        </fieldset>
        <Field label="Expires">
          <select className="field" value={expiry} onChange={(e) => setExpiry(e.target.value)}>
            {EXPIRY.map((x) => (
              <option key={x.id} value={x.id}>
                {x.label}
              </option>
            ))}
          </select>
        </Field>
        <div>
          <Button type="submit" variant="primary" loading={create.isPending}>
            Create link
          </Button>
        </div>
      </form>

      {fresh && <FreshLink link={fresh} title={challengeName} />}

      <div className="mt-6">
        <h4 className="mb-2 text-sm font-medium text-soft">Your links</h4>
        {links.isLoading && <Spinner label="Loading links" />}
        {links.isError && <ErrorNote>{errorMessage(links.error)}</ErrorNote>}
        {links.data?.length === 0 && <p className="text-sm text-faint">No links yet.</p>}
        <ul className="grid gap-2">
          {links.data?.map((l) => {
            const state = linkState(l)
            return (
              <li
                key={l.id}
                className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-line px-3.5 py-2.5 text-sm"
              >
                <span className={state === 'active' ? '' : 'text-faint'}>
                  {SCOPES.find((s) => s.id === l.scope)?.label}
                  <span className="ml-2 text-xs text-faint">
                    made {formatDay(l.created_at.slice(0, 10), { weekday: undefined })}
                    {l.expires_at && state === 'active' && `, expires ${formatDay(l.expires_at.slice(0, 10), { weekday: undefined })}`}
                    {state !== 'active' && ` · ${state}`}
                  </span>
                </span>
                {state === 'active' && (
                  <Button
                    variant="danger"
                    className="px-3 py-1.5"
                    loading={revoke.isPending && revoke.variables === l.id}
                    onClick={() => revoke.mutate(l.id)}
                  >
                    Revoke
                  </Button>
                )}
              </li>
            )
          })}
        </ul>
        <p className="mt-2 text-xs text-faint">
          A link is only shown when you create it. If you lose it, revoke it and make a new one.
        </p>
      </div>
    </section>
  )
}

function FreshLink({ link, title }: { link: ShareLinkCreated; title: string }) {
  const url = `${window.location.origin}${link.path}`
  const [copied, setCopied] = useState(false)
  const canShare = typeof navigator !== 'undefined' && 'share' in navigator

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(url)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 2000)
    } catch {
      // clipboard blocked: the field below is selectable so it can still be copied by hand
    }
  }

  return (
    <div className="mt-5 rounded-xl border border-accent/40 bg-accent/5 p-4" role="status">
      <p className="text-sm font-medium">Your link is ready. Copy it now, it is not shown again.</p>
      <div className="mt-3 flex flex-wrap gap-2">
        <input
          readOnly
          aria-label="Share link"
          value={url}
          onFocus={(e) => e.currentTarget.select()}
          className="field min-w-0 flex-1"
        />
        <Button onClick={copy} aria-label="Copy link">
          {copied ? <Check className="size-4" aria-hidden /> : <Copy className="size-4" aria-hidden />}
          {copied ? 'Copied' : 'Copy'}
        </Button>
        {canShare && (
          <Button onClick={() => navigator.share({ title, url }).catch(() => {})}>
            <Share2 className="size-4" aria-hidden /> Share
          </Button>
        )}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------- friends
function WithFriends({ challengeId }: { challengeId: string }) {
  const friends = useFriends()
  const shares = useChallengeShares(challengeId)
  const toggle = useToggleShare(challengeId)
  const sharedWith = new Set((shares.data ?? []).map((s) => s.friend_id))

  return (
    <section className="card p-5 sm:p-6" aria-labelledby="friends-h">
      <h3 id="friends-h" className="text-base font-semibold">
        Share with friends
      </h3>
      <p className="mt-1 text-sm text-soft">
        Friends you pick can open a read-only view with your dashboard and badges. They can't change anything.
      </p>
      <div className="mt-4">
        {friends.isLoading && <Spinner label="Loading friends" />}
        {friends.isError && <ErrorNote>{errorMessage(friends.error)}</ErrorNote>}
        <ErrorNote>{toggle.isError ? errorMessage(toggle.error) : ''}</ErrorNote>
        {friends.data && friends.data.friends.length === 0 && (
          <p className="text-sm text-soft">
            You have no friends yet.{' '}
            <Link to="/friends" className="text-accent">
              Add one
            </Link>{' '}
            to share this challenge.
          </p>
        )}
        <ul className="grid gap-2">
          {friends.data?.friends.map((f) => (
            <li key={f.user_id}>
              <label className="flex cursor-pointer items-center justify-between gap-3 rounded-xl border border-line px-3.5 py-2.5 text-sm">
                <span>{f.display_name}</span>
                <input
                  type="checkbox"
                  aria-label={`Share with ${f.display_name}`}
                  checked={sharedWith.has(f.user_id)}
                  disabled={toggle.isPending}
                  onChange={(e) => toggle.mutate({ friendId: f.user_id, share: e.target.checked })}
                  className="size-4"
                />
              </label>
            </li>
          ))}
        </ul>
      </div>
    </section>
  )
}
