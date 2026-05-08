# Ladder Flow — Design System

## Product Identity

Ladder Flow is a voice-first content engine for founders and executives.
The design language is "Calm Intelligence" — a premium dark studio experience.
Think Notion meets a professional podcast booth. Every element earns its place.
No decorative noise. Precision over flair. Dark, focused, sharp.

Brand signature color: #E95335 (Ladder AI coral-orange). This is the ONLY accent color.
No purple. No indigo. No blue. Orange is the identity.

---

## Color Palette

### Core Colors

| Token | Hex | Usage |
|----------------|--------------------------|---------------------------------------------|
| background | #0F0F0F | App background, page canvas |
| surface | #1A1A1A | Cards, panels, sidebars, modals |
| surface-raised | #242424 | Hover states, nested cards, dropdowns |
| border-subtle | rgba(255,255,255,0.06) | Dividers, card borders (default) |
| border-default | rgba(255,255,255,0.10) | Input borders, active card borders |

### Accent — Ladder AI Signature Orange

| Token | Hex | Usage |
|-------------|--------------------------|---------------------------------------------|
| accent | #E95335 | ALL CTAs, active nav, selected states |
| accent-dim | #C94020 | Hover state on accent buttons |
| accent-light | #EF826C | Light variant, icon tints, soft highlights |
| accent-glow | rgba(233,83,53,0.15) | Card glow on hover, focus rings |

### Text

| Token | Hex | Usage |
|----------------|----------|----------------------------------------------|
| text-primary | #F5F5F5 | Headlines, body copy, labels |
| text-secondary | #9CA3AF | Subtext, placeholders, timestamps, hints |

### Semantic

| Token | Hex | Usage |
|---------|----------|-----------------------------------------------|
| success | #10B981 | Published state, confirmed, completed |
| warning | #F59E0B | Tier B memory items, draft state, caution |
| error | #EF4444 | Delete actions, error messages, danger zone |

### Signal / Category Colors

| Type | Hex | Usage |
|-----------|----------|-----------------------------------|
| Framework | #E95335 | Orange — structured thinking |
| Opinion | #DB2777 | Pink — hot takes, contrarian |
| Story | #F59E0B | Amber — personal narratives |
| Proof | #10B981 | Green — metrics, case studies |

### Gradient Pairs (stat cards only)

| Card | Gradient |
|-----------|--------------------------------|
| Primary | #E95335 → #C94020 |
| Secondary | #F97316 → #EF826C |
| Tertiary | #0D9488 → #06B6D4 |
| Tour 1 | #E95335 → #C94020 → #0F0F0F |
| Tour 2 | #F97316 → #EF826C → #0F0F0F |
| Tour 3 | #0D9488 → #06B6D4 → #0F0F0F |
| Tour 4 | #F59E0B → #EF4444 → #0F0F0F |

---

## Typography

### Font Families

| Role | Font | Usage |
|-----------|----------------|------------------------------------------------|
| Primary | Inter | All UI text — headings, body, labels, buttons |
| Monospace | JetBrains Mono | Transcripts, timers, chip input, code |

### Type Scale

| Name | Size | Weight | Color | Usage |
|-------------|-------|--------|----------|--------------------------------|
| Display | 36px | 700 | #F5F5F5 | Hero titles, tour screens |
| Heading 1 | 28px | 700 | #F5F5F5 | Page titles |
| Heading 2 | 22px | 700 | #F5F5F5 | Section headers, card titles |
| Heading 3 | 18px | 600 | #F5F5F5 | Sub-sections |
| Body Large | 16px | 400 | #F5F5F5 | Post content, descriptions |
| Body | 14px | 400 | #F5F5F5 | Default UI copy |
| Body Small | 13px | 400 | #9CA3AF | Supporting text, timestamps |
| Label | 11px | 500 | #9CA3AF | Uppercase section labels |
| Mono | 13px | 400 | #F5F5F5 | Transcripts, timers, chips |

### Label Rule
All section labels use: 11px · Inter 500 · #9CA3AF · letter-spacing 0.08em · UPPERCASE

---

## Spacing

Base unit: 8px

| Token | Value | Usage |
|-------|-------|---------------------------------|
| xs | 4px | Icon gaps, tight inline gaps |
| sm | 8px | Inner chip padding |
| md | 16px | Standard element padding |
| lg | 24px | Card inner padding |
| xl | 32px | Section padding |
| 2xl | 48px | Page section gaps |
| 3xl | 64px | Hero spacing |
| 4xl | 96px | Full-section vertical padding |

---

## Border Radius

