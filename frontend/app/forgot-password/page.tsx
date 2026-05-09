'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { ThemeToggle } from '@/components/layout/ThemeToggle';

const RESEND_COOLDOWN = 60;

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');
  const [cooldown, setCooldown] = useState(0);

  useEffect(() => {
    if (cooldown <= 0) return;
    const t = setTimeout(() => setCooldown((c) => c - 1), 1000);
    return () => clearTimeout(t);
  }, [cooldown]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    const API_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? '';
    try {
      await fetch(`${API_URL}/auth/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });
      // Always show success — never reveal whether the email exists
      setSent(true);
      setCooldown(RESEND_COOLDOWN);
    } catch {
      setError('Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const resend = async () => {
    if (cooldown > 0) return;
    setLoading(true);
    setError('');
    const API_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? '';
    try {
      await fetch(`${API_URL}/auth/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });
      setCooldown(RESEND_COOLDOWN);
    } catch {
      setError('Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen bg-[var(--background)] text-[var(--text-primary)] selection:bg-[color:rgba(233,83,53,0.3)]">
      <div className="mesh-background" />

      <header className="fixed top-0 z-50 flex w-full items-center justify-between px-6 py-4 sm:px-8">
        <Link href="/login" className="flex items-center gap-2">
          <span
            className="material-symbols-outlined text-[22px] text-[var(--accent)]"
            style={{ fontVariationSettings: "'FILL' 1" }}
          >
            mic
          </span>
          <span className="text-[17px] font-bold tracking-tight">Ladder Flow</span>
        </Link>
        <ThemeToggle />
      </header>

      <main className="flex min-h-screen items-center justify-center p-5 pt-20 pb-16">
        <div
          className="w-full max-w-[420px] rounded-2xl p-7 lg:p-10 z-10"
          style={{
            background: 'var(--form-glass-bg, rgba(26,26,26,0.88))',
            backdropFilter: 'blur(20px)',
            border: '1px solid var(--form-glass-border, rgba(255,255,255,0.08))',
            boxShadow: '0 8px 32px rgba(0,0,0,0.45)',
          }}
          suppressHydrationWarning
        >
          {!sent ? (
            <>
              <div className="mb-6">
                <h2 className="text-[22px] font-bold lg:text-[26px]">Forgot password?</h2>
                <p className="mt-1 text-[13px] text-[var(--text-secondary)]">
                  Enter your email and we&apos;ll send a reset link
                </p>
              </div>

              <form onSubmit={submit} className="space-y-5">
                {error && (
                  <div className="rounded-lg border border-[color:rgba(239,68,68,0.3)] bg-[color:rgba(239,68,68,0.1)] p-2.5 text-[11px] text-[var(--danger)]">
                    {error}
                  </div>
                )}

                <div>
                  <label className="mb-1.5 block text-[10px] font-medium uppercase tracking-[0.08em] text-[var(--text-secondary)]">
                    Email Address
                  </label>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="executive@founder.com"
                    className="w-full rounded-lg border bg-[var(--background)] px-3.5 py-2.5 text-[13px] text-[var(--text-primary)] outline-none transition-all placeholder:text-[var(--text-secondary)] focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accent)]"
                    style={{ borderColor: 'rgba(255,255,255,0.1)' }}
                    suppressHydrationWarning
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="accent-gradient h-[48px] w-full rounded-xl font-semibold text-[14px] text-white shadow-[0_4px_16px_rgba(233,83,53,0.3)] transition-all duration-200 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:hover:scale-100"
                >
                  {loading ? 'Sending...' : 'Send Reset Link'}
                </button>

                <p className="text-center text-[12px] text-[var(--text-secondary)]">
                  <Link href="/login" className="font-semibold text-[var(--accent)] hover:underline">
                    Back to sign in
                  </Link>
                </p>
              </form>
            </>
          ) : (
            <>
              <div className="mb-6 flex flex-col items-center text-center">
                <div
                  className="mb-4 flex h-14 w-14 items-center justify-center rounded-full"
                  style={{ background: 'rgba(233,83,53,0.12)', border: '1px solid rgba(233,83,53,0.25)' }}
                >
                  <span
                    className="material-symbols-outlined text-[28px] text-[var(--accent)]"
                    style={{ fontVariationSettings: "'FILL' 1" }}
                  >
                    mark_email_read
                  </span>
                </div>
                <h2 className="text-[22px] font-bold lg:text-[24px]">Check your inbox</h2>
                <p className="mt-2 text-[13px] text-[var(--text-secondary)] leading-relaxed">
                  If <span className="text-[var(--text-primary)] font-medium">{email}</span> exists in our system,
                  you&apos;ll receive a reset link shortly.
                </p>
              </div>

              {error && (
                <div className="mb-4 rounded-lg border border-[color:rgba(239,68,68,0.3)] bg-[color:rgba(239,68,68,0.1)] p-2.5 text-[11px] text-[var(--danger)]">
                  {error}
                </div>
              )}

              <div className="space-y-3">
                <button
                  onClick={resend}
                  disabled={loading || cooldown > 0}
                  className="h-[44px] w-full rounded-xl border text-[13px] font-medium transition-all duration-200 hover:border-[var(--accent)] hover:text-[var(--accent)] disabled:cursor-not-allowed disabled:opacity-50"
                  style={{ borderColor: 'rgba(255,255,255,0.1)' }}
                  suppressHydrationWarning
                >
                  {loading
                    ? 'Sending...'
                    : cooldown > 0
                    ? `Resend in ${cooldown}s`
                    : 'Resend email'}
                </button>

                <p className="text-center text-[12px] text-[var(--text-secondary)]">
                  <Link href="/login" className="font-semibold text-[var(--accent)] hover:underline">
                    Back to sign in
                  </Link>
                </p>
              </div>
            </>
          )}
        </div>
      </main>
    </div>
  );
}
