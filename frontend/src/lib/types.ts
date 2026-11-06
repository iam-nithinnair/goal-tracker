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

export interface Badge {
  code: string
  name: string
  description: string
  stars: number
}

export interface EntryWriteResult {
  entries: Entry[]
  new_badges: Badge[]
}

export interface BadgeStatus extends Badge {
  earned_on: string | null
  earned: { challenge_id: string; challenge_name: string; earned_on: string }[]
}

export interface Stars {
  total_stars: number
  by_challenge: { challenge_id: string; name: string; stars: number; badges: number }[]
}

// ---------------------------------------------------------------- dashboard (GET /challenges/{id}/dashboard)
/** completion is null when there is nothing to score yet; the UI shows "-". */
interface Counts {
  done: number
  missed: number
  na: number
  completion: number | null
}

export interface Dashboard {
  as_of: string
  streaks: { current: number; longest: number; perfect_current: number; perfect_longest: number }
  kpis: {
    total_days: number
    days_in: number
    days_left: number
    overall_completion: number | null
    perfect_days: number
    goals_completed: number
    missed: number
    na: number
  }
  goals: (Counts & { goal_id: string; name: string; retired: boolean })[]
  months: (Counts & {
    month: string
    days: number
    perfect_days: number
    avg_daily_score: number | null
    best_day: number | null
  })[]
  goal_months: (Counts & { goal_id: string; month: string })[]
  weeks: { week: number; from: string; to: string; done: number; possible: number; completion: number | null }[]
  days: { date: string; done: number; missed: number; na: number; applicable: number; pending: number; score: number | null }[]
}