| Token | Value | Usage |
|-------|--------|------------------------------------------|
| sm | 6px | Badges, small chips, tag pills |
| md | 10px | Input fields, buttons |
| lg | 14px | Cards, panels, dropdowns |
| xl | 20px | Large cards, modals, sidebars |
| full | 9999px | Pill buttons, avatar circles, tab pills |

---

## Shadows & Elevation

| Level | Value |
|-------------|----------------------------------------------------|
| subtle | 0 1px 3px rgba(0,0,0,0.40) |
| default | 0 4px 16px rgba(0,0,0,0.50) |
| raised | 0 8px 32px rgba(0,0,0,0.60) |
| glow | 0 0 24px rgba(233,83,53,0.20) |
| glow-strong | 0 0 40px rgba(233,83,53,0.35) |

---

## Glassmorphism

Use on: floating panels, transcript panel, control dock, paused overlays.

background: rgba(26, 26, 26, 0.85)
backdrop-filter: blur(20px)
border: 1px solid rgba(255, 255, 255, 0.08)
box-shadow: 0 8px 32px rgba(0, 0, 0, 0.50)

---

## Components

### Card — Default

background: #1A1A1A
border: 1px solid rgba(255,255,255,0.06)
border-radius: 14px
padding: 24px
box-shadow: 0 4px 16px rgba(0,0,0,0.50)

Hover state:
background: #242424
border-color: rgba(255,255,255,0.10)
transform: translateY(-2px)
transition: all 200ms ease-out

Selected/active state:
border: 2px solid #E95335
background: rgba(233,83,53,0.08)
box-shadow: 0 0 24px rgba(233,83,53,0.20)

Gradient stat card:
background: [gradient pair — see Gradient Pairs table]
border-radius: 20px
padding: 28px
color: #FFFFFF

### Button — Primary

