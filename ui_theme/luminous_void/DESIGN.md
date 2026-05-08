# Design System Strategy: The Luminous Void

## 1. Overview & Creative North Star
The Creative North Star for this design system is **"The Digital Curator."** 

In an era of information density, this system prioritizes "Calm Intelligence." We move away from the rigid, boxed-in layouts of traditional SaaS and toward a high-end editorial experience. The interface should feel like a series of frosted glass panels suspended in a deep, luminous void. 

To achieve this, we break the "template" look through:
*   **Intentional Asymmetry:** Off-center typography and staggered card layouts that mimic a premium magazine.
*   **Luminous Depth:** Using vibrant ambient mesh gradients (`primary` and `secondary`) that glow *behind* glass surfaces, rather than sitting on top of them.
*   **Breathable Metadata:** Using technical monospaced type for data, contrasted against elegant, airy sans-serif headlines.

---

## 2. Colors & Surface Logic

### The Palette
The color system is rooted in `surface_container_lowest` (#0E0E0E) to provide a bottomless sense of depth, with high-energy accents providing the "intelligence" sparks.

*   **Primary (#E95335):** Use for active states and critical path actions.
*   **Secondary (#6366F1):** Reserved for "Voice-First" indicators and AI-processing states.
*   **Tertiary (#6ad4f5):** Used sparingly for highlighting insight keywords.

### The "No-Line" Rule
**Prohibit 1px solid borders for sectioning.** 
Boundaries must be defined solely through background color shifts or tonal transitions. To separate a sidebar from a main feed, transition from `surface` to `surface_container_low`. Structural integrity comes from volume, not lines.

### Glassmorphism & Nesting
This system utilizes a "Physical Layering" model. Treat the UI as stacked sheets of fine glass:
1.  **Level 0 (The Void):** `background` (#0F0F0F).
2.  **Level 1 (The Canvas):** `surface_container_low`.
3.  **Level 2 (The Interactive Panel):** `surface` with `backdrop-filter: blur(24px)`.
4.  **Level 3 (The Floating Card):** `surface_bright` with a 4% `on_surface` ambient shadow.

**Signature Texture:** Main CTAs should never be flat. Use a linear gradient from `primary` to `primary_container` at a 135-degree angle to give the element a physical, tactile soul.

---

## 3. Typography
The typographic voice is a conversation between the human (`Inter`) and the engine (`JetBrains Mono`).

*   **Display & Headlines (Inter):** High-contrast scaling. Use `display-lg` for hero statements with negative letter-spacing (-0.02em) to create an authoritative, editorial feel.
*   **Body (Inter):** Keep `body-md` as the workhorse. Ensure line-height is generous (1.6) to maintain the "Calm Intelligence" vibe.
*   **Metadata & Transcripts (JetBrains Mono):** All voice-to-text output and technical timestamps must use this monospaced face. It signals to the user that they are looking at "raw engine data" vs. "curated content."

---

## 4. Elevation & Depth

### The Layering Principle
Depth is achieved by "stacking" surface-container tiers. Place a `surface_container_highest` card on a `surface_container_low` background. This creates a soft, natural lift that feels sophisticated rather than "designed."

### Ambient Shadows
Avoid black shadows. Floating elements must use **Ambient Shadows**:
*   **Blur:** 40px to 80px.
*   **Color:** `rgba(0, 0, 0, 0.4)` combined with a secondary shadow of `primary` at 5% opacity to simulate light refracting through glass.

### The "Ghost Border" & Top Edge Highlight
For accessibility on glass panels, use a **Top Edge Highlight** instead of a full border. 
*   **Stroke:** 1px.
*   **Paint:** Linear gradient (Top to Bottom) from `rgba(255, 255, 255, 0.14)` to `rgba(255, 255, 255, 0)`.
*   This mimics the way light catches the top edge of a physical glass pane.

---

## 5. Components

### Buttons
*   **Primary:** Gradient fill (`primary` to `primary_container`), `full` (9999px) roundness. No border.
*   **Secondary (Glass):** `surface` color with `backdrop-filter: blur(12px)`. Use the Top Edge Highlight.
*   **States:** On hover, increase the `backdrop-blur` and slightly shift the `surface_tint`.

### Cards & Lists
**Strict Rule:** No divider lines. Use `spacing-6` (2rem) or `spacing-8` (2.75rem) to create separation. 
*   **Cards:** Use `xl` (24px) corner radius. 
*   **Content:** Nested content inside cards should sit on a `surface_container_low` background to create a "recessed" look.

### Voice Input (The "Flow" Component)
A signature component for this system. A large, circular glass orb using `secondary` (Indigo) mesh gradients. When active, use a `1.5s` pulse animation where the `outline_variant` expands and fades.

### Input Fields
*   **Base:** `surface_container_lowest`. 
*   **Active:** Transition to `surface_variant` with a `primary` Top Edge highlight. 
*   **Typography:** User input should be `Inter`, while placeholder "suggested prompts" are `JetBrains Mono`.

---

## 6. Do's and Don'ts

### Do:
*   **Do** use asymmetrical margins (e.g., `spacing-20` on the left, `spacing-12` on the right) for editorial layouts.
*   **Do** let mesh gradients bleed behind glass panels to create a sense of environment.
*   **Do** use `JetBrains Mono` for any text that is machine-generated or "in-progress."

### Don't:
*   **Don't** use 100% opaque borders. It shatters the glass illusion.
*   **Don't** use standard "Drop Shadows." Only use large, diffused ambient glows.
*   **Don't** clutter the screen. If a piece of information isn't vital, hide it behind a hover state or move it to a lower surface-container tier.
*   **Don't** use sharp corners. Everything must feel smoothed and ergonomic (`xl` or `full` roundness).