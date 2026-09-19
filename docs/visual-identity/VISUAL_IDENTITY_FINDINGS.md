# docs/visual-identity/VISUAL_IDENTITY_FINDINGS.md

# Visual identity — findings

**Date:** 2026-09-19
**Status:** **baseline-ready.** VI-Q0–Q10 locked. Architecture [pass 3](./reviews/architecture-peer-review/pass-03-2026-09-19.md) **BLOCK create-execution-plan: no.** General plan + execution files exist.
**Purpose:** Baseline for a **PR operator console**: identity (tokens, type, mark) **and** in-app UX rebuilt for logic and usability — not a green paint job. **No execution steps.**
**Evidence:** frontend code on current tree. Greptile look: local captures `misc/image.png` (app) and `misc/image copy.png` (hero) — paths only, gitignored, not inlined. No production Revy screenshot pass.

**Related:** [SCAFFOLD_FINDINGS.md](../starter-pack/SCAFFOLD_FINDINGS.md) Q4 · [R7](../review-pipeline/REVIEW_PIPELINE_R7_REVIEWER_UI_GENERAL_PLAN.md) (routes/API stay; **screens may be restructured**) · [github-onboarding](../github-onboarding/README.md) (connect flow stays; chrome/UX in this program).

---

## Build principles

1. **One identity, tokens first.** Remap `--rv-*` → `--app-*` in `tokens.revy.css`. Feature UI keeps `var(--app-*)`. No hex in components. No second SSOT (`DESIGN_SYSTEM.md` at repo root is **reject**).
2. **Never mislead.** Contrast is computed (WCAG AA / APCA), not eyeballed. Empty/loading/error stay real. No fake stats, logos, or testimonials.
3. **Operator console, not costume.** Phosphor type and green-black field because the product is PRs, diffs, verdicts, logs. Scanlines, boot sequences, `#00FF00` glow, Matrix rain are costume — default **off** on product surfaces.
4. **Earn the palette.** “Dev tool → green terminal” is a category reflex. The concept sentence must still be true if you cover the wordmark.
5. **No corner-cutting.** Shared tokens, type, radius, motion, and logo. Do not theme landing in isolation and leave the app indigo.
6. **In-app UX is in scope (VI-Q9).** Dashboard, shell, reviewer, settings, installations must become **logical operator workflows**. Recoloring starter-pack cards is a fail.
7. **i18n day one.** EN + LV via `t()`. Voice rewrite is in scope with the look.
8. **Reuse the ladder.** Findings → general plan → execution. Third-party UX skills do not generate pages in this repo.

---

## Terminology

| Term | Meaning |
|------|---------|
| **Operator console** | Target identity: dense, monospace-led, green-black, hairline structure, severity as signal lamps (green / amber / red). |
| **Costume** | CRT effects that do not help the task: scanlines, flicker, typewriter heroes, ASCII boxes, phosphor bloom on data tables. |
| **Public surfaces** | Unauthenticated: `/`, `/login`, auth status gates, 404/unauthorized. |
| **Product chrome** | Authenticated shell: sidebar, header, dashboard, settings, admin, installations. |
| **Reviewer** | `/reviewer/**` — findings, PRs, merge readiness. Highest-density surface. |
| **`--app-*`** | Semantic tokens (`tokens.css`). Light `:root` **kept in code** (VI-Q2 dormant). Shipped UI always uses the console (`html.dark`). |
| **`--rv-*`** | Product overlay (`tokens.revy.css`). Today indigo only. |
| **Two intensities (VI-Q1 B)** | Same token system. Public may be theatrical (prompt-line, cursor). Product chrome and reviewer stay dense, flat, no overlay effects. |
| **Thin costume (VI-Q3)** | Public only: prompt-line header + block cursor (off under `prefers-reduced-motion`). **No** scanlines, boot, flicker, rain, or `#00FF00` glow. None of that on app/reviewer. |
| **In-app UX rebuild (VI-Q9)** | Restructure operator flows for scanability and task logic. Not a GitHub.com clone (no in-app diff viewer in this program). |
| **Plex pair (VI-Q4)** | IBM Plex Mono + IBM Plex Sans, OFL, self-host. Mono: chrome, prompts, paths, numbers. Sans: long reading (finding messages, settings). Public may be **mono-led**. Not JetBrains Mono. |
| **Mark (VI-Q5)** | Wordmark-first: `revy` in Plex Mono. Compact mark/favicon = **custom chevron geometry** (wedge SVG), never the Unicode `>` glyph. Prompt-line may use `>` as layout chrome (VI-Q3). Wordmark-only when a mark would duplicate that line or fail at 16px. **Reject** letter-R tile and ASCII-art logos. |
| **No inbox API (VI-Q9 bound)** | This program does **not** add a workspace PR/findings list endpoint. Operator home = IA on existing routes. |
| **Token uncouple (VI-Q10)** | Overlay `--rv-*` scale: canvas, text, muted, ring, primary/CTA, **info ≠ primary**, warning, danger, success. Today `--app-info` aliases `--app-primary` (`tokens.revy.css:11`). |

