# Quick Reference: Component Patterns from PNG Samples

This document provides copy-paste ready code patterns extracted from the HTML samples.

## ⚠️ IMPORTANT: Mockup vs Real API

**The PNG samples show a mockup design that differs from the actual API response.**

### What the Mockup Shows (Screen 2):
- Engagement metrics (likes, comments, shares)
- Category badges (#Productivity, #AI, etc.)
- Trending percentage (+12% this week)

### What the Real API Provides:
```typescript
{
  rank: number;              // 1-5
  topic_title: string;       // Main title
  why_this_matters: string;  // Use as card description
  global_context: string;    // Show on expand
  key_questions: string[];   // 5 questions, show on expand
  source_tweet_id: string;
}
```

**When building Topic Cards**: Use the real API structure (rank, title, why_this_matters). See `API_INTEGRATION.md` for full details.

---

## Table of Contents
1. [Waveform Visualizations](#waveform-visualizations)
2. [Status Badges](#status-badges)
3. [Card States](#card-states)
4. [Loading Skeletons](#loading-skeletons)
5. [Icon Containers](#icon-containers)
6. [Navigation Components](#navigation-components)
7. [Form Elements](#form-elements)

---

## Waveform Visualizations

### Large Center Waveform (Screen 3 - Live Interview)
```tsx
<div className="relative flex items-center justify-center gap-1.5 h-32">
  {/* Ambient glow background */}
  <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2
                  w-64 h-64 bg-primary/20 rounded-full blur-[60px] animate-pulse-slow" />

  {/* Wave bars - randomize heights for visual variety */}
  <div className="wave-bar h-8 opacity-40" />
  <div className="wave-bar h-12 opacity-60" />
  <div className="wave-bar h-6 opacity-40" />
  <div className="wave-bar h-16 opacity-80" />
  <div className="wave-bar h-24" />
  <div className="wave-bar h-10 opacity-70" />
  <div className="wave-bar h-20 opacity-90" />
  <div className="wave-bar h-28 bg-primary" />
  <div className="wave-bar h-14 opacity-70" />
  <div className="wave-bar h-32 bg-primary" />
  <div className="wave-bar h-20 opacity-90" />
  <div className="wave-bar h-10 opacity-60" />
  <div className="wave-bar h-24" />
  <div className="wave-bar h-8 opacity-50" />
  <div className="wave-bar h-16 opacity-80" />
  <div className="wave-bar h-6 opacity-40" />
  <div className="wave-bar h-12 opacity-60" />
  <div className="wave-bar h-4 opacity-30" />
</div>

{/* CSS for wave-bar */}
<style jsx>{`
  .wave-bar {
    width: 6px;
    border-radius: 9999px;
    background-color: #135bec;
    transition: height 0.2s ease;
  }
`}</style>
```

### Mini Waveform (Screen 4 - Audio Player)
```tsx
<div className="h-12 w-full flex items-center gap-0.5 opacity-60">
  <div className="w-1 bg-slate-300 dark:bg-slate-600 h-4 rounded-full" />
  <div className="w-1 bg-slate-300 dark:bg-slate-600 h-6 rounded-full" />
  <div className="w-1 bg-slate-300 dark:bg-slate-600 h-3 rounded-full" />
  <div className="w-1 bg-primary h-8 rounded-full" />
  <div className="w-1 bg-primary h-10 rounded-full" />
  <div className="w-1 bg-primary h-6 rounded-full" />
  <div className="w-1 bg-primary h-4 rounded-full" />
  <div className="w-1 bg-slate-300 dark:bg-slate-600 h-5 rounded-full" />
  {/* Continue pattern... */}
</div>
```

---

## Status Badges

### Live Connection Badge (Screen 3)
```tsx
<div className="flex items-center gap-1.5">
  {/* Pulsing indicator */}
  <span className="relative flex h-2 w-2">
    <span className="animate-ping absolute inline-flex h-full w-full
                     rounded-full bg-green-400 opacity-75" />
    <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500" />
  </span>
  <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
    Live Connection
  </span>
</div>
```

### Recording Badge (Screen 3)
```tsx
<span className="px-2 py-0.5 rounded-full bg-red-100 dark:bg-red-900/30
               text-red-600 dark:text-red-400 text-[10px] font-bold
               uppercase tracking-wide">
  Recording
</span>
```

### Status Pill Badges (Screen 4)
```tsx
{/* Ready state */}
<span className="px-2 py-0.5 rounded-full bg-green-100 text-green-700
               text-xs font-semibold">
  Ready
</span>

{/* Generating state */}
<div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full
                bg-slate-100 dark:bg-slate-800 text-slate-500
                text-xs font-semibold">
  <span className="block size-2 rounded-full bg-slate-400 animate-pulse" />
  Generating...
</div>
```

### Progress Pill (Screen 3)
```tsx
<div className="flex items-center gap-2 bg-surface-light dark:bg-surface-dark
                border border-slate-200 dark:border-slate-800 rounded-full
                px-4 py-1.5 shadow-sm">
  <span className="text-xs font-semibold text-slate-500 dark:text-slate-400
                   uppercase tracking-wider">
    Question
  </span>
  <span className="text-sm font-bold text-slate-900 dark:text-white">
    2 <span className="text-slate-400 dark:text-slate-600 font-normal">of</span> 6
  </span>
</div>
```

---

## Card States

### Selected Topic Card (Screen 2)
```tsx
<div className="group relative flex cursor-pointer flex-col rounded-xl
                border-2 border-primary bg-white p-6 shadow-glow
                transition-all hover:-translate-y-1 dark:bg-slate-800">

  {/* Selection checkmark */}
  <div className="absolute right-4 top-4">
    <div className="flex size-6 items-center justify-center rounded-full
                    bg-primary text-white shadow-sm">
      <span className="material-symbols-outlined text-[18px] font-bold">check</span>
    </div>
  </div>

  {/* Category icon + badge */}
  <div className="mb-4 flex items-center gap-3">
    <div className="flex size-10 items-center justify-center rounded-lg
                    bg-indigo-50 text-indigo-600 dark:bg-indigo-900/30
                    dark:text-indigo-400">
      <span className="material-symbols-outlined filled">work</span>
    </div>
    <span className="inline-flex items-center rounded-md bg-indigo-50
                     px-2 py-1 text-xs font-medium text-indigo-700
                     ring-1 ring-inset ring-indigo-700/10">
      #Productivity
    </span>
  </div>

  {/* Title and description */}
  <h3 className="mb-2 text-xl font-bold leading-tight text-slate-900
                 dark:text-white">
    The Future of Remote Work
  </h3>
  <p className="mb-6 line-clamp-2 text-sm text-slate-500 dark:text-slate-400">
    Exploring how hybrid models are reshaping corporate culture...
  </p>

  {/* Engagement metrics */}
  <div className="mt-auto flex items-center gap-6 border-t border-slate-100
                  pt-4 dark:border-slate-700">
    <div className="flex items-center gap-1.5 text-sm font-semibold
                    text-slate-700 dark:text-slate-300">
      <span className="material-symbols-outlined text-rose-500 text-[18px] filled">
        favorite
      </span>
      12.5k
    </div>
    <div className="flex items-center gap-1.5 text-sm font-semibold
                    text-slate-700 dark:text-slate-300">
      <span className="material-symbols-outlined text-blue-500 text-[18px] filled">
        chat_bubble
      </span>
      840
    </div>
    <div className="flex items-center gap-1.5 text-sm font-semibold
                    text-slate-700 dark:text-slate-300">
      <span className="material-symbols-outlined text-green-500 text-[18px]">
        share
      </span>
      3.2k
    </div>

    {/* Trending indicator */}
    <div className="ml-auto flex items-center gap-1 text-xs font-medium
                    text-emerald-600 dark:text-emerald-400">
      <span className="material-symbols-outlined text-[16px]">trending_up</span>
      +12% this week
    </div>
  </div>
</div>
```

### Unselected Topic Card (Screen 2)
```tsx
<div className="group relative flex cursor-pointer flex-col rounded-xl
                border border-slate-200 bg-white p-6 shadow-sm
                transition-all hover:-translate-y-1 hover:border-primary/50
                hover:shadow-md dark:border-slate-700 dark:bg-slate-800">

  {/* Empty circle (shows on hover) */}
  <div className="absolute right-4 top-4">
    <div className="flex size-6 items-center justify-center rounded-full
                    border-2 border-slate-300 bg-transparent
                    transition-colors group-hover:border-primary
                    dark:border-slate-600" />
  </div>

  {/* Rest of content same as selected, but with grayscale metrics */}
  <div className="flex items-center gap-1.5 text-sm font-semibold
                  text-slate-700 dark:text-slate-300">
    <span className="material-symbols-outlined text-slate-400 text-[18px]">
      favorite
    </span>
    8.2k
  </div>
</div>
```

---

## Loading Skeletons

### Content Generation Loading (Screen 4)
```tsx
<div className="p-6 space-y-3">
  <div className="h-4 bg-slate-100 dark:bg-slate-800 rounded w-3/4 animate-pulse" />
  <div className="h-4 bg-slate-100 dark:bg-slate-800 rounded w-full animate-pulse" />
  <div className="h-4 bg-slate-100 dark:bg-slate-800 rounded w-5/6 animate-pulse" />
  <div className="h-4 bg-slate-100 dark:bg-slate-800 rounded w-2/3 animate-pulse" />
</div>
```

---

## Icon Containers

### Colored Category Icons
```tsx
{/* Pattern: size-10, rounded-lg, colored bg with transparency */}

{/* Indigo (Work/Productivity) */}
<div className="flex size-10 items-center justify-center rounded-lg
                bg-indigo-50 text-indigo-600 dark:bg-indigo-900/30
                dark:text-indigo-400">
  <span className="material-symbols-outlined filled">work</span>
</div>

{/* Teal (AI/Technology) */}
<div className="flex size-10 items-center justify-center rounded-lg
                bg-teal-50 text-teal-600 dark:bg-teal-900/30
                dark:text-teal-400">
  <span className="material-symbols-outlined filled">smart_toy</span>
</div>

{/* Green (Sustainability) */}
<div className="flex size-10 items-center justify-center rounded-lg
                bg-green-50 text-green-600 dark:bg-green-900/30
                dark:text-green-400">
  <span className="material-symbols-outlined filled">eco</span>
</div>

{/* Orange (Crypto/Finance) */}
<div className="flex size-10 items-center justify-center rounded-lg
                bg-orange-50 text-orange-600 dark:bg-orange-900/30
                dark:text-orange-400">
  <span className="material-symbols-outlined filled">currency_bitcoin</span>
</div>

{/* Pink (Mental Health) */}
<div className="flex size-10 items-center justify-center rounded-lg
                bg-pink-50 text-pink-600 dark:bg-pink-900/30
                dark:text-pink-400">
  <span className="material-symbols-outlined filled">health_and_safety</span>
</div>

{/* Purple (Creator Economy) */}
<div className="flex size-10 items-center justify-center rounded-lg
                bg-purple-50 text-purple-600 dark:bg-purple-900/30
                dark:text-purple-400">
  <span className="material-symbols-outlined filled">movie</span>
</div>
```

### Platform Logos
```tsx
{/* LinkedIn */}
<div className="size-8 rounded bg-[#0077b5] flex items-center justify-center text-white">
  <span className="font-bold text-lg">in</span>
</div>

{/* Twitter/X */}
<div className="size-8 rounded bg-black flex items-center justify-center text-white">
  <span className="font-bold text-lg">X</span>
</div>

{/* Newsletter (generic email) */}
<div className="size-8 rounded bg-orange-500 flex items-center justify-center text-white">
  <span className="material-symbols-outlined text-lg">mail</span>
</div>
```

---

## Navigation Components

### Top Navbar (Consistent Across Screens)
```tsx
<header className="w-full bg-white dark:bg-[#1a2230] border-b
                   border-[#f0f2f4] dark:border-[#2a3441] sticky top-0 z-50">
  <div className="px-4 md:px-10 py-3 flex items-center justify-between
                  mx-auto max-w-7xl">

    {/* Logo */}
    <div className="flex items-center gap-3 text-[#111318] dark:text-white">
      <div className="size-8 rounded-lg bg-primary/10 flex items-center
                      justify-center text-primary">
        <span className="material-symbols-outlined text-2xl">graphic_eq</span>
      </div>
      <h2 className="text-lg font-bold leading-tight tracking-tight">
        LadderFlow
      </h2>
    </div>

    {/* Desktop Navigation */}
    <div className="hidden md:flex flex-1 justify-center gap-8">
      <a className="text-[#616f89] dark:text-[#9ca3af] hover:text-primary
                    text-sm font-medium transition-colors"
         href="#">
        Dashboard
      </a>
      <a className="text-primary text-sm font-bold" href="#">
        Content
      </a>
      <a className="text-[#616f89] dark:text-[#9ca3af] hover:text-primary
                    text-sm font-medium transition-colors"
         href="#">
        Settings
      </a>
    </div>

    {/* Right Actions */}
    <div className="flex items-center gap-4">
      <button className="flex items-center justify-center size-10 rounded-full
                         hover:bg-gray-100 dark:hover:bg-gray-800
                         text-[#616f89] dark:text-[#9ca3af] transition-colors">
        <span className="material-symbols-outlined">notifications</span>
      </button>
      <div className="size-9 rounded-full bg-gray-200 dark:bg-gray-700
                      bg-cover bg-center border-2 border-white
                      dark:border-[#2a3441]"
           style={{backgroundImage: "url('...')"}} />
    </div>
  </div>
</header>
```

### Sidebar Navigation (Screen 5 - Dashboard)
```tsx
<aside className="hidden md:flex flex-col w-64 h-full bg-[#F7F7F8]
                  dark:bg-[#151c2a] border-r border-slate-200
                  dark:border-slate-800">

  {/* Logo */}
  <div className="p-6 flex items-center gap-3">
    <div className="flex items-center justify-center w-8 h-8 rounded-lg
                    bg-primary text-white">
      <span className="material-symbols-outlined text-[20px]">graphic_eq</span>
    </div>
    <h1 className="text-base font-bold tracking-tight text-slate-900
                   dark:text-white">
      LadderFlow
    </h1>
  </div>

  {/* Navigation Items */}
  <nav className="flex-1 px-3 py-2 flex flex-col gap-1">
    {/* Active state */}
    <a className="flex items-center gap-3 px-3 py-2 rounded-lg bg-white
                  dark:bg-slate-800 shadow-sm border border-slate-200/50
                  dark:border-slate-700/50 transition-all"
       href="#">
      <span className="material-symbols-outlined text-[20px] text-primary">
        dashboard
      </span>
      <span className="text-sm font-medium text-slate-900 dark:text-white">
        Dashboard
      </span>
    </a>

    {/* Inactive state */}
    <a className="flex items-center gap-3 px-3 py-2 rounded-lg
                  hover:bg-slate-200/50 dark:hover:bg-slate-800/50
                  transition-colors group"
       href="#">
      <span className="material-symbols-outlined text-[20px] text-slate-500
                       group-hover:text-slate-700 dark:text-slate-400
                       dark:group-hover:text-slate-200">
        folder_open
      </span>
      <span className="text-sm font-medium text-slate-600
                       group-hover:text-slate-900 dark:text-slate-400
                       dark:group-hover:text-slate-200">
        Sessions
      </span>
    </a>
  </nav>

  {/* User Profile */}
  <div className="p-4 border-t border-slate-200 dark:border-slate-800">
    <div className="flex items-center gap-3">
      <div className="w-8 h-8 rounded-full bg-cover bg-center"
           style={{backgroundImage: "url('...')"}} />
      <div className="flex flex-col">
        <p className="text-xs font-semibold text-slate-900 dark:text-white">
          Alex Creator
        </p>
        <p className="text-[10px] text-slate-500 dark:text-slate-400">
          Pro Plan
        </p>
      </div>
    </div>
  </div>
</aside>
```

---

## Form Elements

### Large Keyword Input (Screen 1)
```tsx
<div className="bg-white dark:bg-[#1a2230] rounded-2xl shadow-xl
                shadow-gray-200/50 dark:shadow-black/20 p-2 md:p-3
                border border-gray-100 dark:border-gray-800">
  <div className="relative w-full">
    <label className="sr-only" htmlFor="topic-input">Topic Keywords</label>

    {/* Icon */}
    <div className="absolute top-5 left-5 text-primary pointer-events-none">
      <span className="material-symbols-outlined">edit_note</span>
    </div>

    {/* Textarea */}
    <textarea
      autoFocus
      className="w-full min-h-[200px] bg-transparent border-0 rounded-xl
                 p-5 pl-14 text-lg md:text-xl text-[#111318] dark:text-white
                 placeholder:text-[#94a3b8] dark:placeholder:text-[#64748b]
                 focus:ring-0 resize-none leading-relaxed"
      id="topic-input"
      placeholder="e.g. AI automation, No-code, Remote work culture..."
    />

    {/* Bottom Helper */}
    <div className="px-5 pb-3 flex justify-between items-center border-t
                    border-gray-100 dark:border-gray-800 pt-3 mt-2">
      <span className="text-xs font-medium text-gray-400 dark:text-gray-500
                       uppercase tracking-wider">
        Keywords
      </span>
      <span className="px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded
                       text-xs text-gray-500 dark:text-gray-400 font-medium">
        Comma separated
      </span>
    </div>
  </div>
</div>
```

### Search Input (Screen 2, Screen 5)
```tsx
<div className="relative group w-full sm:w-72">
  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400
                   group-focus-within:text-primary">
    <span className="material-symbols-outlined">search</span>
  </span>
  <input
    className="w-full rounded-xl border-slate-200 bg-white py-3 pl-10 pr-4
               text-sm font-medium shadow-sm transition-all focus:border-primary
               focus:ring-4 focus:ring-primary/10 dark:border-slate-700
               dark:bg-slate-800 dark:text-white dark:placeholder-slate-500"
    placeholder="Search keywords or hashtags..."
    type="text"
  />
</div>
```

---

## Button Patterns

### Primary CTA (Large)
```tsx
<button className="group relative w-full bg-primary hover:bg-blue-700
                   active:bg-blue-800 text-white font-bold text-lg h-14
                   rounded-xl shadow-lg shadow-primary/30 transition-all
                   duration-200 transform hover:-translate-y-0.5
                   flex items-center justify-center gap-2 overflow-hidden">
  <span className="relative z-10">Discover Trending Topics</span>
  <span className="material-symbols-outlined relative z-10 transition-transform
                   group-hover:translate-x-1">
    arrow_forward
  </span>

  {/* Shine effect */}
  <div className="absolute inset-0 -translate-x-full
                  group-hover:animate-[shimmer_1.5s_infinite]
                  bg-gradient-to-r from-transparent via-white/20 to-transparent z-0" />
</button>
```

### Secondary Button (Small)
```tsx
<button className="flex items-center gap-2 px-5 py-2.5 bg-primary text-white
                   rounded-lg font-semibold shadow-lg shadow-primary/20
                   hover:bg-blue-600 transition-all hover:translate-y-[-1px]">
  <span className="material-symbols-outlined text-[20px]">ios_share</span>
  <span>Export All</span>
</button>
```

### Icon Button
```tsx
<button className="p-2 text-slate-400 hover:text-primary hover:bg-slate-50
                   dark:hover:bg-slate-800 rounded-lg transition-colors"
        title="Regenerate">
  <span className="material-symbols-outlined text-[20px]">autorenew</span>
</button>
```

### Chip/Filter Button
```tsx
{/* Active */}
<button className="inline-flex h-9 items-center rounded-full bg-slate-900
                   px-4 text-sm font-medium text-white shadow-md
                   transition-transform hover:-translate-y-0.5
                   dark:bg-white dark:text-slate-900">
  All
</button>

{/* Inactive */}
<button className="inline-flex h-9 items-center rounded-full border
                   border-slate-200 bg-white px-4 text-sm font-medium
                   text-slate-600 shadow-sm transition-all hover:-translate-y-0.5
                   hover:border-primary hover:text-primary dark:border-slate-700
                   dark:bg-slate-800 dark:text-slate-300">
  Technology
</button>
```

---

## Control Dock (Screen 3 - Voice Interview)

```tsx
<div className="fixed bottom-8 left-0 right-0 flex justify-center px-4 z-50">
  <div className="flex items-center gap-3 p-2 rounded-2xl bg-white/90
                  dark:bg-surface-dark/90 backdrop-blur-md shadow-xl
                  border border-slate-200/60 dark:border-slate-700/60">

    {/* Pause Button */}
    <button className="group flex flex-col items-center justify-center
                       size-14 rounded-xl hover:bg-slate-100
                       dark:hover:bg-slate-800 transition-colors
                       text-slate-600 dark:text-slate-400">
      <span className="material-symbols-outlined text-[28px]
                       group-hover:scale-110 transition-transform">
        pause_circle
      </span>
      <span className="text-[10px] font-medium mt-0.5">Pause</span>
    </button>

    {/* Active Mic (Primary) */}
    <button className="relative group flex items-center justify-center
                       size-20 rounded-2xl bg-primary text-white shadow-lg
                       shadow-primary/30 hover:bg-primary/90 transition-all
                       hover:scale-105 active:scale-95">
      <div className="absolute inset-0 rounded-2xl border border-white/20" />

      {/* Pulse ring */}
      <span className="absolute inline-flex h-full w-full rounded-2xl
                       bg-primary opacity-20 animate-ping" />

      <div className="flex flex-col items-center z-10">
        <span className="material-symbols-outlined text-[32px]">mic</span>
        <span className="text-[10px] font-bold mt-0.5 tracking-wide">
          LISTENING
        </span>
      </div>
    </button>

    {/* End Button */}
    <button className="group flex flex-col items-center justify-center
                       size-14 rounded-xl hover:bg-red-50
                       dark:hover:bg-red-900/20 transition-colors
                       text-slate-600 dark:text-slate-400
                       hover:text-red-600 dark:hover:text-red-400">
      <span className="material-symbols-outlined text-[28px]
                       group-hover:scale-110 transition-transform">
        call_end
      </span>
      <span className="text-[10px] font-medium mt-0.5">End</span>
    </button>
  </div>
</div>
```

---

## Notes

- All patterns support dark mode via `dark:` prefix
- Use Material Symbols Outlined font for icons
- Primary color: `#135bec`
- Common transition: `transition-all duration-200`
- Hover lift effect: `hover:-translate-y-1`
- Focus rings: `focus:ring-4 focus:ring-primary/10`

**Brand Name Inconsistency**:
The sample HTML files use different names:
- `Voice2Social` (Screens 1, 4)
- `VoiceViral` (Screen 2)
- `Voice2Content` (Screen 5)

Choose one consistent name for your final implementation (recommend: **LadderFlow** per PRD).
