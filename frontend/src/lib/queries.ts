import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from './api'
import type {
  Challenge,
  ChallengeDetail,
  Entry,
  EntryWriteResult,
  Goal,
  Profile,
  Status,
  Template,
} from './types'

export const keys = {
  me: ['me'] as const,
  templates: ['templates'] as const,
  challenges: (status?: string) => ['challenges', status ?? 'all'] as const,
  challenge: (id: string) => ['challenge', id] as const,
  entries: (id: string) => ['entries', id] as const,
}

// ---------------------------------------------------------------- profile
export const useProfile = (enabled = true) =>
  useQuery({ queryKey: keys.me, queryFn: () => api<Profile>('/me'), enabled, staleTime: 60_000 })

export function useUpdateProfile() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: Partial<Pick<Profile, 'display_name' | 'avatar_color' | 'timezone'>>) =>
      api<Profile>('/me', { method: 'PATCH', json: body }),
    onSuccess: (p) => qc.setQueryData(keys.me, p),
  })
}

// ---------------------------------------------------------------- challenges
export const useTemplates = () =>
  useQuery({ queryKey: keys.templates, queryFn: () => api<Template[]>('/templates') })

export const useChallenges = () =>
  useQuery({ queryKey: keys.challenges(), queryFn: () => api<Challenge[]>('/challenges') })

export const useChallenge = (id: string | undefined) =>
  useQuery({
    queryKey: keys.challenge(id ?? ''),
    queryFn: () => api<ChallengeDetail>(`/challenges/${id}`),
    enabled: Boolean(id),
  })

export function useCreateChallenge() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: {
      name: string
      start_date: string
      end_date: string
      template_id?: string
      goals?: string[]
    }) => api<ChallengeDetail>('/challenges', { method: 'POST', json: body }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['challenges'] }),
  })
}

export function useUpdateChallenge(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: Partial<Pick<Challenge, 'name' | 'start_date' | 'end_date' | 'status'>>) =>
      api<ChallengeDetail>(`/challenges/${id}`, { method: 'PATCH', json: body }),
    onSuccess: (c) => {
      qc.setQueryData(keys.challenge(id), c)
      qc.invalidateQueries({ queryKey: ['challenges'] })
    },
  })
}

export function useDeleteChallenge() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api<void>(`/challenges/${id}?confirm=true`, { method: 'DELETE' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['challenges'] }),
  })
}

// ---------------------------------------------------------------- goals
function useGoalMutation<V>(challengeId: string, fn: (v: V) => Promise<unknown>) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: fn,
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.challenge(challengeId) }),
  })
}

export const useAddGoal = (challengeId: string) =>
  useGoalMutation(challengeId, (name: string) =>
    api<Goal>(`/challenges/${challengeId}/goals`, { method: 'POST', json: { name } }),
  )

export const useRenameGoal = (challengeId: string) =>
  useGoalMutation(challengeId, (v: { id: string; name: string }) =>
    api<Goal>(`/goals/${v.id}`, { method: 'PATCH', json: { name: v.name } }),
  )

export const useReorderGoals = (challengeId: string) =>
  useGoalMutation(challengeId, (goalIds: string[]) =>
    api<Goal[]>(`/challenges/${challengeId}/goals/order`, {
      method: 'PUT',
      json: { goal_ids: goalIds },
    }),
  )

export const useRetireGoal = (challengeId: string) =>
  useGoalMutation(challengeId, (v: { id: string; on: string }) =>
    api<Goal>(`/goals/${v.id}/retire`, { method: 'POST', json: { on: v.on } }),
  )

export function useDeleteGoal(challengeId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api<void>(`/goals/${id}?confirm=true`, { method: 'DELETE' }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: keys.challenge(challengeId) })
      qc.invalidateQueries({ queryKey: keys.entries(challengeId) })
    },
  })
}

// ---------------------------------------------------------------- entries
export const useEntries = (challengeId: string | undefined) =>
  useQuery({
    queryKey: keys.entries(challengeId ?? ''),
    queryFn: () => api<Entry[]>(`/challenges/${challengeId}/entries`),
    enabled: Boolean(challengeId),
  })

/** Set (or, with status=null, clear) one goal on one day, updating the cache optimistically. */
export function useSetEntry(challengeId: string) {
  const qc = useQueryClient()
  const key = keys.entries(challengeId)

  type Vars = { goalId: string; date: string; status: Status | null }
  return useMutation<unknown, Error, Vars, { previous?: Entry[] }>({
    mutationFn: (v) =>
      v.status === null
        ? api<void>(`/goals/${v.goalId}/entries/${v.date}`, { method: 'DELETE' })
        : api<EntryWriteResult>(`/goals/${v.goalId}/entries/${v.date}`, {
            method: 'PUT',
            json: { status: v.status },
          }),
    onMutate: async (v) => {
      await qc.cancelQueries({ queryKey: key })
      const previous = qc.getQueryData<Entry[]>(key)
      const rest = (previous ?? []).filter(
        (e) => !(e.goal_id === v.goalId && e.entry_date === v.date),
      )
      qc.setQueryData<Entry[]>(
        key,
        v.status === null ? rest : [...rest, { goal_id: v.goalId, entry_date: v.date, status: v.status }],
      )
      return { previous }
    },
    onError: (_e, _v, ctx) => {
      if (ctx?.previous) qc.setQueryData(key, ctx.previous)
    },
    onSettled: () => qc.invalidateQueries({ queryKey: key }),
  })
}