**Proposed concept (VI-Q0 locked as direction; wording may tighten):**

> The concept is: a **PR operator console** — expressed through phosphor type on a green-black field, hairline structure, severity as amber/red signal lamps, and motion that snaps (not fade-on-data).

Greptile is the **job** rival (AI code review). Live UI is **not** a terminal: dark rounded SaaS + mint banners (`misc/image.png`); light editorial hero + mint pills (`misc/image copy.png`). We may steal product *approach* from Greptile; we steal **nothing** about type, canvas, or hero. Do not de-green Revy to “avoid Greptile.” Cover-the-name vs Greptile: do not ship a **light gray hero + mint pill CTA**, and do not ship **mint billing banners** as identity.

---

## What exists vs genuinely new

### Verified — shipped

| Surface | What it is | Evidence |
|---------|------------|----------|
| Token SSOT | `--app-*` light + dark; Revy overlay maps primary/link/**info**/CTA to the **same** indigo (`--app-info` aliases primary) | `tokens.css`; `tokens.revy.css:4–22`; `index.css:1–4` |
| Theme | `light` / `dark` / `system`; `html.dark`; stored `app-theme` | `frontend/src/lib/theme.ts`; `AppearanceSettingsPage.tsx:13–17`; `index.html` boot script |
| Type | No font loaded. Browser / Tailwind default sans. `font-mono` only on paths. **Target (VI-Q4):** IBM Plex pair | `frontend/index.html` (no font link); `FindingRow.tsx:54`; `ReviewerHomePage.tsx:107` |
| Logo | Rounded square + letter **R** + wordmark. **Target (VI-Q5):** `revy` wordmark + custom wedge favicon (not `>`) | `RevyLogo.tsx:11–25` |
| Favicon | None in `frontend/public/` (only `silent-check-sso.html`) | glob |
| Landing | Centered eyebrow, “Ship with confidence”, radial indigo blob, **three equal Lucide cards**, one CTA | `LandingPage.tsx:26–86`; copy `en.json` `landing.*` |
| Login | Split panel, same blob, “Welcome back”, Lucide `LogIn` | `PublicAuthLayout.tsx`; `LoginPage.tsx` |
| App shell | 224px sidebar, `rounded-lg`, `ring-1`, Lucide nav | `AppShellLayout.tsx:40–88` |
| Dashboard | Greeting card + checklist + quick-action pills | `DashboardPage.tsx`; `WelcomeWidget.tsx`; `QuickActionsWidget.tsx` |
| Reviewer | Tables; merge/PR badges use `--app-success` / `--app-danger`; **severity is uncolored text** | `ReviewerHomePage.tsx`; `FindingRow.tsx:36–38`; `MergeReadinessBadge.tsx:11–15` |
| Motion | Duration tokens + global `prefers-reduced-motion` kill | `motion.css` |
| Toasts | Sonner `richColors` in **two** places | `main.tsx:33–36`; `lib/toast.ts:16–29` |
| Icons | `lucide-react` dependency; default on landing + nav | `frontend/package.json`; `LandingPage.tsx:3` |
| i18n | EN + LV landing keys exist; slogan register | `en.json` / `lv.json` `landing` |
| Scaffold lock | `--app-*` + `tokens.revy.css` is **locked** | `docs/starter-pack/SCAFFOLD_FINDINGS.md` Q4 |

### Verified — slop tells on current landing

These match public anti-slop catalogs (Sailop / ui-ux-kit gate), not taste:

