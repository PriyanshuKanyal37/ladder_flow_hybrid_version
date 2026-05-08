import { useQuery } from '@tanstack/react-query';
import { discoverTrendingTopics } from '@/lib/api/trending';
import type { ResearchResult } from '@/lib/types/trending';

interface UseTrendingTopicsOptions {
  keywords: string;
  enabled?: boolean;
  // Hydrate from sessionStorage when user navigates back to this page so
  // they don't see the research animation again or hit the Perplexity API.
  initialData?: ResearchResult;
}

export function useTrendingTopics({
  keywords,
  enabled = true,
  initialData,
}: UseTrendingTopicsOptions) {
  return useQuery<ResearchResult, Error>({
    queryKey: ['trending-topics', keywords],
    queryFn: () => discoverTrendingTopics(keywords),
    enabled: enabled && keywords.length > 0,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
    gcTime: 10 * 60 * 1000, // Keep in cache for 10 minutes
    retry: 0, // Manual retry button exists in the UI; avoid duplicate backend load
    initialData,
    // Important: when initialData is supplied we don't want a background
    // refetch on mount (would burn Perplexity credits + show loading flash).
    // Keep the cached angles unless user explicitly clicks Retry.
    refetchOnMount: initialData ? false : true,
    refetchOnWindowFocus: false,
  });
}