background: linear-gradient(135deg, #E95335, #C94020)
color: #FFFFFF
font: Inter 600, 14px
border-radius: 10px
padding: 14px 24px
box-shadow: 0 4px 16px rgba(233,83,53,0.30)

Hover:
background: #C94020
transform: translateY(-1px)

Disabled:
background: #242424
color: #9CA3AF
box-shadow: none

### Button — Secondary

background: transparent
border: 1px solid rgba(255,255,255,0.10)
color: #F5F5F5
border-radius: 10px
padding: 14px 24px

Hover:
background: #242424

### Button — Pill (CTA)

border-radius: 9999px
padding: 12px 28px

### Button — Danger

background: transparent
border: 1px solid #EF4444
color: #EF4444
border-radius: 10px

### Input — Text / Textarea

background: #0F0F0F
border: 1px solid rgba(255,255,255,0.10)
border-radius: 10px
color: #F5F5F5
font: Inter 400, 14px
padding: 12px 16px
placeholder: #9CA3AF

Focus:
border-color: #E95335
box-shadow: 0 0 0 3px rgba(233,83,53,0.15)
outline: none

### Chip — Default

background: #242424
border: 1px solid rgba(255,255,255,0.10)
color: #9CA3AF
font: Inter 500, 12px
border-radius: 9999px
padding: 4px 12px

Selected:
background: #E95335
border-color: #E95335
color: #FFFFFF

### Chip — Category

Framework: background #E95335 · color #FFFFFF
Opinion: background #DB2777 · color #FFFFFF
Story: background #F59E0B · color #111111
Proof: background #10B981 · color #FFFFFF

### Badge — Status

Complete: background #10B981 · color #FFFFFF
Draft: background #F59E0B · color #111111
Published: background #E95335 · color #FFFFFF
Private: background #242424 · color #9CA3AF · border rgba(255,255,255,0.10)

### Badge — Trust Tier

Tier A: solid fill #10B981
Tier B: solid fill #F59E0B
Tier C: solid fill #9CA3AF

### Navigation — Pill Tabs

Container: background #1A1A1A · border-radius 9999px · padding 4px
Active tab: background #E95335 · color #FFFFFF · border-radius 9999px
Inactive tab: background transparent · color #9CA3AF
Font: Inter 500, 14px

### Navigation — Sidebar Item

Default: background transparent · color #9CA3AF · padding 12px 16px
Active: border-left 3px solid #E95335 · background #242424 · color #F5F5F5
Hover: background #242424
Icon active: color #E95335

### Waveform Bars

Shape: pill (fully rounded top and bottom) · width 6px · gap 4px
Count: 32 bars in a horizontal row

AI speaking:
fill: linear-gradient(to top, #C94020, #E95335)
height: 40%–90% animated
glow: box-shadow 0 0 12px rgba(233,83,53,0.50)

User speaking:
fill: linear-gradient(to top, #059669, #10B981)
height: 60%–100% higher amplitude

Idle:
fill: rgba(255,255,255,0.12)
height: 20%–40% slow breathing 2s ease-in-out loop

Reflection: mirrored bars below · 20% opacity · blur(3px)
Floor glow: radial-gradient rgba(233,83,53,0.15) beneath bars

### Progress Steps (session creation)

Active: background #E95335 · color #FFFFFF · border-radius 9999px
Completed: background #10B981 · color #FFFFFF · checkmark icon
Upcoming: background #242424 · color #9CA3AF · border-radius 9999px
Connector: 1px solid rgba(255,255,255,0.10)
Font: Inter 500, 13px

### Modal / Overlay

Overlay: background rgba(0,0,0,0.70) · backdrop-filter blur(4px)
Modal card: background #1A1A1A · border 1px solid rgba(255,255,255,0.10)
border-radius 20px · padding 40px
box-shadow 0 24px 64px rgba(0,0,0,0.70)

---

## Layout Patterns

### Sidebar Layout
Used on: Dashboard, Sessions, Digital Brain, Settings

sidebar-width: 260px (collapsed: 68px)
sidebar-background: #1A1A1A
sidebar-border: 1px solid rgba(255,255,255,0.06) on the right edge
main-background: #0F0F0F

### Centered Card Layout
Used on: Onboarding, Keyword Input, Outline Approval, Login, Signup

max-width: 600px–680px
margin: auto horizontal
page-bg: #0F0F0F
card-bg: #1A1A1A

### Full-Screen Layout
Used on: Interview Session only

background: #0F0F0F
No sidebar. No navigation. Nothing competes with the waveform.

---

## Animation

| Motion | Spec |
|----------------|--------------------------------------------------------|
| Card entrance | translateY(16px)→0 + opacity 0→1 · 300ms ease-out |
| Stagger | 60ms delay between sibling cards |
| Hover lift | translateY(-2px) · 200ms ease-out |
| Button press | scale(0.98) · 100ms |
| Panel slide-in | translateX(100%)→0 · 280ms ease-out |
| Skeleton pulse | opacity 0.4→0.8→0.4 · 1.5s loop |
| Waveform | spring height animation · 80ms per frame |
| Glow pulse | box-shadow grow/shrink · 2s ease-in-out loop |
| Dot indicator | scale(1)→scale(1.4)→scale(1) on active · 200ms |

---

## Screen Inventory

| Screen | Layout | Key Visual Notes |
|-------------------------|---------------|-----------------------------------------------|
| Landing Page | Full-width | Hero, feature strip, signup CTA |
| Login / Signup | Split-screen | Left: dark brand panel · Right: form card |
| Product Tour (x4) | Full-screen | One gradient card per screen + motion graphic |
| Onboarding (3 sections) | Centered card | Progress steps + form fields + chip inputs |
| Dashboard | Sidebar | Gradient stat cards + bar chart + recent list |
| Keyword Input | Centered card | Tag chip input + suggestions |
| Research Processing | Centered card | Animated progress steps + loading bar |
| Trending Angles | Sidebar | 2-col angle card grid + custom input |
| Outline Approval | Centered card | Synopsis + bullet topics + duration badge |
| Interview Session | Full-screen | Waveform hero + minimal bottom dock |
| Post-Session Debrief | Centered | Gradient stat cards + signal chips + rating |
| Output Review | Two-panel | Signal sidebar (30%) + post cards (70%) |
| Digital Brain | Sidebar | Filter chips + masonry memory card grid |
| Session History | Sidebar | Searchable table with avatar rows |
| Settings / Profile | Two-panel | Settings nav (240px) + form content area |

---

## Design Rules

1. Background is always #0F0F0F. Never use white or light backgrounds.
2. #E95335 coral-orange is the ONLY accent color. No purple. No indigo. No blue.
3. Gradients only on stat cards and tour screens. Never on page backgrounds.
4. Glassmorphism only on floating elements — control dock, transcript panel, overlays.
5. During the interview session: no sidebar, no nav, no chrome. The session is sacred.
6. The waveform is the hero of the interview screen. Give it maximum visual weight.
7. Every memory card shows source, date, type, and trust tier — no vague UI.
8. Spacing is generous. Default comfortable padding is 40px inside cards.
9. JetBrains Mono for all transcripts, timers, session IDs, and chip input text.
10. Semantic colors (success, warning, error) are for meaning only — not decoration.