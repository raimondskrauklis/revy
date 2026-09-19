# docs/visual-identity/VISUAL_IDENTITY_P0_EXECUTION.md

# P0 — Foundations (execution)

Phase **P0** of [`VISUAL_IDENTITY_GENERAL_PLAN.md`](./VISUAL_IDENTITY_GENERAL_PLAN.md). Baseline: [`VISUAL_IDENTITY_FINDINGS.md`](./VISUAL_IDENTITY_FINDINGS.md) VI-Q0–Q10, Track I (identity). **P0 only.**

**Authority:** findings VI-Q0–Q10.

**Goal:** Shared identity exists before any page is restyled: overlay scale, type, force-dark, mark, toasts.

## Decisions locked for P0

- Overlay `--rv-*` maps the **full** `tokens.css` `html.dark` surface/text/chip family, not accent-only. Required `--app-*`: canvas, **surface**, ring, **ring-strong**, **input-border**, **text-strong**, `--app-text`, muted, **subtle**, **chip / chip-active / chip-hover**, **table-row / table-row-alt**, primary, **info ≠ primary / CTA**, warning, danger, success, CTA fg/bg. Link may stay on primary. Leaving surface/text-strong/chip on slate (`#0F172A` / `#F8FAFC`) is a fail.
- Measure and record in `tokens.revy.css` comments: canvas/body/accent **and** CTA fg/bg **and** info-on-canvas. Floor: WCAG 2.2 AA **and** APCA Lc ≥ 75 (prefer 90). No `#00FF00` body. Avoid Greptile `#28E99F` and GitHub `#39d353` recipes without dropping phosphor.
- IBM Plex Sans + Mono, OFL, latin + latin-ext, bundled (no Google/CDN CSS). Tailwind v4 `@theme` maps `--font-sans` / `--font-mono` so utilities `font-sans` / `font-mono` are Plex.
- Radius tokens `--app-radius-sm` = `0px`, `--app-radius-md` = `4px`. **Defined here; consumed on restyled surfaces in P1/P2.** P0 does not restyle landing/shell.
- Boot + `applyTheme` always paint `html.dark`. Store + `:root` light tokens **kept**. Appearance hides Light/System; honest console-only copy (no fake Light).
- Compact mark = custom wedge **SVG**, never U+003E. Wordmark `revy` in Plex Mono. Raster `favicon.ico` + PNG from the same geometry.
- Drop Sonner `richColors` in `main.tsx` **and** `lib/toast.ts`.
- Hex values are **this phase’s calibration**, not a later fork.

## PR review context (required when code + docs ship in one PR)

- **SSOT (Moonshot inject):** `.revy/review-context.json` — `active_program: "visual-identity"`; **`programs[]` = one entry only** (remove `github-onboarding`); `scope`: `["frontend/**"]`; three doc paths below.
- **Bugbot:** `.cursor/BUGBOT.md` — active program visual-identity + same three docs.
- **Agent mirror:** copy SSOT to `.agent/review-context.json`.
- **Do not** wire Greptile / regenerate `.greptile/files.json` as a reviewer gate (`integrations.greptile` is false).

**Doc paths (SSOT `paths[]` only):**

- `docs/visual-identity/VISUAL_IDENTITY_P0_EXECUTION.md`
- `docs/visual-identity/VISUAL_IDENTITY_FINDINGS.md`
- `docs/visual-identity/VISUAL_IDENTITY_GENERAL_PLAN.md`

## Out of scope for P0 (later phases)

- Landing / login composition, voice, blob → **P1**
- Shell, settings/admin, Quiet* radius consumption, installations cards → **P2**
- `/reviewer` dest retarget, greeting, nav un-gate → **P3**
- Finding-row scan, one-repo hop → **P4**
- Deleting `theme.ts` / `:root` / theme store

---

## P0.0 — Program PR review context (SSOT + Bugbot)

**What:** Switch SSOT from `github-onboarding` to `visual-identity`; one program entry; update Bugbot; copy the same JSON to `.agent/review-context.json`.

**Files:** `.revy/review-context.json`, `.agent/review-context.json`, `.cursor/BUGBOT.md`

**Deliverable:** from **repo root**:

```bash
python -m json.tool .revy/review-context.json > /dev/null
cd backend && pipenv run pytest tests/unit/test_engineering_context_manifest.py -q
```

---

## P0.1 — Overlay scale + contrast record

