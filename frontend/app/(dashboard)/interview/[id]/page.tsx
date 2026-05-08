'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function LegacyInterviewPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/sessions');
  }, [router]);

  return null;
}

