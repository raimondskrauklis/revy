# docs/visual-identity/README.md

# Visual identity

**Status:** P0–P4 shipped. **Next program:** UI/UX + mobile/layout upgrade.

**Authority:**
- [VISUAL_IDENTITY_FINDINGS.md](./VISUAL_IDENTITY_FINDINGS.md) VI-Q0–Q10 · [VISUAL_IDENTITY_GENERAL_PLAN.md](./VISUAL_IDENTITY_GENERAL_PLAN.md) — shipped
- [console-ux-upgrade/README.md](./console-ux-upgrade/README.md) — next program: findings UX + mobile/layout

**Why this folder:** identity **and** in-app operator UX. Not a review-pipeline slice and not GitHub-comment HTML.

**Trigger:** function is ahead of identity **and** in-app UX is starter-pack. Direction: **PR operator console**. Greptile is the **job** rival, not a terminal look. **VI-Q1 B:** two intensities. **VI-Q2:** console only. **VI-Q3:** thin public costume. **VI-Q4:** IBM Plex pair. **VI-Q5:** wordmark + custom wedge. **VI-Q9:** rebuild UX on existing APIs. **VI-Q10:** `--app-info` ≠ primary.

**Does not replace:** [SCAFFOLD_FINDINGS.md](../starter-pack/SCAFFOLD_FINDINGS.md) Q4 · [R7 reviewer UI](../review-pipeline/REVIEW_PIPELINE_R7_REVIEWER_UI_GENERAL_PLAN.md) (routes/API stay; screens may be restructured; no diff viewer) · GitHub publish programs.

| Doc | Purpose |
|-----|---------|
| [VISUAL_IDENTITY_FINDINGS.md](./VISUAL_IDENTITY_FINDINGS.md) | Baseline. No execution steps. |
| [VISUAL_IDENTITY_GENERAL_PLAN.md](./VISUAL_IDENTITY_GENERAL_PLAN.md) | P0–P4 goals. No execution steps. |
| [console-ux-upgrade/UIUX_CONSOLE_FINDINGS.md](./console-ux-upgrade/UIUX_CONSOLE_FINDINGS.md) | Console UX audit — merge verdict, findings table, settings, marketing. **Next program baseline.** |
| [console-ux-upgrade/MOBILE_AND_LAYOUT_FINDINGS.md](./console-ux-upgrade/MOBILE_AND_LAYOUT_FINDINGS.md) | Mobile + layout audit — sidebar, hamburger, responsive tables, settings nav. **Next program baseline.** |
| [console-ux-upgrade/UIUX_CONSOLE_GENERAL_PLAN.md](./console-ux-upgrade/UIUX_CONSOLE_GENERAL_PLAN.md) | Combined general plan for both findings baselines. P0–P3. **No execution.** |
| [Architecture peer review](./reviews/architecture-peer-review/README.md) | Pass index. Latest: pass 3 — BLOCK create-execution-plan: no |
| [Execution peer review](./reviews/execution-peer-review/README.md) | Pass index. Latest: pass 2 — BLOCK phase-execution: no |

## Shipped — visual identity (P0–P4)

| Phase | Focus | File | Status |
|-------|-------|------|--------|
| P0 | Overlay, type `@theme`, force-dark, mark, toasts | [VISUAL_IDENTITY_P0_EXECUTION.md](./VISUAL_IDENTITY_P0_EXECUTION.md) | done `fb9615b` |
| P1 | Public landing + login split + voice | [VISUAL_IDENTITY_P1_EXECUTION.md](./VISUAL_IDENTITY_P1_EXECUTION.md) | done `2520e68` |
| P2 | Shell, settings/admin, connect chrome | [VISUAL_IDENTITY_P2_EXECUTION.md](./VISUAL_IDENTITY_P2_EXECUTION.md) | done `436c8a1` |
| P3 | Operator home `/reviewer` + dest retarget | [VISUAL_IDENTITY_P3_EXECUTION.md](./VISUAL_IDENTITY_P3_EXECUTION.md) | done `3ee2dda` |
| P4 | Reviewer scan, one-repo hop, doc-sync | [VISUAL_IDENTITY_P4_EXECUTION.md](./VISUAL_IDENTITY_P4_EXECUTION.md) | done |

## Next — UI/UX + mobile/layout upgrade

Two findings baselines ready for general plan + execution:

1. **[console-ux-upgrade/UIUX_CONSOLE_FINDINGS.md](./console-ux-upgrade/UIUX_CONSOLE_FINDINGS.md)** — 12 findings (2 Critical, 6 Major, 4 Minor):
   - C1: No explicit merge-readiness verdict; `'failure'` dead code in `deriveMergeConclusion`
   - C2: No severity summary bar; pipeline "Completed" competes with active findings
   - M1: Dense findings table — no search, filter, sort, detail panel, only Dismiss
   - M2: Weak loading states — generic "Loading…" and flash of contradictory status
   - M3: Settings overpromise unfinished work
   - M4: Team table hides Actions behind horizontal scroll
   - M5: Empty repo state has no refresh/help
   - M6: `/reviewer` logged-out flash (no dead links — landing is clean, code verified)
   - m1–m4: Terminology drift, opaque onboarding, contrast, danger zone

2. **[console-ux-upgrade/MOBILE_AND_LAYOUT_FINDINGS.md](./console-ux-upgrade/MOBILE_AND_LAYOUT_FINDINGS.md)** — 7 findings (1 Critical, 2 High, 4 Medium):
   - M1: No mobile sidebar/hamburger — app unnavigable on phones
   - M2: Sidebar lacks expand/collapse — wastes 224px
   - M3: Settings double-level nav (main sidebar + settings sidebar)
   - M4: Dashboard/settings containers too narrow (`max-w-lg`, 512px)
   - M5: Tables lack mobile card/stacked layout
   - M6: DevNoticeWidget button wrong color token
   - M7: No bottom tab bar on mobile

**Shared findings across both docs (plan together):**
- Findings table redesign (console M1 + layout M5) — toolbar, filters, detail panel, mobile cards
- Team table Actions column (console M4 + layout M5) — same responsive table pattern

**Next steps:**
1. ~~Architecture peer review on both findings baselines~~
2. ~~Combined general plan~~ → [console-ux-upgrade/UIUX_CONSOLE_GENERAL_PLAN.md](./console-ux-upgrade/UIUX_CONSOLE_GENERAL_PLAN.md) (P0–P3)
3. Architecture peer review on general plan
4. Per-phase execution plan
5. `phase-execution` LOOP

**Boundaries (same as VI-Q9):**
- No new APIs. No diff viewer. No workspace inbox.
- Build on existing routes, hooks, and types.
- VI-Q9 already shipped: dashboard redirect, reviewer as default, one-repo hop, QuietSelect.
- Next program extends: findings detail panel, merge verdict logic, filters/search, mobile responsiveness, settings nav flattening.