- Centered generic hero + uppercase eyebrow (`LandingPage.tsx:43–52`).
- Radial primary blob (`LandingPage.tsx:27–30`).
- Three identical icon + title + body cards (`LandingPage.tsx:69–86`).
- Interchangeable copy: “Ship with confidence”, “Get started”, “AI-assisted review” (`en.json` `landing.hero` / `landing.features`).
- Indigo primary — default AI-SaaS hue (`tokens.revy.css:5`).
- `rounded-xl` + `ring-1` + Lucide as the component kit.

### Verified — in-app UX is not an operator console

Look aside, these flows are starter-pack:

- **Dashboard** is a greeting + setup checklist + pills (`DashboardPage.tsx`, `WelcomeWidget.tsx`, `QuickActionsWidget.tsx`). `ReviewerSummaryWidget` is a **CTA card** to `/reviewer` when available (`ReviewerSummaryWidget.tsx:17–31`; `registerRevy.ts`) — not a queue. There is **no** workspace inbox API (`reviewer/api.ts` is per repository / PR).
- **Reviewer** extra hop is **repo table → PR list** (installation `<select>` only if `installations.length > 1`, and it is a raw `<select>` not Quiet*). Findings dump title + full message; severity is uncolored text (`FindingRow.tsx:36–38`). Severity has **four** levels: `info \| warning \| error \| critical` (`types.ts:22`).
- **Shell** is generic SaaS nav; sidebar title is `common.appName`. Reviewer nav is an **extension** and returns `null` until `useReviewerAvailability` (`ReviewerNavItem.tsx:15–17`).
- **Installations** uses four equal explainer cards plus a primary button (`ConnectGitHubPanel.tsx:32–46`). github-onboarding connect **behavior** is a live program — this slice restyles chrome, does not rewrite HMAC / start-connect.
- **Appearance** offers light / dark / system (`AppearanceSettingsPage.tsx:13–17`) — VI-Q2 will hide that as a working choice, not delete the store. Boot must **force** `html.dark` (today `system` often paints `:root`).

### Genuinely new (this program)

| Gap | Why |
|-----|-----|
| Phosphor scale | Overlay today is one indigo; need canvas / text / accent / dim olive / signal amber / danger; **info ≠ primary** (VI-Q10) |
| Type contract | Load IBM Plex pair; `--font-sans` / `--font-mono`; self-host **latin + latin-ext** (LV diacritics) |
| Mark | Replace letter-R tile; favicon + OG missing |
| Public structure | Landing is not a conversion page and not a console; needs a non-3-card composition |
| In-app UX | Shell/dashboard/reviewer/settings/installations are starter-pack **workflows**, not only starter-pack colors |
| Voice | Slogan EN/LV → console voice (status, verdict, command) |
| Severity color | Findings table does not use semantic color (`FindingRow.tsx`) |
| Toast tokens | `richColors` bypasses `--app-*` |

### Reuse traps

- **Do not fork tokens.** Remap overlay. Touching `tokens.css` light values is shared scaffold; prefer overlay + dark-first mapping (VI-Q2).
- **Do not restyle GitHub markdown** here. Check-run / issue comment HTML is other programs.
- **Do not add a workspace inbox API** in this program (VI-Q9 bound). No client fan-out across repos pretending to be a complete queue.
- **Do not add a diff viewer.** R7 out-of-scoped it.
- **Do not rewrite github-onboarding behavior.** Restyle `ConnectGitHubPanel` chrome only.
- **Lucide ban is not a drive-by.** ui-ux-kit hard-bans Lucide-by-default; we use it in shell, settings, reviewer nav. Icon system is a track, not a drive-by swap.
- **`ring-1` is elevation.** Token overlay alone will still look like boxed SaaS until radius/border usage changes.
- **Do not delete the theme stack.** `theme.ts`, `html.dark`, `:root` light tokens, appearance settings plumbing stay. VI-Q2 ships console-only; revert must not be archaeology.

---

## Catalog (tracks)

Not execution. Labels for the later general plan.

### Track I — Identity (shared infra)

Palette, type, radius (0–4px), motion, mark, favicon.

**Rationale:** every surface reads the overlay. Fix once.

**Method:** `--rv-*` scale → `--app-*` with **info ≠ primary** (VI-Q10) **and** surface / text-strong / chip / ring-strong / input-border / table-row (not accent-only — slate leak); load **IBM Plex Mono + IBM Plex Sans** (self-host OFL, latin + latin-ext) in `index.html` / CSS; `--font-sans` / `--font-mono`; replace `RevyLogo` with wordmark + **wedge SVG** favicon; drop `richColors` in `main.tsx` **and** `lib/toast.ts`.

