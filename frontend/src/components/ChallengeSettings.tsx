import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { errorMessage } from '../lib/api'
import { daysBetween } from '../lib/dates'
import { useDeleteChallenge, useUpdateChallenge } from '../lib/queries'
import type { ChallengeDetail } from '../lib/types'
import { Button, Dialog, ErrorNote, Field, InfoNote } from './ui'

export function ChallengeSettings({ challenge }: { challenge: ChallengeDetail }) {
  const navigate = useNavigate()
  const update = useUpdateChallenge(challenge.id)
  const remove = useDeleteChallenge()

  const [name, setName] = useState(challenge.name)
  const [start, setStart] = useState(challenge.start_date)
  const [end, setEnd] = useState(challenge.end_date)
  const [saved, setSaved] = useState(false)
  const [localError, setLocalError] = useState('')
  const [confirmDelete, setConfirmDelete] = useState(false)

  const days = daysBetween(start, end) + 1
  const dirty = name.trim() !== challenge.name || start !== challenge.start_date || end !== challenge.end_date

  async function save(e: FormEvent) {
    e.preventDefault()
    setSaved(false)
    setLocalError('')
    if (!name.trim()) return setLocalError('Give your challenge a name.')
    if (end < start) return setLocalError('The end date must be on or after the start date.')
    if (days > 366) return setLocalError('A challenge can last at most 366 days.')
    await update
      .mutateAsync({ name: name.trim(), start_date: start, end_date: end })
      .then(() => setSaved(true), () => {})
  }

  const archived = challenge.status === 'archived'

  return (
    <div className="grid max-w-xl gap-8">
      <form onSubmit={save} className="card grid gap-5 p-6" noValidate>
        <h2 className="text-base font-semibold">Details</h2>
        <ErrorNote>{localError || (update.isError ? errorMessage(update.error) : '')}</ErrorNote>
        {saved && !dirty && <InfoNote>Saved.</InfoNote>}
        <Field label="Name">
          <input className="field" maxLength={80} value={name} onChange={(e) => setName(e.target.value)} />
        </Field>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Starts">
            <input className="field" type="date" value={start} onChange={(e) => setStart(e.target.value)} />
          </Field>
          <Field label="Ends">
            <input className="field" type="date" value={end} min={start} onChange={(e) => setEnd(e.target.value)} />
          </Field>
        </div>
        <p className="-mt-2 text-xs text-faint">
          {days > 0 ? `${days} days` : 'End date is before the start'}. Dates can't leave out days you've already
          logged.
        </p>
        <div>
          <Button type="submit" variant="primary" loading={update.isPending} disabled={!dirty}>
            Save changes
          </Button>
        </div>
      </form>

      <section className="card grid gap-3 p-6">
        <h2 className="text-base font-semibold">{archived ? 'Restore' : 'Archive'}</h2>
        <p className="text-sm text-soft">
          {archived
            ? 'Bring this challenge back to your active list.'
            : 'Hide this challenge from your active list. Nothing is deleted and you can restore it any time.'}
        </p>
        <div>
          <Button
            loading={update.isPending}
            onClick={() => update.mutate({ status: archived ? 'active' : 'archived' })}
          >
            {archived ? 'Restore challenge' : 'Archive challenge'}
          </Button>
        </div>
      </section>

      <section className="card grid gap-3 border-no/25 p-6">
        <h2 className="text-base font-semibold text-no">Delete</h2>
        <p className="text-sm text-soft">
          Permanently deletes this challenge, its goals and every day you've logged.
        </p>
        <div>
          <Button variant="danger" onClick={() => setConfirmDelete(true)}>
            Delete challenge
          </Button>
        </div>
      </section>

      <Dialog open={confirmDelete} onClose={() => setConfirmDelete(false)} title="Delete this challenge?">
        <div className="grid gap-4">
          <p className="text-sm text-soft">
            <strong className="text-ink">{challenge.name}</strong> and all of its history will be gone for good. If you
            just want it out of the way, archive it instead.
          </p>
          {remove.isError && <ErrorNote>{errorMessage(remove.error)}</ErrorNote>}
          <div className="flex flex-wrap justify-end gap-2">
            <Button variant="ghost" onClick={() => setConfirmDelete(false)}>
              Cancel
            </Button>
            <Button
              variant="danger"
              loading={remove.isPending}
              onClick={async () => {
                await remove.mutateAsync(challenge.id).then(
                  () => navigate('/challenges', { replace: true }),
                  () => {},
                )
              }}
            >
              Delete forever
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  )
}
