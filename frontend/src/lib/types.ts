export type Status = 'yes' | 'no' | 'na'

export interface Profile {
  id: string
  email: string | null
  display_name: string
  avatar_color: string
  timezone: string
  role: string
}

export interface Goal {
  id: string
  challenge_id: string
  name: string
  position: number
  active_from: string
  active_to: string | null
}

export interface Challenge {
  id: string
  name: string
  start_date: string
  end_date: string
  status: 'active' | 'archived'
  is_template: boolean
  created_at?: string
}

export interface ChallengeDetail extends Challenge {
  goals: Goal[]
}

export interface Template {
  id: string
  name: string
  start_date: string
  end_date: string
  goals: Goal[]
}

export interface Entry {
  goal_id: string
  entry_date: string
  status: Status
}

export interface EntryWriteResult {
  entries: Entry[]
  new_badges: string[]
}