**Gate:** no feature file contains a raw brand hex; cover-the-wordmark test; body contrast **WCAG 2.2 AA floor** (4.5:1 body, 3:1 UI) **and** APCA Lc ≥ 75 body on canvas (prefer Lc 90). No `#00FF00` body even if WCAG “passes.”

### Track P — Public

`/`, `/login`, status gates, 404.

**Rationale:** first impression is the current slop specimen.

**Method:** new landing composition (not 3 equal cards, not trust-bar/testimonial template). Login inherits tokens; may keep split if it earns a distinctive move.

**Gate:** adversarial review on hero; EN+LV voice; 375 / ~800 height; reduced-motion; VI-Q3 thin costume only.

### Track C — Product chrome + operator UX

Shell, dashboard, settings, installations wizard, admin.

**Rationale:** users spend time here. Paint-only is a fail (VI-Q9).

**Method:** same tokens; denser type; fewer boxes. **Rebuild the flows on existing APIs:** kill the greeting card; keep ReviewerSummaryWidget as the slot to replace (copy/hierarchy, not a fake queue); keep reviewer **nav visible** (empty/connect state — do not gate the item off); installations = short connect path, not four equal cards. Quiet* stay; swap ReviewerHome raw `<select>` to `QuietSelect`. Do not rewrite github-onboarding HMAC/start-connect.

**Gate:** a member can reach the next useful action without “hello {name}”; 44px targets; settings/admin readable; appearance does not offer a fake Light theme (VI-Q2). **No** invented inbox counts.

### Track R — Reviewer UX

Repos → PRs → findings.

**Rationale:** this is the product. Costume here is a defect. Current tables are a data dump.

**Method:** operator scan, not marketing cards. Four severities stay named (info / warning / error / critical) — text + shape + hue; **green is merge success, not info**. Truncate message; severity first; path mono. Expensive hop to shorten is **repo → PR** only when there is nothing to pick (`<=1` install and one repo); hide `ReviewerLayout` back-to-`/reviewer` in that case so it does not bounce. No scanlines/glow. **No in-app diff viewer.** **No workspace inbox endpoint.**

**Gate:** finding rows scannable; merge badge still success/danger; empty/loading/error on every list; no overlay effects.

### Track V — Voice

Landing, login, empty states, CTAs.

**Rationale:** green type on “Ship with confidence” is still slop.

**Method:** rewrite keys EN+LV together. No “Elevate / Seamless / Unleash / Ship with confidence.”

**Gate:** cover the brand name in copy; could this be CodeRabbit/Greptile? If yes, rewrite.

---

## Advice / options

**Locked path (VI-Q1):** **B — one system, two intensities.** Public may use a blinking cursor, prompt-line header, slightly brighter phosphor. Product chrome and reviewer stay dense, flat, no overlay effects.

**Locked path (VI-Q2):** **Ship console only.** Always apply `html.dark`. **Mechanism:** boot script forces class; `applyTheme` ignores stored `light` for *paint*; Appearance control hidden or disabled with copy that this product is console-only; `theme.ts` / `:root` / store **kept**. Do not show Light that no-ops (never mislead). Revert later = re-enable + map `:root`.

**Locked path (VI-Q3):** **Thin public costume.** Prompt-line header + block cursor on landing/login. Cursor off under `prefers-reduced-motion`. Prompt-line may use `>` as **layout** only. **No** scanlines, boot, flicker, rain, glow — public or product.

**Locked path (VI-Q4):** **IBM Plex pair.** Mono for chrome/prompts/paths/numbers; Sans for long reading. Public **mono-led** (wordmark + hero). Self-host OFL **latin + latin-ext**. **Reject** JetBrains Mono and app-wide mono-only body. Do not prefix headlines with `>` / `$` as fake code (IBM Developer trap).

**Locked path (VI-Q5):** **Wordmark-first + custom wedge.** `revy` in Plex Mono. Favicon / collapsed mark = **custom chevron geometry** (SVG), **never U+003E**. `>` only as optional VI-Q3 prompt-line chrome, omitted where it duplicates. **Reject** letter-R tile and ASCII art.

