'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '@/lib/context/ThemeContext';

/**
 * Module-level QueryClient — exported so the logout flow can call
 * `queryClient.clear()` to drop ALL cached per-user query data when the
 * user signs out. Without this, a second user on the same browser sees
 * the previous user's cached `/api/me`, `/api/interviews`, etc.
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // 30s stale window — instant repeat-render from cache, background refetch
      // on remount keeps data fresh without making the user wait.
      staleTime: 30 * 1000,
      retry: 1,
      // Refresh data when user returns to the tab. Critical for "data updated
      // in background but I want to see it instantly" UX.
      refetchOnWindowFocus: true,
      refetchOnMount: true,
    },
  },
});

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    </ThemeProvider>
  );
}
