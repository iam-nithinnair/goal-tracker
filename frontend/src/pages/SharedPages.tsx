import { Link, useParams } from 'react-router-dom'
import { SharedSummary } from '../components/SharedSummary'
import { EmptyState, Logo, Spinner } from '../components/ui'
import { usePublicShare, useSharedView } from '../lib/sharing'

/** A friend's challenge, read-only. */
export function SharedPage() {
  const { id } = useParams()
  const { data, isLoading, isError } = useSharedView(id)

  return (
    <div className="grid gap-6">
      <Link to="/friends" className="text-sm text-soft hover:text-ink">
        ← Friends
      </Link>
      {isLoading && <Spinner label="Loading" />}
      {isError && (
        <EmptyState
          title="This challenge isn't shared with you"
          hint="It may have been unshared, or you may no longer be friends."
        />
      )}
      {data && (
        <>
          <p className="rounded-xl border border-line bg-raised/60 px-4 py-3 text-sm text-soft">
            Read-only view. You can look but not change anything.
          </p>
          <SharedSummary view={data} />
        </>
      )}
    </div>
  )
}

/** The logged-out page behind a public link. */
export function PublicSharePage() {
  const { token } = useParams()
  const { data, isLoading, isError } = usePublicShare(token)

  return (
    <div className="mx-auto min-h-dvh w-full max-w-5xl px-4 sm:px-6">
      <header className="flex h-16 items-center justify-between">
        <Logo />
        <Link to="/register" className="text-sm text-accent">
          Track your own goals →
        </Link>
      </header>
      <main className="py-8 sm:py-10">
        {isLoading && <Spinner label="Loading" />}
        {isError && (
          <EmptyState
            title="This link isn't available"
            hint="It may have been switched off or expired. Ask the owner for a new one."
          />
        )}
        {data && <SharedSummary view={data} />}
      </main>
    </div>
  )
}
