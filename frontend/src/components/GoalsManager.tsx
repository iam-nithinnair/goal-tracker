import { ArrowDown, ArrowUp, Archive, Pencil, Plus, Trash2 } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { errorMessage } from '../lib/api'
import { formatDay, maxISO, minISO } from '../lib/dates'
import {
  useAddGoal,
  useDeleteGoal,
  useRenameGoal,
  useReorderGoals,
  useRetireGoal,
} from '../lib/queries'
import type { ChallengeDetail, Goal } from '../lib/types'
import { Button, Dialog, ErrorNote } from './ui'

export function GoalsManager({ challenge, today }: { challenge: ChallengeDetail; today: string }) {
  const add = useAddGoal(challenge.id)
  const rename = useRenameGoal(challenge.id)
  const reorder = useReorderGoals(challenge.id)
  const retire = useRetireGoal(challenge.id)
  const remove = useDeleteGoal(challenge.id)

  const [newName, setNewName] = useState('')
  const [editing, setEditing] = useState<string | null>(null)
  const [draft, setDraft] = useState('')
  const [retiring, setRetiring] = useState<Goal | null>(null)
  const [retireOn, setRetireOn] = useState('')
  const [deleting, setDeleting] = useState<Goal | null>(null)

  const goals = challenge.goals
  const firstError = [add, rename, reorder, retire, remove].find((m) => m.isError)

  async function submitNew(e: FormEvent) {
    e.preventDefault()
    const name = newName.trim()
    if (!name) return
    await add.mutateAsync(name).then(() => setNewName(''), () => {})
  }

  function move(index: number, delta: -1 | 1) {
    const ids = goals.map((g) => g.id)
    const target = index + delta
    if (target < 0 || target >= ids.length) return
    ;[ids[index], ids[target]] = [ids[target], ids[index]]
    reorder.mutate(ids)
  }

  function startRename(g: Goal) {
    setEditing(g.id)
    setDraft(g.name)
  }

  async function saveRename(g: Goal) {
    const name = draft.trim()
    setEditing(null)
    if (name && name !== g.name) await rename.mutateAsync({ id: g.id, name }).catch(() => {})
  }

  function openRetire(g: Goal) {
    setRetiring(g)
    // default: the last day the goal counted is yesterday; keep within its window
    const yesterday = new Date(`${today}T00:00:00`)
    yesterday.setDate(yesterday.getDate() - 1)
    const y = `${yesterday.getFullYear()}-${String(yesterday.getMonth() + 1).padStart(2, '0')}-${String(yesterday.getDate()).padStart(2, '0')}`
    setRetireOn(minISO(maxISO(y, g.active_from), challenge.end_date))
  }

  return (
    <div className="grid gap-5">
      {firstError && <ErrorNote>{errorMessage(firstError.error)}</ErrorNote>}

      <form onSubmit={submitNew} className="flex gap-2">
        <label className="flex-1">
          <span className="sr-only">New goal name</span>
          <input
            className="field"
            maxLength={80}
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="Add a goal, e.g. Read 10 minutes"
          />
        </label>
        <Button type="submit" variant="primary" loading={add.isPending} disabled={!newName.trim()}>
          <Plus className="size-4" aria-hidden /> Add
        </Button>
      </form>

      {goals.length === 0 ? (
        <p className="text-sm text-soft">No goals yet. Add your first one above.</p>
      ) : (
        <ul className="card divide-y divide-line/70">
          {goals.map((g, i) => (
            <li key={g.id} className="flex items-center gap-2 px-4 py-3">
              <div className="min-w-0 flex-1">
                {editing === g.id ? (
                  <input
                    autoFocus
                    className="field !py-1.5"
                    value={draft}
                    maxLength={80}
                    onChange={(e) => setDraft(e.target.value)}
                    onBlur={() => saveRename(g)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') e.currentTarget.blur()
                      if (e.key === 'Escape') setEditing(null)
                    }}
                    aria-label={`Rename ${g.name}`}
                  />
                ) : (
                  <p className="truncate font-medium">{g.name}</p>
                )}
                {g.active_to && (
                  <p className="mt-0.5 text-xs text-warn">
                    Retired. Last counted {formatDay(g.active_to, { year: 'numeric' })}
                  </p>
                )}
              </div>

              <IconButton label={`Move ${g.name} up`} disabled={i === 0} onClick={() => move(i, -1)}>
                <ArrowUp className="size-4" />
              </IconButton>
              <IconButton label={`Move ${g.name} down`} disabled={i === goals.length - 1} onClick={() => move(i, 1)}>
                <ArrowDown className="size-4" />
              </IconButton>
              <IconButton label={`Rename ${g.name}`} onClick={() => startRename(g)}>
                <Pencil className="size-4" />
              </IconButton>
              {!g.active_to && (
                <IconButton label={`Retire ${g.name}`} onClick={() => openRetire(g)}>
                  <Archive className="size-4" />
                </IconButton>
              )}
              <IconButton label={`Delete ${g.name}`} danger onClick={() => setDeleting(g)}>
                <Trash2 className="size-4" />
              </IconButton>
            </li>
          ))}
        </ul>
      )}

      <p className="text-xs text-faint">
        Retiring a goal keeps its history and stops counting it after the date you choose. Deleting removes its
        history too.
      </p>

      {/* retire */}
      <Dialog open={retiring !== null} onClose={() => setRetiring(null)} title="Retire this goal">
        {retiring && (
          <form
            className="grid gap-4"
            onSubmit={async (e) => {
              e.preventDefault()
              await retire.mutateAsync({ id: retiring.id, on: retireOn }).then(
                () => setRetiring(null),
                () => {},
              )
            }}
          >
            <p className="text-sm text-soft">
              <strong className="text-ink">{retiring.name}</strong> stops counting after the last day below. Earlier
              days stay exactly as you logged them.
            </p>
            <label>
              <span className="label">Last day it counts</span>
              <input
                type="date"
                className="field"
                value={retireOn}
                min={retiring.active_from}
                max={challenge.end_date}
                onChange={(e) => setRetireOn(e.target.value)}
              />
            </label>
            <div className="flex justify-end gap-2">
              <Button type="button" variant="ghost" onClick={() => setRetiring(null)}>
                Cancel
              </Button>
              <Button type="submit" variant="primary" loading={retire.isPending}>
                Retire goal
              </Button>
            </div>
          </form>
        )}
      </Dialog>

      {/* delete */}
      <Dialog open={deleting !== null} onClose={() => setDeleting(null)} title="Delete this goal?">
        {deleting && (
          <div className="grid gap-4">
            <p className="text-sm text-soft">
              <strong className="text-ink">{deleting.name}</strong> and every day you logged for it will be removed.
              This can't be undone. Retiring it instead keeps your history.
            </p>
            <div className="flex flex-wrap justify-end gap-2">
              <Button variant="ghost" onClick={() => setDeleting(null)}>
                Cancel
              </Button>
              <Button
                variant="danger"
                loading={remove.isPending}
                onClick={async () => {
                  await remove.mutateAsync(deleting.id).then(
                    () => setDeleting(null),
                    () => {},
                  )
                }}
              >
                Delete goal
              </Button>
            </div>
          </div>
        )}
      </Dialog>
    </div>
  )
}

function IconButton({
  label,
  onClick,
  disabled,
  danger,
  children,
}: {
  label: string
  onClick: () => void
  disabled?: boolean
  danger?: boolean
  children: React.ReactNode
}) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      disabled={disabled}
      onClick={onClick}
      className={`grid size-9 shrink-0 place-items-center rounded-lg transition-colors disabled:cursor-not-allowed disabled:opacity-30 ${
        danger ? 'text-soft hover:bg-no/10 hover:text-no' : 'text-soft hover:bg-white/5 hover:text-ink'
      }`}
    >
      {children}
    </button>
  )
}
