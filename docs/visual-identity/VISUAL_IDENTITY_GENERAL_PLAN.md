# docs/visual-identity/VISUAL_IDENTITY_GENERAL_PLAN.md

# Visual identity — general plan

**Baseline:** [VISUAL_IDENTITY_FINDINGS.md](./VISUAL_IDENTITY_FINDINGS.md) (VI-Q0–Q10 locked; architecture [pass 3](./reviews/architecture-peer-review/pass-03-2026-09-19.md) **BLOCK create-execution-plan: no**). **No execution steps.**

**Thesis:** One PR operator console — phosphor on green-black, hairline, Plex pair, wordmark + wedge. Public thin costume; app dense. Rebuild in-app UX on existing APIs. Greptile is the job rival; copy none of the UI.

**Locked:** VI-Q0–Q10. Pass-3 enumerations: Tailwind `@theme` font map in P0; `--app-radius` consumed in P1/P2; login keep-split-without-blob; 404 / unauthorized / CompleteProfile home → `/reviewer`; one-repo skip table. Calibration only: named `--rv-*` hex after P0 contrast measure.

---

## Cross-cutting (every phase)

- **Never mislead:** no fake queue counts, no Light control that no-ops, no hex in feature UI, no `#00FF00` body.
- **Coverage / exclusions:** no inbox API, no diff viewer, no github-onboarding HMAC rewrite, no admin `/admin/dashboard` / impersonation-stop / danger-zone retarget unless named here (they are **out**).
- **Visualization:** cover-the-name screenshots (not mint-pill light hero, not mint billing banner, not CRT template, not three Lucide cards).
- **i18n:** EN+LV via `t()` in the same change; latin-ext for LV diacritics.
- **Tokens:** `var(--app-*)` only in features; overlay in `tokens.revy.css`.
- **Tests:** Vitest beside touched screens; landing/login/callback defaults; theme boot always `html.dark`; contrast pairs recorded.
- **Motion:** 120–200ms snap/opacity on chrome; reduced-motion already global — public cursor dies with it.

---

## P0 — Foundations

**Goal:** Shared identity exists before any page is restyled: overlay scale, type, force-dark, mark, toasts.

**Scope:** In — `--rv-*` overlay must remap the full `tokens.css` `html.dark` surface/text/chip family, not only accent: canvas, **surface**, ring, **ring-strong**, **input-border**, **text-strong**, body (`--app-text`), muted, **subtle**, **chip / chip-active / chip-hover**, **table-row / table-row-alt**, primary / **info ≠ primary** / warning / danger / success / CTA (link may stay on primary). Leaving surface/text-strong/chip on slate is a leak (GitHub-dark canvas + phosphor buttons). Measure WCAG 2.2 AA **and** APCA Lc ≥ 75 (prefer 90) on canvas/body/accent **and** CTA fg/bg **and** info-on-canvas; avoid Greptile `#28E99F` and GitHub `#39d353` *recipes* without dropping phosphor; IBM Plex Mono+Sans self-host OFL latin+latin-ext; Tailwind v4 `@theme` maps `--font-sans` / `--font-mono` so `font-mono` is Plex; boot + `applyTheme` force `html.dark`, store kept; Appearance honest (hidden/disabled, not a fake Light); `RevyLogo` wordmark + **wedge SVG** plus raster favicon (`favicon.ico` / PNG); drop `richColors` in `main.tsx` **and** `lib/toast.ts`; radius 0–4px tokens defined here, **consumed** on restyled surfaces in P1/P2 (P0 tokens do not restyle pages by themselves). Out — landing rewrite; reviewer IA; new APIs; deleting `theme.ts` / `:root`.

**Deliverables:** Every screen that already uses `--app-*` can paint the console; info findings would not share CTA green; OS-light users get the console; contrast numbers are in the overlay comments or this folder; no Google/CDN font CSS.

**Depends on:** None.

---

## P1 — Public + voice

**Goal:** `/` and `/login` are the operator console, not indigo SaaS slop.

**Scope:** In — landing composition (not 3-card / trust-bar / testimonials / mint-pill light hero); VI-Q3 prompt-line + block cursor (`>` layout only, not the mark); login **keep two-column split**, remove blob, inherit tokens (do not collapse to single column); status gates + 404 **look**; EN+LV voice (no “Ship with confidence” / LV slogan twin). Out — authenticated shell; GitHub.com copy; 404/unauthorized/CompleteProfile **destination** retarget (P3).

**Deliverables:** Cover-the-name on hero passes; 375 and ~700–800 height usable; reduced-motion kills blink.

**Depends on:** P0.

---

## P2 — Product chrome

**Goal:** Shell, settings, admin, and connect chrome are the dense console — not rounded starter-pack cards.

**Scope:** In — sidebar/header wordmark; hairline not `ring-1` card elevation; **consume** `--app-radius` / hairline on shell + Quiet*; settings + admin readable; impersonation banner stays unmistakable; installations **chrome** (kill four equal cards) without rewriting HMAC/start-connect. Out — dashboard greeting/entrypoints (P3); finding-row scan (P4).

**Deliverables:** Authenticated chrome matches P0 tokens; connect path is short; github-onboarding behavior unchanged.

**Depends on:** P0.

---

## P3 — Operator home

**Goal:** After sign-in, the member is in the reviewer, not a greeting dashboard.

**Scope:** In — default authenticated landing `/reviewer` from `LandingPage` (logged-in redirect), `LoginPage` `from`, `AuthCallbackPage` default, `CompleteProfilePage` success dest, `NotFoundPage` home link, `UnauthorizedPage` navigate + home link — **not** admin dashboard, impersonation-stop, or danger-zone fallbacks; kill Welcome greeting; restyle `ReviewerSummaryWidget` slot (no fake counts; show when unavailable as connect, not `null`); reviewer **nav always visible** (empty/connect, not gated `null`); dashboard becomes status + connect + next action. Out — workspace inbox API; client fan-out across repos.

**Deliverables:** Tests cover the six dest files; a member reaches the next useful action without “hello {name}.”

**Depends on:** P0, P2.

---

## P4 — Reviewer UX

**Goal:** Repos → PRs → findings are scannable operator tables.

**Scope:** In — severity as text + shape + hue (four levels; green = merge success, not info); truncate message; path mono / body Sans; shorten **repo → PR** by **auto-`Navigate` only when `installations.length <= 1` and that install has exactly one repo after load** (to `/reviewer/repositories/:id/pull-requests`); **hide** `ReviewerLayout` `backToRepositories` in that case (it would bounce `/reviewer` → Navigate). When `installations.length > 1`, never auto-Navigate (QuietSelect must stay reachable); one repo = one-row table. Multiple repos = denser table. Empty/loading/error on every list. Out — in-app diff viewer; new list endpoint; workspace PR list; scanlines/glow.

**Deliverables:** A finding row is readable without the full message; merge badge still success/danger.

**Depends on:** P0, P3.

---

**Open (calibration only):** none — named `--rv-*` hex recorded in findings parking after P0 measure.

**Next:** none (P0–P4 shipped).
