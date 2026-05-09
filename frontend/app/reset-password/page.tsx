'use client';

import { Suspense, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Eye, EyeOff, Check, X } from 'lucide-react';
import { ThemeToggle } from '@/components/layout/ThemeToggle';

const RULES = [
  { label: '8+ characters', test: (p: string) => p.length >= 8 },
  { label: 'One uppercase', test: (p: string) => /[A-Z]/.test(p) },
  { label: 'One number', test: (p: string) => /\d/.test(p) },
  { label: 'One special character', test: (p: string) => /[^A-Za-z0-9]/.test(p) },
];

function ResetPasswordInner() {
  const router = useRouter();
  const params = useSearchParams();
  const token = params.get('token') ?? '';

  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [done, setDone] = useState(false);

  const allRulesMet = RULES.every((r) => r.test(password));
  const passwordsMatch = password === confirm && confirm.length > 0;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!allRulesMet || !passwordsMatch) return;
    if (!token) {
      setError('Reset link is invalid or expired. Please request a new one.');
      return;
    }
    setLoading(true);
    setError('');
    const API_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? '';
    try {
      const res = await fetch(`${API_URL}/auth/reset-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, password }),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Reset failed. The link may have expired.');
      }
      setDone(true);
      setTimeout(() => router.push('/login'), 3000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
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
          {done ? (
            <div className="flex flex-col items-center text-center gap-4">
              <div
                className="flex h-14 w-14 items-center justify-center rounded-full"
                style={{ background: 'rgba(34,197,94,0.12)', border: '1px solid rgba(34,197,94,0.3)' }}
              >
                <Check className="h-7 w-7 text-green-400" />
              </div>
              <h2 className="text-[22px] font-bold">Password updated!</h2>
              <p className="text-[13px] text-[var(--text-secondary)]">
                Redirecting you to sign in&hellip;
              </p>
              <Link href="/login" className="text-[13px] font-semibold text-[var(--accent)] hover:underline">
                Go now
              </Link>
            </div>
          ) : (
            <>
              <div className="mb-6">
                <h2 className="text-[22px] font-bold lg:text-[26px]">Set new password</h2>
                <p className="mt-1 text-[13px] text-[var(--text-secondary)]">
                  Choose a strong password for your account
                </p>
              </div>

              <form onSubmit={handleSubmit} className="space-y-5">
                {error && (
                  <div className="rounded-lg border border-[color:rgba(239,68,68,0.3)] bg-[color:rgba(239,68,68,0.1)] p-2.5 text-[11px] text-[var(--danger)]">
                    {error}
                  </div>
                )}

                {!token && (
                  <div className="rounded-lg border border-[color:rgba(239,68,68,0.3)] bg-[color:rgba(239,68,68,0.1)] p-2.5 text-[11px] text-[var(--danger)]">
                    Invalid or missing reset token.{' '}
                    <Link href="/forgot-password" className="font-semibold underline">
                      Request a new link
                    </Link>
                  </div>
                )}

                {/* New password */}
                <div>
                  <label className="mb-1.5 block text-[10px] font-medium uppercase tracking-[0.08em] text-[var(--text-secondary)]">
                    New Password
                  </label>
                  <div className="relative">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••"
                      className="w-full rounded-lg border bg-[var(--background)] px-3.5 py-2.5 pr-10 text-[13px] text-[var(--text-primary)] outline-none transition-all placeholder:text-[var(--text-secondary)] focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accent)]"
                      style={{ borderColor: 'rgba(255,255,255,0.1)' }}
                      suppressHydrationWarning
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                      tabIndex={-1}
                    >
                      {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                    </button>
                  </div>

                  {/* Password rules */}
                  {password.length > 0 && (
                    <div className="mt-2 grid grid-cols-2 gap-1">
                      {RULES.map((rule) => {
                        const ok = rule.test(password);
                        return (
                          <div key={rule.label} className="flex items-center gap-1">
                            {ok
                              ? <Check size={10} className="text-green-400 flex-shrink-0" />
                              : <X size={10} className="text-[var(--danger)] flex-shrink-0" />}
                            <span className={`text-[10px] ${ok ? 'text-green-400' : 'text-[var(--text-secondary)]'}`}>
                              {rule.label}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>

                {/* Confirm password */}
                <div>
                  <label className="mb-1.5 block text-[10px] font-medium uppercase tracking-[0.08em] text-[var(--text-secondary)]">
                    Confirm Password
                  </label>
                  <input
                    type="password"
                    required
                    value={confirm}
                    onChange={(e) => setConfirm(e.target.value)}
                    placeholder="••••••••"
                    className="w-full rounded-lg border bg-[var(--background)] px-3.5 py-2.5 text-[13px] text-[var(--text-primary)] outline-none transition-all placeholder:text-[var(--text-secondary)] focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accent)]"
                    style={{
                      borderColor: confirm.length > 0
                        ? passwordsMatch ? 'rgba(34,197,94,0.5)' : 'rgba(239,68,68,0.5)'
                        : 'rgba(255,255,255,0.1)',
                    }}
                    suppressHydrationWarning
                  />
                  {confirm.length > 0 && !passwordsMatch && (
                    <p className="mt-1 text-[10px] text-[var(--danger)]">Passwords don&apos;t match</p>
                  )}
                </div>

                <button
                  type="submit"
                  disabled={loading || !allRulesMet || !passwordsMatch || !token}
                  className="accent-gradient h-[48px] w-full rounded-xl font-semibold text-[14px] text-white shadow-[0_4px_16px_rgba(233,83,53,0.3)] transition-all duration-200 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:hover:scale-100"
                >
                  {loading ? 'Updating...' : 'Update Password'}
                </button>

                <p className="text-center text-[12px] text-[var(--text-secondary)]">
                  <Link href="/login" className="font-semibold text-[var(--accent)] hover:underline">
                    Back to sign in
                  </Link>
                </p>
              </form>
            </>
          )}
        </div>
      </main>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense>
      <ResetPasswordInner />
    </Suspense>
  );
}
