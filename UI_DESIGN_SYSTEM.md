# ThinkAloudAI — Master UI Design System & Best Practices

This document defines the strict UI, typography, color palette, button geometries, alignment standards, and engineering rules for all pages across ThinkAloudAI.

---

## 1. Color Palette & Theme Tokens

The platform uses a high-contrast, modern developer SaaS palette with `#C7381A` (Crimson / Rust Red) as the signature accent. **Never use muddy browns or uncalibrated orange tones.**

### Dark Mode (Default)
| Token | Hex / Value | Usage |
| :--- | :--- | :--- |
| **Canvas Background** | `#09090b` | Main page background |
| **Surface (Card / Panel)** | `#121215` / `rgba(18,18,21,0.8)` | Elevated panels, glassmorphic cards |
| **Raised Surface** | `#18181b` | Active rows, dropdowns, code editor headers |
| **Primary Text** | `#f4f4f5` | Headings, titles, primary labels |
| **Muted Text** | `#a1a1aa` | Body descriptions, secondary metadata |
| **Subtle Text** | `#71717a` | Timestamps, line numbers, placeholder text |
| **Borders & Dividers** | `#27272a` / `rgba(39,39,42,0.8)` | Card borders, section dividers |
| **Brand Accent** | `#C7381A` | Highlights, active tabs, badges, subtle glows |
| **Brand Light / Glow** | `#E04F2E` | Dark-mode text contrast highlight |
| **Success Status** | `#22c55e` | Passing test cases, live operational pills |
| **Warning / Caution** | `#f59e0b` | Memory warning, hints |
| **Error / Failure** | `#ef4444` | Failed test cases, syntax errors |

### Light Mode
| Token | Hex / Value | Usage |
| :--- | :--- | :--- |
| **Canvas Background** | `#fcfcfc` | Main page background |
| **Surface (Card / Panel)** | `#ffffff` / `rgba(255,255,255,0.8)` | Cards, floating navbar, forms |
| **Raised Surface** | `#f4f4f5` | Code backgrounds, active rows |
| **Primary Text** | `#09090b` | Main headings, primary content |
| **Muted Text** | `#71717a` | Secondary copy, descriptions |
| **Borders & Dividers** | `#e4e4e7` | Card borders, horizontal rules |
| **Brand Accent** | `#C7381A` | Primary brand accent and active highlights |

---

## 2. Button Shapes & Interactive Controls

All interactive buttons and inputs must adhere to modern **square-rounded geometry** (8px–12px border radius).

### Rules
1. **Never use retro chunky terminal buttons** (e.g., `[ Execute Run ]`).
2. **Never make entire buttons bright orange.**
3. **Primary Action Button:**
   - Dark Mode: `bg-white text-black hover:bg-zinc-200 font-semibold text-xs sm:text-sm rounded-lg sm:rounded-xl px-5 py-2.5 shadow-sm active:scale-95 transition-all`
   - Light Mode: `bg-zinc-950 text-white hover:bg-zinc-800 font-semibold text-xs sm:text-sm rounded-lg sm:rounded-xl px-5 py-2.5 shadow-sm active:scale-95 transition-all`
4. **Secondary / Outline Button:**
   - `bg-white/60 dark:bg-zinc-900/60 border border-zinc-200 dark:border-zinc-800 text-zinc-800 dark:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 font-medium text-xs sm:text-sm rounded-lg sm:rounded-xl px-5 py-2.5 transition-all`
5. **Brand Accent Highlight Button (Selective):**
   - `bg-[#C7381A] hover:bg-[#B02F14] text-white font-semibold text-xs sm:text-sm rounded-lg sm:rounded-xl px-5 py-2.5 shadow-sm shadow-[#C7381A]/20 transition-all`
6. **Form Inputs:**
   - `rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white/80 dark:bg-zinc-900/80 px-4 py-2.5 text-sm text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 dark:placeholder:text-zinc-600 focus:outline-none focus:ring-2 focus:ring-[#C7381A]/40 focus:border-[#C7381A]`

---

## 3. Typography & Copy Standards

1. **Font Families:**
   - Display & Headings: `Space Grotesk` (`var(--font-heading)`)
   - Body & Controls: `Inter` (`var(--font-sans)`)
   - Code & Telemetry: `JetBrains Mono` (`var(--font-mono)`)
2. **Taglines & Subheads:**
   - Must be **short, punchy, and single-line** wherever possible to maintain vertical scannability.
   - Avoid bloated multi-paragraph descriptions on marketing cards.
3. **Authenticity & Honesty:**
   - Never fabricate fake user counts, fake FAANG employment claims, or synthetic reviews.
   - Focus exclusively on product features, real interview mechanics, and actionable utility.

---

## 4. Grid, Alignment & Container Rules

To prevent jagged margins and asymmetrical layouts:
1. **Standard Page Container:**
   - Outer Section: `<section className="w-full border-t border-zinc-200/80 dark:border-zinc-800/80">`
   - Inner Max-Width Wrapper: `<div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-20">`
2. **Floating Top Navigation Bar:**
   - Centered with `fixed top-4 left-1/2 -translate-x-1/2 w-[92%] sm:w-[90%] max-w-5xl z-50 rounded-2xl bg-white/80 dark:bg-[#0d0d10]/80 backdrop-blur-xl border border-zinc-200/90 dark:border-zinc-800/90 shadow-lg`.
3. **Glassmorphism Spec:**
   - `backdrop-blur-xl bg-white/70 dark:bg-[#121215]/70 border border-zinc-200/90 dark:border-zinc-800/90`

---

## 5. Icons & Media

1. **Official Brand Logo:**
   - Always render `/logo.png` via Next.js `next/image` with `priority` above the fold.
2. **Vector Icons:**
   - Use clean, inline SVGs with standard 24x24 viewBox and `strokeWidth="2"`.
   - Never use missing Lucide brand icons (e.g. Twitter/Github from lucide); use SVG paths.

---

## 6. Page-by-Page Implementation Roadmap

1. ✅ **Landing Page (`/`)**: Rebuilt with takeUforward-inspired roadmaps, 1:1 interview studio mockup, floating header, unified grid, and `#C7381A` palette.
2. 🔄 **Auth Pages (`/login`, `/signup`, `/forgot-password`)**: Clean glassmorphic auth cards, square-round inputs, `#C7381A` focus rings, brand logo, working auth submission.
3. 🔄 **Dashboard Overview (`/dashboard`)**: Structured overview with interview history, skill radar, quick mock launcher, and recommended roadmap tracks.
4. 🔄 **DSA Practice Arena (`/dashboard/practice`)**: Monaco editor, test runner, problem list drawer, and speech prompt integration.
5. 🔄 **Interview Modes (`/dashboard/interviews`)**: Live voice interview setup, track selector, system design simulator.
6. 🔄 **Session Analysis (`/dashboard/interviews/[id]/analysis`)**: Post-interview `SESSION_REVIEW.md` breakdown, line comments, audio playback, and homework generation.
