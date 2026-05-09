'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useTrendingTopics } from '@/hooks/useTrendingTopics';
import { authHeaders } from '@/lib/auth';
import type { TrendingTopic, ResearchResult } from '@/lib/types/trending';

// ── Source pool ───────────────────────────────────────────────────────────────
const SOURCE_POOL = [
  // Social platforms
  'LinkedIn', 'X (Twitter)', 'Reddit', 'YouTube', 'TikTok',
  'Quora', 'Facebook', 'Instagram', 'Threads',
  // Creator & tech communities
  'Hacker News', 'Product Hunt', 'Substack', 'Medium', 'Indie Hackers',
  // Globally famous news & publications
  'Bloomberg', 'Reuters', 'BBC News', 'The New York Times',
  'Forbes', 'TechCrunch', 'The Economist', 'Wired',
  'The Guardian', 'CNBC', 'Financial Times',
];

// Pick N unique items at random from the pool
function pickRandom<T>(arr: T[], n: number): T[] {
  return [...arr].sort(() => Math.random() - 0.5).slice(0, n);
}

// Static labels for steps 2-4
const STATIC_STEPS = [
  'Mining comments for unanswered questions...',
  'Ranking angles by relevance to your ICP...',
  'Building your content angle map...',
];

interface AngleOption {
  id: string;
  title: string;
  summary: string;
  quote: string;
  tags: string[];
  match: string;
  trending?: boolean;
  // Angle-specific outline + agent context. Each angle is a distinct lens
  // on the topic, so the session arc, talking points, and "why this matters"
  // must differ — otherwise the outline page and the voice agent see
  // identical content regardless of which angle the user picked.
  sessionArc: string;
  talkingPoints: string[];
  whyThisMatters: string;
}

function makeTopicPayload(angle: AngleOption): TrendingTopic {
  return {
    rank: 1,
    topic_title: angle.title,
    global_context: angle.sessionArc,
    why_this_matters: angle.whyThisMatters,
    key_questions: angle.talkingPoints,
  };
}

const STEPS = [
  { id: 1, label: 'Keywords' },
  { id: 2, label: 'Research' },
  { id: 3, label: 'Angles' },
  { id: 4, label: 'Outline' },
];

