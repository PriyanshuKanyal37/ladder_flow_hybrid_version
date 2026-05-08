'use client';

import { useEffect, useLayoutEffect, useRef, useState } from 'react';

export interface HamburgerMenuItem {
  key: string;
  label: string;
  icon?: string;
  danger?: boolean;
  disabled?: boolean;
  onSelect: () => void | Promise<void>;
}

interface HamburgerMenuProps {
  items: HamburgerMenuItem[];
  ariaLabel?: string;
  align?: 'left' | 'right';
}

const ITEM_HEIGHT = 36;       // approx px per menu item (py-2 + line-height)
const MENU_PADDING = 8;       // top/bottom padding inside menu
const VIEWPORT_MARGIN = 8;    // space we want to leave at edges

export function HamburgerMenu({
  items,
  ariaLabel = 'Open actions',
  align = 'right',
}: HamburgerMenuProps) {
  const [open, setOpen] = useState(false);
  const [placement, setPlacement] = useState<'bottom' | 'top'>('bottom');
  const [horizontal, setHorizontal] = useState<'left' | 'right'>(align);
  const rootRef = useRef<HTMLDivElement | null>(null);
  const btnRef = useRef<HTMLButtonElement | null>(null);

  // Click outside + ESC to close.
  useEffect(() => {
    if (!open) return;
    function onClickAway(e: MouseEvent) {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) setOpen(false);
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') setOpen(false);
    }
    window.addEventListener('mousedown', onClickAway);
    window.addEventListener('keydown', onKey);
    return () => {
      window.removeEventListener('mousedown', onClickAway);
      window.removeEventListener('keydown', onKey);
    };
  }, [open]);

  // Reposition menu BEFORE paint to avoid flicker.
  // Measures available space around the trigger, flips up when bottom is
  // tight, and flips horizontal alignment when right edge would clip.
  useLayoutEffect(() => {
    if (!open || !btnRef.current) return;

    const recompute = () => {
      const btn = btnRef.current;
      if (!btn) return;
      const rect = btn.getBoundingClientRect();
      const vh = window.innerHeight;
      const vw = window.innerWidth;

      const estimatedHeight = items.length * ITEM_HEIGHT + MENU_PADDING * 2;
      const spaceBelow = vh - rect.bottom - VIEWPORT_MARGIN;
      const spaceAbove = rect.top - VIEWPORT_MARGIN;

      // Prefer bottom; flip up only if it doesn't fit AND there's more room above.
      if (spaceBelow < estimatedHeight && spaceAbove > spaceBelow) {
        setPlacement('top');
      } else {
        setPlacement('bottom');
      }

      // Horizontal: if default 'right' would push the menu off the right edge
      // (button is too far left), or default 'left' would push it off the left
      // edge, flip the other way. Most cases are fine; this only kicks in when
      // the trigger is very close to a viewport edge.
      const estimatedWidth = 200; // matches min-w-[180px] + slight buffer
      if (align === 'right') {
        // Menu anchors to right of button: it extends LEFT.
        // If button is too close to left edge, button.left - menu_width < 0.
        if (rect.right - estimatedWidth < VIEWPORT_MARGIN) {
          setHorizontal('left');
        } else {
          setHorizontal('right');
        }
      } else {
        // Menu anchors to left of button: it extends RIGHT.
        if (rect.left + estimatedWidth > vw - VIEWPORT_MARGIN) {
          setHorizontal('right');
        } else {
          setHorizontal('left');
        }
      }
    };

    recompute();

    // Reposition on scroll/resize while open so the menu doesn't drift off-screen.
    window.addEventListener('scroll', recompute, true);
    window.addEventListener('resize', recompute);
    return () => {
      window.removeEventListener('scroll', recompute, true);
      window.removeEventListener('resize', recompute);
    };
  }, [open, items.length, align]);

  const verticalStyle: React.CSSProperties =
    placement === 'top'
      ? { bottom: '100%', marginBottom: 4 }
      : { top: '100%', marginTop: 4 };

  return (
    <div ref={rootRef} className="relative">
      <button
        ref={btnRef}
        type="button"
        aria-label={ariaLabel}
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={(e) => {
          e.stopPropagation();
          e.preventDefault();
          setOpen((v) => !v);
        }}
        className="flex h-8 w-8 items-center justify-center rounded-lg transition-colors hover:bg-[var(--surface-raised)]"
        style={{ color: 'var(--text-secondary)', border: '1px solid var(--border-default)' }}
      >
        <span className="material-symbols-outlined text-[18px]">more_vert</span>
      </button>

      {open && (
        <div
          role="menu"
          className="absolute z-50 min-w-[180px] overflow-hidden rounded-xl shadow-xl"
          style={{
            ...verticalStyle,
            [horizontal]: 0,
            background: 'var(--surface)',
            border: '1px solid var(--border-default)',
            backdropFilter: 'blur(12px)',
          } as React.CSSProperties}
        >
          {items.map((item) => (
            <button
              key={item.key}
              role="menuitem"
              type="button"
              disabled={item.disabled}
              onClick={async (e) => {
                e.stopPropagation();
                e.preventDefault();
                setOpen(false);
                if (!item.disabled) await item.onSelect();
              }}
              className="flex w-full items-center gap-2.5 px-3 py-2 text-left text-[12px] font-medium transition-colors hover:bg-[var(--surface-raised)] disabled:cursor-not-allowed disabled:opacity-40"
              style={{ color: item.danger ? 'var(--danger)' : 'var(--text-primary)' }}
            >
              {item.icon && (
                <span className="material-symbols-outlined text-[16px]" aria-hidden>
                  {item.icon}
                </span>
              )}
              {item.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
