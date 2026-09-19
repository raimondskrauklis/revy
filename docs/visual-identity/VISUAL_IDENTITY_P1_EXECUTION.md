# docs/visual-identity/VISUAL_IDENTITY_P1_EXECUTION.md

# P1 — Public + voice (execution)

Phase **P1** of [`VISUAL_IDENTITY_GENERAL_PLAN.md`](./VISUAL_IDENTITY_GENERAL_PLAN.md). Baseline: [`VISUAL_IDENTITY_FINDINGS.md`](./VISUAL_IDENTITY_FINDINGS.md) Track P, VI-Q1/Q3. **P1 only.**

**Authority:** findings VI-Q0–Q10.

**Goal:** `/` and `/login` are the operator console, not indigo SaaS slop.

## Decisions locked for P1

- Kill 3 Lucide feature cards, indigo blob, trust-bar, testimonials, mint-pill light hero. Not a recolor of the current grid.
- VI-Q3 thin costume: prompt-line header + block cursor. `>` is **layout chrome only**, not the mark. Cursor off under `prefers-reduced-motion` (`motion.css` already global).
- Public **mono-led** (wordmark + hero). No `>` / `$` headline prefixes.
- Login: **keep `lg:grid-cols-2` split**; remove the radial blob; inherit P0 tokens / `--app-radius-*`. Do not collapse to one column.
- Status gates + 404 **look** only. Destinations stay `/dashboard` until **P3**.
- Voice: drop “Ship with confidence” and LV slogan twin. EN+LV via `t()` in the same change.
- Cover-the-name: not Greptile mint-pill light hero, not mint billing banner, not CRT template, not three Lucide cards.

## Out of scope for P1 (later phases)

- Authenticated shell / Quiet* / installations cards → **P2**
- Logged-in redirect, login `from`, callback, CompleteProfile, 404/unauthorized **href** → **P3**
- Reviewer tables → **P4**
- GitHub.com copy

---

## P1.1 — Landing composition

**What:** Rewrite `LandingPage` as a console field: prompt-line + wordmark, one operator claim, CTA. Remove `features` Lucide grid and top radial blob. Consume `--app-radius-*`. Cursor blink 120–200ms; `motion-reduce:` kills it. Test comment: 375 and ~700–800 height usable (cover-the-name screenshot remains **non-gate**).

**Files:** `frontend/src/features/marketing/pages/LandingPage.tsx`, `frontend/src/features/marketing/pages/LandingPage.test.tsx`

**Deliverable:** test no longer expects “Ship with confidence” or three feature headings; no `GitBranch` / `ShieldCheck` / `Users` icons on the page; landing source notes 375 / ~800 usable.

```bash
cd frontend && npm test -- LandingPage
```

---

## P1.2 — Login keep-split, no blob

**What:** `PublicAuthLayout` stays two-column on `lg`. Delete the `radial-gradient` blob. Panel copy inherits P0 tokens; hairline instead of `rounded-xl` + shadow card. `LoginPage` form uses `--app-radius-md`. Dest `from` default stays `/dashboard` (P3).

**Files:** `frontend/src/components/auth/PublicAuthLayout.tsx`, `frontend/src/features/auth/pages/LoginPage.tsx`, `frontend/src/features/auth/pages/LoginPage.test.tsx`

**Deliverable:** layout still `lg:grid-cols-2`; source has no `radial-gradient`; login test still calls `login('/dashboard')`.

```bash
cd frontend && npm test -- LoginPage
```

---

## P1.3 — Status gates + 404 look

**What:** Restyle `StatusGatePage`, `NotFoundPage`, `UnauthorizedPage` to the console field (tokens, hairline, Plex). Do **not** change `to="/dashboard"` / `navigate('/dashboard')`.

**Files:** `frontend/src/features/auth/pages/StatusGatePage.tsx`, `frontend/src/components/errors/NotFoundPage.tsx`, `frontend/src/components/errors/NotFoundPage.test.tsx` (new), `frontend/src/features/auth/pages/UnauthorizedPage.tsx`, `frontend/src/features/auth/pages/UnauthorizedPage.test.tsx`

**Deliverable:** unauthorized/404 tests still route home to `/dashboard`.

```bash
cd frontend && npm test -- UnauthorizedPage NotFoundPage
```

---

## P1.4 — EN + LV voice

**What:** Replace landing/login/panel slogan keys. No “AI-powered” eyebrow, no “Ship with confidence”, no LV twin slogan. Operator-console voice; same keys in `en.json` + `lv.json`.

**Files:** `frontend/src/i18n/locales/en.json`, `frontend/src/i18n/locales/lv.json`, `frontend/src/features/marketing/pages/LandingPage.test.tsx`

**Deliverable:** `en.json` / `lv.json` landing hero strings do not contain “Ship with confidence” / “Pārliecība”; landing test matches the new EN heading.

```bash
cd frontend && npm test -- LandingPage LoginPage
```

---

**Phase gate** (from `frontend/`):

```bash
npm test -- LandingPage LoginPage UnauthorizedPage NotFoundPage
```

**Human gate:** none (cover-the-name screenshot is **non-gate** — 375 and ~700–800 height usable; not mint-pill / CRT / 3-card).

**Deploy:** public surfaces pick up P0 tokens. Authenticated chrome still starter-pack until P2.

**Next:** [`VISUAL_IDENTITY_P2_EXECUTION.md`](./VISUAL_IDENTITY_P2_EXECUTION.md)
