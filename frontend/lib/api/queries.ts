/**
 * Central TanStack Query hooks for hot data paths.
 *
 * Why: every page that fetched via raw `fetch()` in `useEffect` was paying
 * 5-10s on every navigation. With these hooks, the second visit is served
 * from cache in <100ms, while a background refetch keeps data fresh.
 *
 * Cache invalidation: when something changes (interview ends, memory edited,
 * post regenerated), the corresponding mutation MUST call
 * `queryClient.invalidateQueries({ queryKey: [...] })` so the UI updates
 * without a manual refresh.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { authHeaders } from '@/lib/auth';

// ── Query keys (single source of truth) ───────────────────────────────────
export const queryKeys = {
  interviews: ['interviews'] as const,
  interview: (id: string) => ['interviews', id] as const,
  brainMemories: ['brain', 'memories'] as const,
  brainGraph: ['brain', 'graph'] as const,
  brainStats: ['brain', 'stats'] as const,
  posts: ['posts'] as const,
  userProfile: ['user', 'profile'] as const,
  ttsCredits: ['tts', 'credits'] as const,
};

// ── TTS credit pre-flight ─────────────────────────────────────────────────
export interface TtsProviderStatus {
  available: boolean;
  configured: boolean;
  remaining_chars: number | null;          // ElevenLabs uses chars
  limit_chars: number | null;
  remaining_usd?: number | null;            // Deepgram uses USD balance
  estimated_minutes_remaining?: number | null;  // human-friendly: minutes of agent speech left
  warning: boolean;
  exhausted: boolean;
  error: string | null;
  credit_check_supported?: boolean;         // false for Cartesia/Inworld (no public API)
}

export interface TtsCreditsResponse {
  providers: {
    elevenlabs: TtsProviderStatus;
    cartesia: TtsProviderStatus;
    inworld: TtsProviderStatus;
    deepgram: TtsProviderStatus;
  };
}

export function useTtsCredits() {
  return useQuery<TtsCreditsResponse>({
    queryKey: queryKeys.ttsCredits,
    queryFn: () => fetchJson<TtsCreditsResponse>('/api/tts-credits'),
    // Refresh every 60s while the page is open — credits change slowly.
    staleTime: 60 * 1000,
    retry: 0,
  });
}

// ── Fetch helpers ─────────────────────────────────────────────────────────
async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url, { headers: authHeaders() });
  if (!res.ok) {
    throw new Error(`${url}: ${res.status}`);
  }
  return res.json();
}

// ── Query hooks ───────────────────────────────────────────────────────────

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function useInterviews<T = any>() {
  return useQuery<T[]>({
    queryKey: queryKeys.interviews,
    queryFn: () => fetchJson<T[]>('/api/interviews'),
  });
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function useBrainMemories<T = any>() {
  return useQuery<T[]>({
    queryKey: queryKeys.brainMemories,
    queryFn: () => fetchJson<T[]>('/api/brain/memories'),
  });
}

export function useBrainGraph<T = { nodes: unknown[]; links: unknown[] }>() {
  return useQuery<T>({
    queryKey: queryKeys.brainGraph,
    queryFn: () => fetchJson<T>('/api/brain/graph'),
  });
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function usePosts<T = any>() {
  return useQuery<T[]>({
    queryKey: queryKeys.posts,
    queryFn: () => fetchJson<T[]>('/api/posts'),
  });
}

export function useInvalidatePosts() {
  const qc = useQueryClient();
  return () => qc.invalidateQueries({ queryKey: queryKeys.posts });
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function useUserProfile<T = any>() {
  return useQuery<T>({
    queryKey: queryKeys.userProfile,
    queryFn: () => fetchJson<T>('/api/users/profile'),
    // Profile rarely changes — keep it warm for longer.
    staleTime: 5 * 60 * 1000,
  });
}

export function useInvalidateUserProfile() {
  const qc = useQueryClient();
  return () => qc.invalidateQueries({ queryKey: queryKeys.userProfile });
}

// ── Mutation: after any write that changes data, invalidate ───────────────
export function useInvalidateInterviews() {
  const qc = useQueryClient();
  return () => qc.invalidateQueries({ queryKey: queryKeys.interviews });
}

export function useInvalidateBrain() {
  const qc = useQueryClient();
  return () => {
    qc.invalidateQueries({ queryKey: queryKeys.brainMemories });
    qc.invalidateQueries({ queryKey: queryKeys.brainGraph });
    qc.invalidateQueries({ queryKey: queryKeys.brainStats });
  };
}

// Combined invalidation for "interview ended" — refresh sessions list AND
// brain (because new memories were just extracted in background).
export function useInvalidateAfterInterviewEnded() {
  const qc = useQueryClient();
  return () => {
    qc.invalidateQueries({ queryKey: queryKeys.interviews });
    qc.invalidateQueries({ queryKey: queryKeys.brainMemories });
    qc.invalidateQueries({ queryKey: queryKeys.brainGraph });
    qc.invalidateQueries({ queryKey: queryKeys.brainStats });
  };
}

// Generic mutation helper — pass the query keys to invalidate after success.
export function useApiMutation<TVars, TResp>(
  fn: (vars: TVars) => Promise<TResp>,
  invalidate: readonly (readonly string[])[] = [],
) {
  const qc = useQueryClient();
  return useMutation<TResp, Error, TVars>({
    mutationFn: fn,
    onSuccess: () => {
      for (const key of invalidate) {
        qc.invalidateQueries({ queryKey: key });
      }
    },
  });
}
