import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from './api'
import type {
  ChallengeShare,
  Friends,
  ShareLink,
  ShareLinkCreated,
  ShareScope,
  SharedChallenge,
  SharedView,
} from './types'

export const sharingKeys = {
  links: (id: string) => ['share-links', id] as const,
  shares: (id: string) => ['shares', id] as const,
  friends: ['friends'] as const,
  sharedWithMe: ['shared-with-me'] as const,
  shared: (id: string) => ['shared', id] as const,
  publicView: (token: string) => ['public-share', token] as const,
}

// ---------------------------------------------------------------- public links
export const useShareLinks = (challengeId: string) =>
  useQuery({
    queryKey: sharingKeys.links(challengeId),
    queryFn: () => api<ShareLink[]>(`/challenges/${challengeId}/share-links`),
  })

export function useCreateShareLink(challengeId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (v: { scope: ShareScope; expires_at?: string }) =>
      api<ShareLinkCreated>(`/challenges/${challengeId}/share-links`, { method: 'POST', json: v }),
    onSuccess: () => qc.invalidateQueries({ queryKey: sharingKeys.links(challengeId) }),
  })
}

export function useRevokeShareLink(challengeId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (linkId: string) => api<void>(`/share-links/${linkId}`, { method: 'DELETE' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: sharingKeys.links(challengeId) }),
  })
}

/** The logged-out page. A 404 means unknown, revoked or expired: they are deliberately the same. */
export const usePublicShare = (token: string | undefined) =>
  useQuery({
    queryKey: sharingKeys.publicView(token ?? ''),
    queryFn: () => api<SharedView>(`/public/share/${token}`),
    enabled: Boolean(token),
    retry: false,
  })

// ---------------------------------------------------------------- friends
export const useFriends = () =>
  useQuery({ queryKey: sharingKeys.friends, queryFn: () => api<Friends>('/friends') })

export function useSendFriendRequest() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (email: string) =>
      api<{ message: string }>('/friends/requests', { method: 'POST', json: { email } }),
    onSuccess: () => qc.invalidateQueries({ queryKey: sharingKeys.friends }),
  })
}

export function useAnswerRequest() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (v: { id: string; accept: boolean }) =>
      api<void>(`/friends/requests/${v.id}/${v.accept ? 'accept' : 'decline'}`, { method: 'POST' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: sharingKeys.friends }),
  })
}

export function useRemoveFriend() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (userId: string) => api<void>(`/friends/${userId}`, { method: 'DELETE' }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: sharingKeys.friends })
      qc.invalidateQueries({ queryKey: sharingKeys.sharedWithMe })
      qc.invalidateQueries({ queryKey: ['shares'] })
    },
  })
}

// ---------------------------------------------------------------- sharing with a friend
export const useChallengeShares = (challengeId: string) =>
  useQuery({
    queryKey: sharingKeys.shares(challengeId),
    queryFn: () => api<ChallengeShare[]>(`/challenges/${challengeId}/shares`),
  })

export function useToggleShare(challengeId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (v: { friendId: string; share: boolean }): Promise<unknown> =>
      v.share
        ? api<ChallengeShare>(`/challenges/${challengeId}/shares`, {
            method: 'POST',
            json: { friend_id: v.friendId },
          })
        : api<void>(`/challenges/${challengeId}/shares/${v.friendId}`, { method: 'DELETE' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: sharingKeys.shares(challengeId) }),
  })
}

export const useSharedWithMe = () =>
  useQuery({
    queryKey: sharingKeys.sharedWithMe,
    queryFn: () => api<SharedChallenge[]>('/shared-with-me'),
  })

export const useSharedView = (challengeId: string | undefined) =>
  useQuery({
    queryKey: sharingKeys.shared(challengeId ?? ''),
    queryFn: () => api<SharedView>(`/shared-with-me/${challengeId}/dashboard`),
    enabled: Boolean(challengeId),
    retry: false,
  })
