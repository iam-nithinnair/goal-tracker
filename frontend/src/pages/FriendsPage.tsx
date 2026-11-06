import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Button, EmptyState, ErrorNote, Field, InfoNote, Spinner } from '../components/ui'
import { errorMessage } from '../lib/api'
import { formatRange } from '../lib/dates'
import {
  useAnswerRequest,
  useFriends,
  useRemoveFriend,
  useSendFriendRequest,
  useSharedWithMe,
} from '../lib/sharing'

export function FriendsPage() {
  const friends = useFriends()
  const shared = useSharedWithMe()
  const answer = useAnswerRequest()
  const remove = useRemoveFriend()
  const [confirming, setConfirming] = useState<string | null>(null)

  return (
    <div className="grid gap-8">
      <div>
        <h1 className="text-3xl font-semibold">Friends</h1>
        <p className="mt-1.5 text-sm text-soft">Add friends to share a challenge and cheer each other on.</p>
      </div>

      <AddFriend />

      {friends.isLoading && <Spinner label="Loading friends" />}
      {friends.isError && <ErrorNote>{errorMessage(friends.error)}</ErrorNote>}
      <ErrorNote>{answer.isError ? errorMessage(answer.error) : ''}</ErrorNote>

      {friends.data && friends.data.incoming.length > 0 && (
        <section aria-labelledby="req-h" className="card p-5 sm:p-6">
          <h2 id="req-h" className="mb-3 text-base font-semibold">
            Requests <span className="text-faint">({friends.data.incoming.length})</span>
          </h2>
          <ul className="grid gap-2">
            {friends.data.incoming.map((r) => (
              <li key={r.id} className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-line px-3.5 py-2.5">
                <span className="text-sm">{r.display_name} wants to be friends</span>
                <span className="flex gap-2">
                  <Button
                    variant="primary"
                    className="px-3 py-1.5"
                    disabled={answer.isPending}
                    onClick={() => answer.mutate({ id: r.id, accept: true })}
                  >
                    Accept
                  </Button>
                  <Button
                    className="px-3 py-1.5"
                    disabled={answer.isPending}
                    onClick={() => answer.mutate({ id: r.id, accept: false })}
                  >
                    Decline
                  </Button>
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {friends.data && (
        <section aria-labelledby="friends-h">
          <h2 id="friends-h" className="mb-3 text-base font-semibold">
            Your friends <span className="text-faint">({friends.data.friends.length})</span>
          </h2>
          {friends.data.friends.length === 0 ? (
            <EmptyState
              title="No friends yet"
              hint="Enter a friend's email above. They need an account, and they will see your request here."
            />
          ) : (
            <ul className="grid gap-2">
              {friends.data.friends.map((f) => (
                <li key={f.user_id} className="card flex items-center justify-between gap-3 px-4 py-3">
                  <span className="text-sm font-medium">{f.display_name}</span>
                  {confirming === f.user_id ? (
                    <span className="flex items-center gap-2 text-sm">
                      <span className="text-soft">Also stops any sharing between you.</span>
                      <Button
                        variant="danger"
                        className="px-3 py-1.5"
                        loading={remove.isPending}
                        onClick={() => remove.mutate(f.user_id, { onSettled: () => setConfirming(null) })}
                      >
                        Remove
                      </Button>
                      <Button className="px-3 py-1.5" onClick={() => setConfirming(null)}>
                        Cancel
                      </Button>
                    </span>
                  ) : (
                    <Button variant="ghost" className="px-3 py-1.5" onClick={() => setConfirming(f.user_id)}>
                      Remove friend
                    </Button>
                  )}
                </li>
              ))}
            </ul>
          )}
        </section>
      )}

      <section aria-labelledby="shared-h">
        <h2 id="shared-h" className="mb-3 text-base font-semibold">
          Shared with you
        </h2>
        {shared.isLoading && <Spinner label="Loading" />}
        {shared.data?.length === 0 && (
          <p className="text-sm text-soft">Nothing has been shared with you yet.</p>
        )}
        <ul className="grid gap-2">
          {shared.data?.map((s) => (
            <li key={s.challenge_id}>
              <Link
                to={`/shared/${s.challenge_id}`}
                className="card flex flex-wrap items-center justify-between gap-2 px-4 py-3 transition-colors hover:border-accent"
              >
                <span className="text-sm font-medium">{s.name}</span>
                <span className="text-xs text-soft">
                  {s.owner_display_name} · {formatRange(s.start_date, s.end_date)}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}

function AddFriend() {
  const send = useSendFriendRequest()
  const [email, setEmail] = useState('')

  return (
    <form
      className="card grid gap-3 p-5 sm:p-6"
      noValidate
      onSubmit={(e) => {
        e.preventDefault()
        send.mutate(email.trim(), { onSuccess: () => setEmail('') })
      }}
    >
      <h2 className="text-base font-semibold">Add a friend</h2>
      <ErrorNote>{send.isError ? errorMessage(send.error) : ''}</ErrorNote>
      {send.isSuccess && <InfoNote>{send.data.message}</InfoNote>}
      <Field label="Their email">
        <input
          className="field"
          type="email"
          autoComplete="off"
          placeholder="friend@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
      </Field>
      <div>
        <Button type="submit" variant="primary" loading={send.isPending} disabled={!email.trim()}>
          Send request
        </Button>
      </div>
    </form>
  )
}