export default function TrendingTopicsPage() {
  const router = useRouter();
  const [keywords] = useState(() => {
    if (typeof window === 'undefined') return '';
    return sessionStorage.getItem('trending-keywords') ?? '';
  });

  // Hydrate from sessionStorage if we already have a research result FOR
  // THE CURRENT KEYWORDS. If keywords changed (e.g. user went back to
  // /discover and entered different terms), discard the old research so
  // the page re-runs Perplexity for the new query.
  const cachedResearch = (() => {
    if (typeof window === 'undefined') return null;
    try {
      const raw = sessionStorage.getItem('research-context');
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      if (!parsed?.title || !parsed?.deep_context) return null;
      // Compare keywords-stamp on cached research vs current keywords.
      // If absent (legacy data) or mismatched, treat as cold-start.
      const cachedKw = sessionStorage.getItem('research-context-keywords') || '';
      const currentKw = sessionStorage.getItem('trending-keywords') || '';
      if (cachedKw !== currentKw) return null;
      return parsed;
    } catch {
      return null;
    }
  })();

  // Keyword-gated sessionStorage read: stale data from a prior keyword set
  // must not bleed into the current research run.
  const readForCurrentKeywords = <T,>(key: string, parse: (raw: string) => T | null): T | null => {
    if (typeof window === 'undefined') return null;
    try {
      const cachedKw = sessionStorage.getItem('research-context-keywords') || '';
      const currentKw = sessionStorage.getItem('trending-keywords') || '';
      if (cachedKw !== currentKw) return null;
      const raw = sessionStorage.getItem(key);
      if (!raw) return null;
      return parse(raw);
    } catch {
      return null;
    }
  };

  // Restore which angle the user had picked last time, if any.
  const [selectedId, setSelectedId] = useState<string>(
    () => readForCurrentKeywords<string>('selected-angle-id', (r) => r) ?? 'angle-1',
  );
  const [customAngle, setCustomAngle] = useState('');
  // LLM-generated 5th angle from the user's free-form input.
  // Persisted to sessionStorage so back-nav from Outline → Discovery
  // restores the card. Gated by keyword stamp.
  const [generatedAngle, setGeneratedAngle] = useState<AngleOption | null>(
    () => readForCurrentKeywords<AngleOption>('generated-angle', (r) => JSON.parse(r) as AngleOption),
  );
  const [isGeneratingAngle, setIsGeneratingAngle] = useState(false);
  const [angleGenError, setAngleGenError] = useState<string | null>(null);

  // Pick 4 random sources once on mount — never changes during the session
  const [pickedSources] = useState<string[]>(() => pickRandom(SOURCE_POOL, 4));

  // researchStep: 0 = scanning platforms, 1-3 = static steps. If we have
  // cached research from a prior visit (back-nav from Outline), jump to 3.
  const [researchStep, setResearchStep] = useState(cachedResearch ? 3 : 0);
  // platformIdx: which of the 4 picked sources is currently shown in step 0
  const [platformIdx, setPlatformIdx] = useState(0);
  // fade flag for the platform name crossfade
  const [platformFade, setPlatformFade] = useState(false);

  useEffect(() => {
    if (!keywords) router.push('/discover');
  }, [keywords, router]);

  const { data: research, isLoading, error, refetch } = useTrendingTopics({
    keywords,
    enabled: keywords.length > 0,
    initialData: cachedResearch ?? undefined,
  });

  // ── Step 0: cycle through picked platforms with a linger + fade ──────────
  useEffect(() => {
    if (!isLoading || researchStep !== 0) return;
    const timer = setTimeout(() => {
      if (platformIdx < pickedSources.length - 1) {
        // Fade out, swap name, fade in
        setPlatformFade(true);
        setTimeout(() => {
          setPlatformIdx((i) => i + 1);
          setPlatformFade(false);
        }, 220);
      } else {
        // All platforms scanned — advance to step 1
        setResearchStep(1);
      }
    }, 1900);
    return () => clearTimeout(timer);
  }, [isLoading, researchStep, platformIdx, pickedSources.length]);

  // ── Steps 1-3: advance every 1800ms ──────────────────────────────────────
  useEffect(() => {
    if (!isLoading || researchStep === 0 || researchStep >= 3) return;
    const timer = setTimeout(() => setResearchStep((s) => s + 1), 1800);
    return () => clearTimeout(timer);
  }, [isLoading, researchStep]);

  const options = useMemo<AngleOption[]>(() => {
    if (!research) return [];

    const insights = research.key_insights.length
      ? research.key_insights
      : ['Identify your unique signal before scaling.'];
    const questions = research.discussion_points.length
      ? research.discussion_points
      : ['What is your defensible founder edge?'];

    const a = insights[0];
    const b = insights[1] || insights[0];
    const c = questions[0];
    const d = questions[1] || questions[0];
    const e = insights[2] || insights[insights.length - 1] || a;
    const f = questions[questions.length - 1] || c;

    const titleSeed = (research.title || 'this topic').split(/[—:]/)[0].trim();

    // 4 distinct lenses on the same research. Each carries its own
    // sessionArc / talkingPoints / whyThisMatters so the outline page
    // and voice agent receive angle-specific context, not raw research.
    const base: AngleOption[] = [
      {
        id: 'angle-1',
        title: research.title,
        summary: research.deep_context,
        quote: `"${a}"`,
        tags: ['Strategy', 'Narrative'],
        match: '94%',
        trending: true,
        sessionArc: research.deep_context,
        talkingPoints: questions,
        whyThisMatters: insights.join('. '),
      },
      {
        id: 'angle-2',
        title: a.slice(0, 72),
        summary: b,
        quote: `"${questions[0] || a}"`,
        tags: ['Signal', 'Positioning'],
        match: '89%',
        sessionArc: `Signal-driven framing: ${b}\n\n${a}`,
        talkingPoints: insights.length >= 3 ? insights : questions,
        whyThisMatters: `${b} ${a}`.trim(),
      },
      {
        id: 'angle-3',
        title: c.slice(0, 72),
        summary: d,
        quote: `"${questions[2] || b}"`,
        tags: ['Execution', 'Framework'],
        match: '82%',
        sessionArc: `Practical execution focus: ${d}\n\n${c}`,
        talkingPoints: questions,
        whyThisMatters: questions.slice(0, 3).join('. '),
      },
      {
        id: 'angle-4',
        title: `What Most Founders Get Wrong About ${titleSeed.slice(0, 40)}`,
        summary: e,
        quote: `"${f}"`,
        tags: ['Contrarian', 'Counter-narrative'],
        match: '78%',
        sessionArc: `Counter-narrative — challenging the consensus: ${e}`,
        talkingPoints: [...questions].reverse(),
        whyThisMatters: insights.slice().reverse().join('. '),
      },
    ];
    // Append the user-generated 5th card if present.
    return generatedAngle ? [...base, generatedAngle] : base;
  }, [research, generatedAngle]);

  const selectedOption = options.find((o) => o.id === selectedId) ?? options[0];

  // Synthesize a custom 5th angle from the user's free-form input. Calls
  // the LLM-backed /api/refine-angle endpoint, appends the result as a
  // new card, and auto-selects it WITHOUT navigating away.
  const handleGenerateAngle = async () => {
    const input = customAngle.trim();
    if (!input || !research || isGeneratingAngle) return;
    setIsGeneratingAngle(true);
    setAngleGenError(null);
    try {
      const res = await fetch('/api/refine-angle', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({
          user_input: input,
          research_context: {
            title: research.title,
            deep_context: research.deep_context,
            key_insights: research.key_insights,
            discussion_points: research.discussion_points,
          },
          selected_angle: selectedOption
            ? { title: selectedOption.title, summary: selectedOption.summary }
            : null,
        }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        setAngleGenError(body?.detail || `Generation failed (${res.status})`);
        return;
      }
      const data = await res.json();
      const angle = data?.angle;
      if (!angle?.title) {
        setAngleGenError('Empty angle returned. Try again.');
        return;
      }
      const summary: string = angle.summary || '';
      const newAngle: AngleOption = {
        id: 'angle-custom-generated',
        title: angle.title,
        summary,
        quote: angle.quote || `"${input}"`,
        tags: Array.isArray(angle.tags) ? angle.tags : ['Custom'],
        match: angle.match || 'Custom',
        trending: false,
        sessionArc: summary || research.deep_context,
        talkingPoints: research.discussion_points.length
          ? research.discussion_points
          : research.key_insights,
        whyThisMatters: summary || research.key_insights.join('. '),
      };
      setGeneratedAngle(newAngle);
      setSelectedId(newAngle.id);
      // Persist so back-nav from /interview/new → /discover/trending
      // rehydrates the 5th card and keeps it selected.
      try {
        sessionStorage.setItem('generated-angle', JSON.stringify(newAngle));
        sessionStorage.setItem('selected-angle-id', newAngle.id);
      } catch { /* quota or serialization — non-fatal */ }
      // Clear the input so user knows it landed; they can type again to regenerate.
      setCustomAngle('');
    } catch {
      setAngleGenError('Generation failed. Try again.');
    } finally {
      setIsGeneratingAngle(false);
    }
  };

  const handleContinue = () => {
    if (!research) return;
    const finalAngle: AngleOption = customAngle.trim()
      ? {
          id: 'custom',
          title: customAngle.trim(),
          summary: research.deep_context,
          quote: `"${research.key_insights[0] || customAngle}"`,
          tags: ['Custom'],
          match: 'User',
          sessionArc: research.deep_context,
          talkingPoints: research.discussion_points.length
            ? research.discussion_points
            : research.key_insights,
          whyThisMatters: research.key_insights.join('. '),
        }
      : selectedOption;
    if (!finalAngle) return;
    sessionStorage.setItem('selected-topics', JSON.stringify([makeTopicPayload(finalAngle)]));
    // research-context stores RAW research (never mutated). Back-nav to
    // /discover/trending must rebuild angles from clean data, otherwise
    // the displayed titles/summaries drift on each round-trip.
    sessionStorage.setItem('research-context', JSON.stringify(research));
    // Stamp which keywords this research is tied to. Used on back-nav to
    // detect stale cache when the user changes keywords.
    sessionStorage.setItem('research-context-keywords', keywords);
    sessionStorage.setItem('selected-angle-id', finalAngle.id);
    // Full angle is the source of truth for /interview/new and the agent.
    sessionStorage.setItem('selected-angle', JSON.stringify(finalAngle));
    router.push('/interview/new');
  };

  const currentStep = isLoading ? 2 : 3;

  return (
    <div className="screen-frame min-h-screen px-4 py-6 md:px-8">

      {/* Step progress */}
      <nav className="mb-8 flex items-center justify-center">
        <div className="flex items-center">
          {STEPS.map((step, i) => {
            const active = step.id === currentStep;
            const done = step.id < currentStep;
            return (
              <div key={step.id} className="flex items-center">
                <div className="flex flex-col items-center gap-1.5">
                  <div
                    className="flex h-7 w-7 items-center justify-center rounded-full text-[11px] font-bold transition-all"
                    style={
                      active
                        ? { background: 'var(--accent)', color: '#fff', boxShadow: '0 0 14px rgba(233,83,53,0.4)' }
                        : done
                        ? { background: 'rgba(16,185,129,0.15)', color: '#10b981', border: '1px solid rgba(16,185,129,0.35)' }
                        : { background: 'var(--surface-raised)', color: 'var(--text-secondary)', border: '1px solid var(--border-default)' }
                    }
                  >
                    {done ? <span className="material-symbols-outlined text-[13px]">check</span> : step.id}
                  </div>
                  <span className="text-[10px] font-bold uppercase tracking-[0.08em]" style={{ color: active ? 'var(--accent)' : done ? '#10b981' : 'var(--text-secondary)' }}>
                    {step.label}
                  </span>
                </div>
                {i < STEPS.length - 1 && (
                  <div className="mx-2.5 mb-4 h-px w-10 md:w-14" style={{ background: done ? 'rgba(16,185,129,0.4)' : 'var(--border-default)' }} />
                )}
              </div>
            );
          })}
        </div>
      </nav>

      <div className="mx-auto max-w-4xl">

        {/* ── Research loading state ── */}
        {isLoading && (
          <div className="mx-auto max-w-xl">
            <div className="mb-6 text-center">
              <div className="mb-4 inline-flex h-14 w-14 items-center justify-center rounded-full" style={{ background: 'rgba(233,83,53,0.1)', border: '1px solid rgba(233,83,53,0.2)' }}>
                <span className="material-symbols-outlined animate-pulse text-[28px] text-[var(--accent)]">travel_explore</span>
              </div>
              <h1 className="text-[22px] font-bold text-primary">Finding your best angles…</h1>
              <p className="mt-1 text-[13px] text-[var(--text-secondary)]">Real research. Not a spinner.</p>
            </div>

            <div className="mb-6 overflow-hidden rounded-2xl" style={{ background: 'var(--surface)', border: '1px solid var(--border-default)' }}>

              {/* ── Step 0: dynamic platform scanning ── */}
              <div
                className="flex items-center gap-3 px-5 py-3.5 transition-all"
                style={{
                  borderBottom: '1px solid var(--border-default)',
                  background: researchStep === 0 ? 'rgba(233,83,53,0.06)' : 'transparent',
                }}
              >
                {researchStep > 0 ? (
                  <span className="material-symbols-outlined text-[16px] shrink-0 text-[#10b981]" style={{ fontVariationSettings: "'FILL' 1" }}>check_circle</span>
                ) : (
                  <span className="h-3 w-3 shrink-0 animate-spin rounded-full border-2 border-[var(--accent)] border-t-transparent" />
                )}
                <p className="text-[12px]" style={{ color: 'var(--text-primary)' }}>
                  Scanning{' '}
                  <span
                    className="font-bold transition-opacity duration-200"
                    style={{
                      color: researchStep > 0 ? 'var(--text-primary)' : 'var(--accent)',
                      opacity: platformFade ? 0 : 1,
                    }}
                  >
                    {researchStep > 0 ? pickedSources[pickedSources.length - 1] : pickedSources[platformIdx]}
                  </span>
                  {' '}for trending conversations...
                </p>
              </div>

              {/* ── Steps 1-3: static ── */}
              {STATIC_STEPS.map((label, i) => {
                const stepIdx = i + 1; // maps to researchStep 1, 2, 3
                const done = researchStep > stepIdx;
                const active = researchStep === stepIdx;
                return (
                  <div
                    key={i}
                    className="flex items-center gap-3 px-5 py-3.5 transition-all"
                    style={{
                      borderBottom: i < STATIC_STEPS.length - 1 ? '1px solid var(--border-default)' : 'none',
                      background: active ? 'rgba(233,83,53,0.06)' : 'transparent',
                    }}
                  >
                    {done ? (
                      <span className="material-symbols-outlined text-[16px] shrink-0 text-[#10b981]" style={{ fontVariationSettings: "'FILL' 1" }}>check_circle</span>
                    ) : active ? (
                      <span className="h-3 w-3 shrink-0 animate-spin rounded-full border-2 border-[var(--accent)] border-t-transparent" />
                    ) : (
                      <span className="h-3 w-3 shrink-0 rounded-full" style={{ background: 'var(--border-default)' }} />
                    )}
                    <p className="text-[12px]" style={{ color: done || active ? 'var(--text-primary)' : 'var(--text-secondary)' }}>
                      {label}
                    </p>
                  </div>
                );
              })}
            </div>

            <div className="rounded-xl px-4 py-3 text-center" style={{ background: 'var(--surface-raised)' }}>
              <p className="text-[11px] text-[var(--text-secondary)]">Estimated: ~45 seconds</p>
              <div className="mt-2 h-1 w-full rounded-full" style={{ background: 'var(--border-default)' }}>
                <div
                  className="h-1 rounded-full transition-all duration-700"
                  style={{
                    width: researchStep === 0
                      ? `${((platformIdx + 1) / pickedSources.length) * 25}%`
                      : `${25 + (researchStep / 3) * 70}%`,
                    background: 'var(--accent)',
                  }}
                />
              </div>
            </div>
          </div>
        )}

        {/* ── Error state ── */}
        {!isLoading && error && (
          <div className="mx-auto max-w-md text-center">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full" style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)' }}>
              <span className="material-symbols-outlined text-[24px] text-[var(--danger)]">error</span>
            </div>
            <h2 className="text-[18px] font-bold text-primary">Research Agent Failed</h2>
            <p className="mt-2 text-[13px] text-[var(--text-secondary)]">{error.message}</p>
            <button
              onClick={() => refetch()}
              className="accent-gradient mt-5 inline-flex items-center gap-2 rounded-xl px-6 py-3 text-[13px] font-bold text-white"
            >
              <span className="material-symbols-outlined text-[16px]">refresh</span>
              Retry
            </button>
          </div>
        )}

        {/* ── Angle selection ── */}
        {!isLoading && !error && research && (
          <>
            <div className="mb-3 flex items-end justify-between gap-3">
              <div>
                <h1 className="text-[20px] font-extrabold tracking-tight text-primary">Choose Your Angle</h1>
                <p className="mt-0.5 text-[12px] text-[var(--text-secondary)]">Select one — the AI host will guide your session around it.</p>
              </div>
              <div className="flex items-center gap-3 shrink-0">
                <button
                  onClick={() => router.push('/discover')}
                  className="text-[12px] font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
                >
                  ← Back
                </button>
                <button
                  onClick={handleContinue}
                  className="accent-gradient inline-flex items-center gap-1.5 rounded-xl px-4 py-2 text-[12px] font-bold text-white shadow-[0_4px_16px_rgba(233,83,53,0.3)] transition-all hover:scale-[1.02] active:scale-[0.98]"
                >
                  Build My Outline
                  <span className="material-symbols-outlined text-[14px]">auto_awesome</span>
                </button>
              </div>
            </div>

            <div className="mb-3 grid grid-cols-1 gap-2.5 sm:grid-cols-2">
              {options.map((option) => {
                const active = option.id === selectedId;
                return (
                  <button
                    key={option.id}
                    type="button"
                    onClick={() => {
                      setSelectedId(option.id);
                      setCustomAngle('');
                      try { sessionStorage.setItem('selected-angle-id', option.id); } catch {}
                    }}
                    className="flex flex-col items-start overflow-hidden rounded-xl p-4 text-left transition-all"
                    style={{
                      background: active ? 'rgba(233,83,53,0.07)' : 'var(--surface)',
                      border: `1.5px solid ${active ? 'var(--accent)' : 'var(--border-default)'}`,
                      boxShadow: active ? '0 0 0 3px rgba(233,83,53,0.08)' : 'none',
                    }}
                  >
                    {/* Tags row */}
                    <div className="mb-2.5 flex flex-wrap items-center gap-1">
                      {option.trending && (
                        <span className="rounded-full px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider text-black" style={{ background: '#f59e0b' }}>
                          Trending
                        </span>
                      )}
                      <span className="rounded-full px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider" style={{ background: 'rgba(99,102,241,0.15)', color: '#818cf8', border: '1px solid rgba(99,102,241,0.25)' }}>
                        {option.match} match
                      </span>
                      {option.tags.map((t) => (
                        <span key={t} className="rounded-full px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wider" style={{ background: 'var(--surface-raised)', color: 'var(--text-secondary)' }}>
                          {t}
                        </span>
                      ))}
                      {active && (
                        <span className="flex items-center gap-0.5 rounded-full px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider" style={{ background: 'rgba(233,83,53,0.15)', color: 'var(--accent)' }}>
                          <span className="material-symbols-outlined text-[10px]" style={{ fontVariationSettings: "'FILL' 1" }}>check_circle</span>
                          Selected
                        </span>
                      )}
                    </div>

                    {/* Title — max 2 lines */}
                    <h3
                      className="mb-2 w-full text-[13px] font-bold leading-snug"
                      style={{
                        color: active ? 'var(--accent)' : 'var(--text-primary)',
                        display: '-webkit-box',
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical',
                        overflow: 'hidden',
                      }}
                    >
                      {option.title}
                    </h3>

                    {/* Summary — max 3 lines */}
                    <p
                      className="mb-2.5 w-full text-[12px] leading-relaxed text-[var(--text-secondary)]"
                      style={{
                        display: '-webkit-box',
                        WebkitLineClamp: 3,
                        WebkitBoxOrient: 'vertical',
                        overflow: 'hidden',
                      }}
                    >
                      {option.summary}
                    </p>

                    {/* Quote — 1 line only */}
                    <p
                      className="mt-auto w-full rounded-lg px-3 py-2 text-[11px] italic text-[var(--text-secondary)]"
                      style={{
                        background: 'rgba(255,255,255,0.04)',
                        border: '1px solid rgba(255,255,255,0.06)',
                        overflow: 'hidden',
                        whiteSpace: 'nowrap',
                        textOverflow: 'ellipsis',
                      }}
                    >
                      {option.quote}
                    </p>
                  </button>
                );
              })}
            </div>

            {/* Custom angle — typing reveals an inline ✨ Generate button.
                Click sends user_input + research + selected angle to Claude
                Sonnet 4.6, which returns a refined 5th-card angle. The card
                is appended to the grid above and auto-selected. */}
            <div
              className="mb-3 flex items-center gap-3 rounded-xl px-4 py-3 transition-all"
              style={{
                background: 'var(--surface)',
                border: `1.5px solid var(--border-default)`,
              }}
            >
              <span className="material-symbols-outlined shrink-0 text-[16px]" style={{ color: 'var(--text-secondary)' }}>edit</span>
              <input
                value={customAngle}
                onChange={(e) => {
                  setCustomAngle(e.target.value);
                  setAngleGenError(null);
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && customAngle.trim() && !isGeneratingAngle) {
                    e.preventDefault();
                    void handleGenerateAngle();
                  }
                }}
                placeholder="Or type your own angle — we'll synthesize a 5th option"
                className="flex-1 bg-transparent text-[12px] text-[var(--text-primary)] outline-none placeholder:text-[var(--text-secondary)]"
                disabled={isGeneratingAngle}
                maxLength={500}
              />
              {/* Generate button — only visible when text is entered. */}
              {customAngle.trim() && (
                <button
                  type="button"
                  onClick={() => void handleGenerateAngle()}
                  disabled={isGeneratingAngle}
                  className="flex shrink-0 items-center gap-1.5 rounded-lg px-3 py-1.5 text-[11px] font-bold text-white transition-all hover:scale-[1.02] disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:scale-100"
                  style={{ background: 'var(--accent)', boxShadow: '0 2px 8px rgba(233,83,53,0.30)' }}
                  aria-label="Generate custom angle"
                >
                  {isGeneratingAngle ? (
                    <>
                      <span className="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" />
                      Generating
                    </>
                  ) : (
                    <>
                      <span className="material-symbols-outlined text-[14px]" style={{ fontVariationSettings: "'FILL' 1" }}>auto_awesome</span>
                      Generate
                    </>
                  )}
                </button>
              )}
            </div>
            {angleGenError && (
              <p className="mb-3 text-[11px] text-[var(--danger)]">{angleGenError}</p>
            )}
          </>
        )}
      </div>
    </div>
  );
}