**Locked path (VI-Q9):** **Rebuild in-app UX**, not restyle-only. **No new list API.** Operator home = promote `/reviewer` (nav always visible; empty/connect if needed), kill greeting, replace ReviewerSummaryWidget copy/hierarchy, shorten **repo → PR** by auto-Navigate only when `<=1` install and one repo — and hide `ReviewerLayout` back-to-`/reviewer` in that case. Dashboard is status + connect + next action — not a fake queue. Diff viewer / GitHub clone stay **out**.

**Locked path (VI-Q10):** Overlay `--rv-*` scale maps `--app-info` to a **distinct** token from `--app-primary` / CTA. Info findings must not share phosphor with the brand button.

| Option | What | Verdict |
|--------|------|---------|
| **A.** Public only | Landing/login terminal; app stays slate/indigo | **Reject** — identity split; next agent reverts to SaaS |
| **B.** Two intensities | Same tokens; public theatrical, app dense | **Locked** 2026-09-19 |
| **C.** Full CRT everywhere | Scanlines/glow on tables | **Reject** — fatigue, a11y, novelty |

**Phase shape (advice only):** I first (tokens+type+logo), then P+V, then C, then R. Do not ship a green landing on an indigo app.

---

## External research / patterns

| Source | Adopt / defer / reject |
|--------|-------------------------|
| [arham777/ui-ux-kit](https://github.com/arham777/ui-ux-kit) — concept sentence, adversarial review, countable anti-slop gate, surface routing (landing ≠ dashboard) | **Adopt ideas.** **Reject** in-repo clone / auto-skill / root `DESIGN_SYSTEM.md` / their landing anatomy (trust bar → feature cards → testimonials → pricing) |
| [Laith0003/ux-skill](https://github.com/Laith0003/ux-skill) (`uxskill`) | **Defer.** Optional later lint only. Must not generate pages |
| [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | **Reject.** Style catalog (glassmorphism / cyberpunk) |
| [carmahhawwari/ui-design-brain](https://github.com/carmahhawwari/ui-design-brain) | **Reject as default.** “Modern SaaS” is the look we are leaving. Component notes may inform Track C later |
| Sailop anti-slop (3-card grid, indigo, Inter, gradient blob) | **Adopt as diagnosis.** Current landing matches |
| designmd “Terminal Green” (`#0d1117` + `#39d353` + JetBrains Mono + scanlines) | **Defer palette.** GitHub-blue-black is not green-black. Scanlines = costume. **Reject** JetBrains Mono (VI-Q4) |
| Warp marketing (warm near-black, almost no green) | **Reject as palette.** Useful as “restraint” warning: terminal companies often refuse neon green |
| Meta CRT cookbook / phosphor-ui / astro-tui portfolios | **Reject as product UI.** Landing may cite them for VI-Q3 thin costume only |
| Greptile live UI | **Not a terminal look.** App = dark SaaS settings + mint subscription banner (`misc/image.png`). Hero = light editorial “The AI Code Reviewer.” + mint pills (`misc/image copy.png`). Mint is CTA/banner, not phosphor type. **Keep VI-Q0.** Steal **product approach** (review job) if useful; steal **nothing** about type, canvas, or hero. Do not copy mint pills or mint billing banners. |
| Greptile brand guidelines (True Black + `#28E99F` + Space Mono) | **Reject as Revy UI.** Guidelines ≠ shipped product in the captures. Still avoid shipping *that* mint-on-black as our identity, without dropping our console. |
| GitHub `#39d353` on `#0d1117` / designmd Terminal Green | **Reject as recipe.** Costume template (JetBrains + scanlines + GitHub-dark). Not a Greptile collision. |
| Qodo + IBM Plex Mono | **Noted.** Distinctiveness is density + lamps + console field, not the font. Keep Plex pair (VI-Q4). |

**Adapted anti-slop gate (this program):**

Hard fail: default purple/indigo gradient blob; 3 identical feature cards; Lucide as the *landing* identity; sparkle/“AI-powered” eyebrow; slogan copy; raw `#00FF00` body text; scanlines on reviewer/tables; hex in feature components; `richColors` toasts left as brand; focus ring on mouse click (`:focus` vs `:focus-visible` — current code mostly `focus-visible`, keep); light-gray hero + mint pill CTA (Greptile marketing); mint billing banner as identity (Greptile app).

---

## Data scope & exclusions

**In:**

- `frontend/src/styles/tokens.css` (only if overlay cannot express the system)
- `frontend/src/styles/tokens.revy.css`
- `frontend/index.html` (fonts, title, favicon, theme boot)
- `frontend/src/features/marketing/`
- `frontend/src/components/auth/`, `layout/`, `ui/` visual treatment
- `frontend/src/features/{dashboard,installations,reviewer,settings,admin,auth}/` visual, copy, **and operator UX** (layout/hierarchy of existing routes)
- `frontend/src/i18n/locales/{en,lv}.json` user-facing strings those screens use
- `frontend/src/main.tsx` toaster
- `frontend/src/lib/toast.ts` (same `richColors` leak)

**Out (this program):**

- GitHub check-run name, issue comment markdown, inline thread HTML
- GitHub App Marketplace listing / org install screens (GitHub-owned)
- Pipeline, judge, reconcile, billing logic
- Workspace PR/findings **inbox API** (later program)
- In-app diff viewer, Kanban, or other new reviewer SKUs (R7 out-of-scope stays)
- Installing `ui-ux-kit` / `ux-skill` / `ui-ux-pro-max` into `.cursor/skills/`
- Email HTML (no in-app template tree found under `backend/` for this pass)

---

## Edge cases

| Edge | Why it is hard |
|------|----------------|
| **Light mode** | Phosphor on white is a different product. **Shipped:** console only (VI-Q2). OS light users currently get light via `system` — that path must stop painting `:root` without deleting the store. |
| **Color vision** | Green/red severity pair. Need text + amber; do not encode state in hue only |
| **Fatigue / reading** | Neon body + mono-only findings hurt. VI-Q4: Plex Sans for long messages; dim olive body, bright accent sparingly |
| **Reduced motion** | Already a global kill (`motion.css:11–19`). Public typewriter/blink must honor it |
| **LV** | Console voice in Latvian; do not leave LV as translated slogans |
| **Admin impersonation banner** | Must remain unmistakable if chrome goes dark-green |
| **Sonner / Radix** | Third-party default surfaces will leak slate unless tokens or wrappers change |
| **Contrast on phosphor** | `#00FF00` on `#000` is a movie; compute AA/APCA on the real pairs |
| **Category reflex** | If the only distinctive move is “it is green,” it fails the cover-the-name test |

---

## Decisions registry

| Q# | Question | Status | Resolution |
|----|----------|--------|------------|
| **VI-Q0** | What is the identity? | **locked** | PR operator console: phosphor type on green-black field, hairline structure, severity lamps. Not generic SaaS. Not CRT costume. **Not Greptile’s look** (pass-01δ: app = dark SaaS, hero = light editorial). Cover-the-name vs Greptile = no mint-pill light hero / no mint billing banner — not “drop phosphor.” Chat + peer delta 2026-09-19. |
| **VI-Q1** | How far? A public-only / B two intensities / C full CRT | **locked** | **B.** Same tokens. Public may be theatrical; product chrome and reviewer stay dense and quiet. No scanlines/glow on tables. Chat 2026-09-19. |
| **VI-Q2** | Light mode? | **locked** | **Ship console only.** Boot forces `html.dark`; `applyTheme` ignores `light` for paint; Appearance hidden/disabled with honest copy; store + `:root` **kept**. Chat 2026-09-19; mechanism from pass-01. |
| **VI-Q3** | Public costume budget? | **locked** | **Thin.** Public: prompt-line header + block cursor (killed by reduced-motion). `>` allowed as prompt-line **layout** only. **No** scanlines, boot, flicker, rain, `#00FF00` glow. None on app/reviewer. Chat 2026-09-19. |
| **VI-Q4** | Type? | **locked** | **IBM Plex pair** (Mono + Sans), OFL, self-host latin+latin-ext. Mono: chrome, prompts, paths, numbers; public mono-led. Sans: finding messages and other long reading. **Reject** JetBrains Mono, app-wide mono-only body, and `>`/`$` headline prefixes. Chat 2026-09-19. |
| **VI-Q5** | Mark / wordmark / favicon? | **locked** | **Wordmark-first** (`revy` in Plex Mono) + **custom wedge SVG** as compact mark/favicon. **Never** Unicode `>` as the asset. `>` only on VI-Q3 prompt-line when it does not duplicate. **Reject** letter-R tile and ASCII-art. Chat 2026-09-19; geometry bound pass-01. |
| **VI-Q6** | Third-party UX skills in repo? | **locked** | **Reject** clone into `.cursor/skills/`. Steal concept + adversarial + gate into this folder only. |
| **VI-Q7** | Design SSOT? | **locked** | `tokens.revy.css` + `--app-*`. Optional DESIGN notes **in this folder** if useful. No repo-root `DESIGN_SYSTEM.md`. |
| **VI-Q8** | GitHub.com comment/check visual? | **locked** | **Out of scope.** Separate publish programs. |
| **VI-Q9** | In-app UX rebuild vs paint-only? | **locked** | **Rebuild** on **existing APIs**. No workspace inbox endpoint. Operator home = `/reviewer` IA + kill greeting + restyle existing dashboard widget slot. Recolor-only is a fail. **Out:** diff viewer, fake queue counts. Chat 2026-09-19; API bound pass-01. |
| **VI-Q10** | `--app-info` vs primary? | **locked** | **Uncouple.** Overlay must give info a token distinct from primary/CTA. Pass-01 high. |

---

## Parking lot

- Architecture peer review pass 3 complete (**BLOCK create-execution-plan: no**).
- Execution peer review pass 1 highs applied: overlay remaps surface/text-strong/chip; one-repo hop hides `ReviewerLayout` back link and does not auto-Navigate when `installations.length > 1`.
- Named `--rv-*` hex — **P0 deliverable** (canvas/body/accent **and** CTA fg/bg **and** info-on-canvas; AA + APCA). Avoid Greptile `#28E99F` and GitHub `#39d353` recipes without dropping phosphor.

---

## Devil's advocate

- **Green-on-black is as default as indigo** for “AI for developers.” If the layout stays three cards, we only recolored slop. Greptile is **not** that look (pass-01δ); still fail if we ship mint-pill SaaS or CRT costume.
- **Warp and Linear got distinctive by refusing phosphor.** We may look like a 2024 hacker portfolio, not a review product.
- **Console-only loses** users who keep OS light mode (current default path is system → often light). Plumbing stays so this is reversible.
- **Mono on long finding messages** hurts reading. Reviewer is a reading surface — VI-Q4 assigns Plex Sans there.
- **Token remap without UX rebuild** still looks like shadcn. VI-Q9 exists to stop that; unbounded UX scope can swallow the program — keep diff viewer out.
- **Token remap without radius/border/icon change** still looks like shadcn.
- **Doing this on `main` beside resolution-honesty** risks mixed PRs. Findings may live here; implementation should not hitchhike on pipeline work.

---

## Experiment / verification

Pass/fail later (not now):

| Check | Pass |
|-------|------|
| Cover the wordmark on landing screenshot | Not Greptile mint-pill light hero / not CodeRabbit / not generic SaaS / not CRT template |
| Body text vs canvas | WCAG 2.2 AA **and** APCA Lc ≥ 75 (prefer 90) on the named trio |
| Operator home | Authenticated path is reviewer IA + next action; **no** fake inbox counts |
| Severity | Color + text; not color alone |
| Reviewer | No scanline/flicker overlay |
| Reduced motion | No blink/typewriter |
| i18n | EN and LV keys for every new string |
| Token leak | No brand hex in `features/**` |
| Viewport | 375 width and ~700–800 height: landing usable |
| Reviewer scan | Severity visible without reading the whole row; empty/loading/error present |

**This findings pass did not** screenshot the running app. Visual claims above are **code-verified**.

---

## References

**Code:**

- `frontend/src/styles/tokens.css`
- `frontend/src/styles/tokens.revy.css`
- `frontend/src/index.css`
- `frontend/src/styles/motion.css`
- `frontend/src/features/marketing/pages/LandingPage.tsx`
- `frontend/src/components/auth/RevyLogo.tsx`
- `frontend/src/components/auth/PublicAuthLayout.tsx`
- `frontend/src/components/layout/AppShellLayout.tsx`
- `frontend/src/lib/theme.ts`
- `frontend/src/main.tsx`
- `frontend/src/lib/toast.ts`
- `frontend/src/features/reviewer/ReviewerSummaryWidget.tsx`
- `frontend/src/i18n/locales/en.json` (`landing`, `auth.login`)
- `frontend/src/features/reviewer/components/FindingRow.tsx`
- `docs/starter-pack/SCAFFOLD_FINDINGS.md` Q4
- `misc/image.png` / `misc/image copy.png` (local Greptile captures, gitignored)

**Literature / prior art (see External research):** ui-ux-kit; Sailop; designmd Terminal Green (reject recipe); Warp restraint; Greptile job rival, not console look.
