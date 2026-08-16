# ThinkAloudAI — Visual & UX Design System (Industrial Blueprint)

## 1. Core Creative Direction
**Concept:** "A high-precision, brutalist engineering tool."
- **Vibe:** Technical, stark, architectural, hyper-precise, cold.
- **Avoid:** Warm cream/brown tones, friendly rounded corners, heavy shadows, floating cards, serif fonts, "editorial magazine" aesthetics.

## 2. Color System (Obsidian & Cyan)
- **Primary Backgrounds:** True Black (`#000000`), Deep Zinc (`#09090B`).
- **Surfaces & Borders:** Dark Zinc (`#18181B`), Hairlines (`#27272A`).
- **Text:** Frost White (`#FAFAFA`), Steel Gray (`#A1A1AA`).
- **Primary Accent:** Electric Cyan (`#00F0FF`) — used for active states, critical terminal output, and focal points.
- **Secondary Accents:** None. The product relies on monochromatic contrast and structure.

## 3. Typography (Stark & Technical)
1. **Display & UI (Grotesk Sans):** `Inter` or `Space Grotesk`. Tight letter-spacing, cold, mechanical.
2. **Structural & Hero (Monospace):** `JetBrains Mono` or `Geist Mono`. The core identity is driven by monospace text to emphasize that this is a *developer* tool.

## 4. UI Elements & Layout (The Blueprint)
- **Grid & Spacing:** Rigid 12-column grid.
- **Borders & Radii:** Explicit 1px hairline borders (`solid #27272A`) dividing sections. **Zero border-radius** (0px). Everything is sharp and flush.
- **Shadows:** No shadows. Depth is created by border intersections and background color changes (e.g., `#000000` to `#09090B`).
- **Texture:** Very subtle CRT/terminal grain or none at all. Pure vector sharpness is preferred.

## 5. Motion & Micro-interactions
- **Philosophy:** Instant, snappy, and terminal-like. No slow, "physical" sweeps.
- **Feedback:** Blinking cursors, instantaneous color inversion on hover (e.g., Black text on Cyan background).
