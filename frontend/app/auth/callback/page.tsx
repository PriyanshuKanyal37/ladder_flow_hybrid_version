'use client';

import { Suspense, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { setToken } from '@/lib/auth';

function OAuthCallbackInner() {
  const router = useRouter();
  const params = useSearchParams();

  useEffect(() => {
    const token = params.get('token');
    const error = params.get('error');

    if (error || !token) {
      router.replace(`/login?error=${error ?? 'oauth_failed'}`);
      return;
    }

    setToken(token);
    router.replace('/dashboard');
  }, [params, router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--background)]">
      <div className="flex flex-col items-center gap-3">
        <span
          className="material-symbols-outlined animate-spin text-[32px] text-[var(--accent)]"
          style={{ fontVariationSettings: "'FILL' 1" }}
        >
          progress_activity
        </span>
        <p className="text-[13px] text-[var(--text-secondary)]">Signing you in&hellip;</p>
      </div>
    </div>
  );
}

export default function OAuthCallbackPage() {
  return (
    <Suspense>
      <OAuthCallbackInner />
    </Suspense>
  );
}