**What:** Replace indigo-only overlay with `--rv-*` for the full `html.dark` family listed in Decisions (surface, text-strong, chip, ring-strong, input-border, table-row included). Map to `--app-*` including `--app-cta-*`. Define `--app-radius-sm` / `--app-radius-md`. Keep `:root` light mappings in overlay for dormant plumbing; shipped paint is `html.dark`. Comment table: pair, WCAG ratio, APCA Lc for canvas/body, canvas/accent, CTA fg/bg, info-on-canvas.

**Files:** `frontend/src/styles/tokens.revy.css`, `frontend/src/styles/consoleContrast.test.ts` (new)

**Deliverable:** overlay `html.dark` sets `--app-surface`, `--app-text-strong`, `--app-chip` (not left to `tokens.css` slate); `--app-info` hex ≠ `--app-primary`; overlay text does not contain `#28E99F`, `#39d353`, or `#00FF00` as body/primary; WCAG AA helper covers the named pairs.

```bash
cd frontend && npm test -- src/styles/consoleContrast.test.ts
```

---

## P0.2 — Plex `@theme` + latin-ext

**What:** Add `@fontsource/ibm-plex-sans` and `@fontsource/ibm-plex-mono` (latin + latin-ext). Import in `index.css`. `@theme { --font-sans; --font-mono; }` so Tailwind `font-mono` is Plex Mono. `html` uses sans. No Google/CDN `<link>`.

**Files:** `frontend/package.json`, `frontend/src/index.css`, `frontend/index.html` (no CDN), `frontend/src/styles/fonts.test.ts` (new)

**Deliverable:** `index.css` `@theme` maps `--font-sans` / `--font-mono` to IBM Plex; `index.html` has no fonts.googleapis / typekit URL.

```bash
cd frontend && npm test -- src/styles/fonts.test.ts
```

---

## P0.3 — Force-dark boot + honest Appearance

**What:** `index.html` boot always adds `html.dark` (ignore stored `light` / OS `system`). `applyTheme` always toggles `dark` **on** for paint; still writes the requested mode to `localStorage`. Appearance page: no Light/System control; EN+LV copy that the product is console-only. Keep store + `ThemeMode` type.

**Files:** `frontend/index.html`, `frontend/src/lib/theme.ts`, `frontend/src/lib/theme.test.ts` (new), `frontend/src/features/settings/pages/AppearanceSettingsPage.tsx`, `frontend/src/features/settings/pages/AppearanceSettingsPage.test.tsx`, `frontend/src/i18n/locales/en.json`, `frontend/src/i18n/locales/lv.json`

**Deliverable:** `applyTheme('light')` and `applyTheme('system')` leave `html.dark`; Appearance has no Light option.

```bash
cd frontend && npm test -- src/lib/theme.test.ts AppearanceSettingsPage
```

---

## P0.4 — Wordmark + wedge + raster favicon

**What:** Replace letter-R tile with Plex Mono wordmark `revy` plus inline custom wedge SVG (not `>`). `showWordmark={false}` is wedge-only. Add `frontend/public/favicon.ico` and PNG from the same SVG; `<link rel="icon">` in `index.html`.

**Files:** `frontend/src/components/auth/RevyLogo.tsx`, `frontend/src/components/auth/RevyLogo.test.tsx` (new), `frontend/public/favicon.ico`, `frontend/public/favicon.png`, `frontend/index.html`

**Deliverable:** logo markup has no letter `R` tile; SVG path is not a text `>` glyph; favicon files exist.

```bash
cd frontend && npm test -- RevyLogo
```

---

## P0.5 — Drop `richColors`

**What:** Remove `richColors` from the root `Toaster` and from `lib/toast.ts` defaults so toasts use `--app-*`.

**Files:** `frontend/src/main.tsx`, `frontend/src/lib/toast.ts`, `frontend/src/lib/toast.richColors.test.ts` (new)

**Deliverable:** neither production file contains `richColors`.

```bash
cd frontend && npm test -- src/lib/toast.richColors.test.ts
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_engineering_context_manifest.py -q
```

**Phase gate** (from repo root, then `frontend/`):

```bash
python -m json.tool .revy/review-context.json > /dev/null
cd frontend && npm test -- src/styles/consoleContrast.test.ts src/styles/fonts.test.ts src/lib/theme.test.ts src/lib/toast.richColors.test.ts AppearanceSettingsPage RevyLogo
```

**Human gate:** none.

**Deploy:** frontend-only; P1–P4 consume these tokens. Can ship P0 alone (existing screens pick up overlay).

**Next:** [`VISUAL_IDENTITY_P1_EXECUTION.md`](./VISUAL_IDENTITY_P1_EXECUTION.md)
