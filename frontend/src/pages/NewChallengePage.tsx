import clsx from 'clsx'
import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Button, ErrorNote, Field, Spinner } from '../components/ui'
import { errorMessage } from '../lib/api'
import { addDays, daysBetween, todayIn } from '../lib/dates'
import { useCreateChallenge, useProfile, useTemplates } from '../lib/queries'

export function NewChallengePage() {
  const navigate = useNavigate()
  const { data: profile } = useProfile()
  const templates = useTemplates()
  const create = useCreateChallenge()
  const today = todayIn(profile?.timezone ?? Intl.DateTimeFormat().resolvedOptions().timeZone)

  // 'blank' or a template id
  const [source, setSource] = useState<string>('blank')
  const [name, setName] = useState('')
  const [start, setStart] = useState(today)
  const [end, setEnd] = useState(addDays(today, 29))
  const [goalsText, setGoalsText] = useState('')
  const [clientError, setClientError] = useState('')

  const template = templates.data?.find((t) => t.id === source)
  const days = daysBetween(start, end) + 1

  function pickSource(id: string) {
    setSource(id)
    const t = templates.data?.find((x) => x.id === id)
    if (t) {
      setName(t.name)
      setStart(t.start_date)
      setEnd(t.end_date)
    }
  }

  async function submit(e: FormEvent) {
    e.preventDefault()
    setClientError('')
    if (!name.trim()) return setClientError('Give your challenge a name.')
    if (!start || !end) return setClientError('Pick a start and end date.')
    if (end < start) return setClientError('The end date must be on or after the start date.')
    if (days > 366) return setClientError('A challenge can last at most 366 days.')

    const goals = goalsText
      .split('\n')
      .map((g) => g.trim())
      .filter(Boolean)
    try {
      const created = await create.mutateAsync({
        name: name.trim(),
        start_date: start,
        end_date: end,
        template_id: template?.id,
        goals,
      })
      navigate(`/challenges/${created.id}${created.goals.length ? '' : '?tab=goals'}`, { replace: true })
    } catch {
      /* shown below through create.error */
    }
  }

  return (
    <div className="mx-auto grid max-w-xl gap-6">
      <div>
        <Link to="/challenges" className="text-sm text-soft hover:text-ink">
          ← Challenges
        </Link>
        <h1 className="mt-3 text-3xl font-semibold">New challenge</h1>
      </div>

      <form onSubmit={submit} className="card grid gap-5 p-6" noValidate>
        <ErrorNote>{clientError || (create.isError ? errorMessage(create.error) : '')}</ErrorNote>

        <fieldset>
          <legend className="label">Start from</legend>
          {templates.isLoading ? (
            <Spinner />
          ) : (
            <div className="grid gap-2 sm:grid-cols-2">
              <SourceOption selected={source === 'blank'} onClick={() => pickSource('blank')} title="Blank" hint="Add your own goals" />
              {(templates.data ?? []).map((t) => (
                <SourceOption
                  key={t.id}
                  selected={source === t.id}
                  onClick={() => pickSource(t.id)}
                  title={t.name}
                  hint={`${t.goals.length} ready-made goals`}
                />
              ))}
            </div>
          )}
        </fieldset>

        <Field label="Name">
          <input
            className="field"
            maxLength={80}
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Winter Arc 2026"
          />
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
          {days > 0 ? `${days} day${days === 1 ? '' : 's'}` : 'End date is before the start'}
        </p>

        {template ? (
          <div>
            <span className="label">Goals from the template</span>
            <ul className="flex flex-wrap gap-2">
              {template.goals.map((g) => (
                <li key={g.id} className="rounded-full border border-line bg-raised px-3 py-1 text-xs text-soft">
                  {g.name}
                </li>
              ))}
            </ul>
            <p className="mt-2 text-xs text-faint">You can rename, add, reorder or retire goals after creating.</p>
          </div>
        ) : (
          <Field label="Goals" hint="One per line. You can change them any time.">
            <textarea
              className="field min-h-32 resize-y"
              value={goalsText}
              onChange={(e) => setGoalsText(e.target.value)}
              placeholder={'Wake up at 7\nCold shower\nRead 10 minutes'}
            />
          </Field>
        )}

        <Button type="submit" variant="primary" loading={create.isPending}>
          Create challenge
        </Button>
      </form>
    </div>
  )
}

function SourceOption({
  selected,
  onClick,
  title,
  hint,
}: {
  selected: boolean
  onClick: () => void
  title: string
  hint: string
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={selected}
      className={clsx(
        'rounded-xl border px-4 py-3 text-left transition-colors',
        selected ? 'border-accent bg-accent/10' : 'border-line bg-raised hover:border-line-strong',
      )}
    >
      <span className="block text-sm font-semibold">{title}</span>
      <span className="block text-xs text-soft">{hint}</span>
    </button>
  )
}
