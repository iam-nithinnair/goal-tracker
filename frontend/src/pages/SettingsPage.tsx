import { useMemo, useState, type FormEvent } from 'react'
import { Button, ErrorNote, Field, InfoNote, Spinner } from '../components/ui'
import { errorMessage } from '../lib/api'
import { useProfile, useUpdateProfile } from '../lib/queries'
import type { Profile } from '../lib/types'

const SWATCHES = ['#7c8cff', '#4ade80', '#fb7185', '#fbbf24', '#38bdf8', '#c084fc', '#f472b6', '#94a3b8']

export function SettingsPage() {
  const { data: profile, isLoading } = useProfile()
  if (isLoading || !profile) return <Spinner label="Loading profile" />
  return <ProfileForm profile={profile} />
}

function ProfileForm({ profile }: { profile: Profile }) {
  const update = useUpdateProfile()
  const [name, setName] = useState(profile.display_name)
  const [color, setColor] = useState(profile.avatar_color)
  const [timezone, setTimezone] = useState(profile.timezone)
  const [saved, setSaved] = useState(false)

  const zones = useMemo(() => {
    const list = (Intl as unknown as { supportedValuesOf?: (k: string) => string[] }).supportedValuesOf?.('timeZone') ?? []
    return list.includes(timezone) ? list : [timezone, ...list]
  }, [timezone])

  const dirty =
    name.trim() !== profile.display_name || color !== profile.avatar_color || timezone !== profile.timezone

  async function save(e: FormEvent) {
    e.preventDefault()
    setSaved(false)
    await update
      .mutateAsync({ display_name: name.trim(), avatar_color: color, timezone })
      .then(() => setSaved(true), () => {})
  }

  return (
    <div className="mx-auto grid max-w-xl gap-6">
      <div>
        <h1 className="text-3xl font-semibold">Profile</h1>
        <p className="mt-1.5 text-soft">{profile.email}</p>
      </div>

      <form onSubmit={save} className="card grid gap-5 p-6" noValidate>
        {update.isError && <ErrorNote>{errorMessage(update.error)}</ErrorNote>}
        {saved && !dirty && <InfoNote>Saved.</InfoNote>}

        <Field label="Display name" hint="Shown on anything you share with friends.">
          <input className="field" maxLength={50} value={name} onChange={(e) => setName(e.target.value)} />
        </Field>

        <fieldset>
          <legend className="label">Avatar colour</legend>
          <div className="flex flex-wrap gap-2">
            {SWATCHES.map((c) => (
              <button
                key={c}
                type="button"
                aria-label={`Colour ${c}`}
                aria-pressed={color === c}
                onClick={() => setColor(c)}
                className="size-8 rounded-full border-2 transition-transform hover:scale-110"
                style={{ background: c, borderColor: color === c ? '#fff' : 'transparent' }}
              />
            ))}
          </div>
        </fieldset>

        <Field
          label="Timezone"
          hint='This decides when "today" starts, so a late-night check-in lands on the right day.'
        >
          <select className="field" value={timezone} onChange={(e) => setTimezone(e.target.value)}>
            {zones.map((z) => (
              <option key={z} value={z}>
                {z}
              </option>
            ))}
          </select>
        </Field>

        <div>
          <Button type="submit" variant="primary" loading={update.isPending} disabled={!dirty || !name.trim()}>
            Save changes
          </Button>
        </div>
      </form>
    </div>
  )
}
