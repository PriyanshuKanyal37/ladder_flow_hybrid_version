'use client';

import { useEffect } from 'react';

interface ConfirmModalProps {
  /** Show/hide trigger. Modal renders nothing when null. */
  open: boolean;
  /** Title shown in bold next to the icon. */
  title: string;
  /** Optional emphasised line — e.g. the name of the item being deleted. */
  highlight?: string;
  /** Body copy explaining what happens. */
  description: string;
  /** Label for the destructive button. */
  confirmLabel?: string;
  /** Material symbol name for the leading icon. */
  icon?: string;
  /** Treat as destructive (red) or neutral (accent color). */
  variant?: 'danger' | 'neutral';
  /** Whether the confirm action is currently running — disables both buttons + shows spinner. */
  busy?: boolean;
  /** Cancel handler — fires on Cancel click, ESC, or backdrop click. */
  onCancel: () => void;
  /** Confirm handler — fires on confirm button click. */
  onConfirm: () => void | Promise<void>;
}

/**
 * Production-grade confirm dialog. Replaces native browser `confirm()`.
 *
 * Features:
 *  - Backdrop click closes (unless busy)
 *  - ESC closes (unless busy)
 *  - Body scroll locked while open
 *  - Spinner inside confirm button when `busy=true`
 *  - ARIA: role="dialog", aria-modal, aria-labelledby
 *  - Matches app design system via CSS vars (--surface, --accent, etc.)
 */
export function ConfirmModal({
  open,
  title,
  highlight,
  description,
  confirmLabel = 'Delete',
  icon = 'delete_forever',
  variant = 'danger',
  busy = false,
  onCancel,
  onConfirm,
}: ConfirmModalProps) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !busy) onCancel();
    };
    document.addEventListener('keydown', onKey);
    // Lock background scroll while modal is open
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = prevOverflow;
    };
  }, [open, busy, onCancel]);

  if (!open) return null;

  const accentBg = variant === 'danger' ? 'rgba(239,68,68,0.12)' : 'rgba(233,83,53,0.12)';
  const accentBorder = variant === 'danger' ? 'rgba(239,68,68,0.25)' : 'rgba(233,83,53,0.25)';
  const accentColor = variant === 'danger' ? '#ef4444' : 'var(--accent)';
  const btnBg = variant === 'danger' ? '#ef4444' : 'var(--accent)';
  const btnShadow = variant === 'danger' ? '0 4px 14px rgba(239,68,68,0.35)' : '0 4px 14px rgba(233,83,53,0.35)';

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-modal-title"
      className="fixed inset-0 z-[100] flex items-center justify-center px-4"
      style={{ background: 'rgba(0,0,0,0.55)', backdropFilter: 'blur(4px)' }}
      onClick={() => { if (!busy) onCancel(); }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-md rounded-2xl p-6"
        style={{
          background: 'var(--surface)',
          border: '1px solid var(--border-default)',
          boxShadow: '0 20px 50px rgba(0,0,0,0.4)',
        }}
      >
        <div className="mb-4 flex items-center gap-3">
          <span
            className="flex h-10 w-10 items-center justify-center rounded-full"
            style={{ background: accentBg, border: `1px solid ${accentBorder}` }}
          >
            <span className="material-symbols-outlined text-[20px]" style={{ color: accentColor }}>{icon}</span>
          </span>
          <h2
            id="confirm-modal-title"
            className="text-[15px] font-extrabold text-primary"
          >
            {title}
          </h2>
        </div>
        {highlight && (
          <p className="mb-1 text-[13px] text-[var(--text-primary)]">
            &ldquo;{highlight}&rdquo;
          </p>
        )}
        <p className="mb-5 text-[12px] text-[var(--text-secondary)]">{description}</p>
        <div className="flex justify-end gap-2">
          <button
            type="button"
            disabled={busy}
            onClick={onCancel}
            className="rounded-xl px-4 py-2 text-[12px] font-semibold text-[var(--text-secondary)] transition-all hover:text-[var(--text-primary)] disabled:opacity-50"
            style={{ border: '1px solid var(--border-default)' }}
          >
            Cancel
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={() => { void onConfirm(); }}
            className="flex items-center gap-2 rounded-xl px-4 py-2 text-[12px] font-bold text-white transition-all hover:scale-[1.02] disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:scale-100"
            style={{ background: btnBg, boxShadow: btnShadow }}
          >
            {busy ? (
              <>
                <span className="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" />
                Working…
              </>
            ) : (
              <>
                <span className="material-symbols-outlined text-[14px]">{icon}</span>
                {confirmLabel}
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
