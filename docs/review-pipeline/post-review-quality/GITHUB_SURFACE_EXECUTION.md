# GitHub surface — execution index

**Program:** [README.md](./README.md) · **Baseline:** [POST_REVIEW_QUALITY_FINDINGS.md](./POST_REVIEW_QUALITY_FINDINGS.md) · **General plan:** [POST_REVIEW_QUALITY_GENERAL_PLAN.md](./POST_REVIEW_QUALITY_GENERAL_PLAN.md)

**Authority:** [GITHUB_WEBHOOK_DEV.md](../GITHUB_WEBHOOK_DEV.md) (R8 autostart pre-merge) · [REVIEW_PIPELINE_PRODUCT_PATTERNS.md](../REVIEW_PIPELINE_PRODUCT_PATTERNS.md) · [GITHUB_APP_SETUP.md](../../utils/GITHUB_APP_SETUP.md)

**Goal:** Ship L1–L3 GitHub presentation (Greptile-comparable surface). Track B (recall/STRUCT) is out of scope.

## How we work (locked)

```text
PR branch push → pull_request opened|synchronize → index head_sha → review → publish on open PR
Greptile autostart in parallel on same PR (pre-merge)
main deploy → updates worker image only (publisher code for next PR pushes)
Dogfood row → GITHUB_SURFACE_DOGFOOD.md per push
```

## Decisions locked for execution

- **PQ-6:** No artificial smoke PRs — dogfood on real branch pushes.
- **PQ-7:** Visual (L1–L3) before intelligence tuning (track B).
- **G3:** Compact check `output.summary`; full triage on issue comment.
- **L2 v1 bar:** `build_pr_review_comment_fallback` — Moonshot narrative optional (H2).
- **L3 v1:** Table shows all severities; inline includes error/critical/warning/info when line-accurate (P3).
- **H3:** Empty Revy vs Greptile on code → investigate track B later — do not block L2/L3 polish.
- **i18n:** GitHub markdown English v1; EN+LV only for new app / ack strings.
- **Migrations:** None expected; hand-written only if schema required.
- **Tags:** Optional deploy bookmarks — not LOOP gates.

## PR review context (Greptile + Bugbot)

Ship in **P0.1** (first program commit):

| Tool | Files |
|------|--------|
| Greptile | `.greptile/files.json` — post-review-quality findings + general plan + execution index |
| Bugbot | `.cursor/BUGBOT.md` — links to same docs; scope `backend/**` publish/formatter |

Per-phase commits: code + README status row — not full findings rewrite each push.

## LOOP order

**Linear:** P0 → P1 → P2 → P3 → P4

| Phase | Focus | Execution | Status |
|-------|--------|-----------|--------|
| P0 — Worker + first dogfood | Ops checklist, publish path, first row | [GITHUB_SURFACE_P0_EXECUTION.md](./GITHUB_SURFACE_P0_EXECUTION.md) | code done · dogfood pending |
| P1 — L2 triage | Issue comment + G3 split | [GITHUB_SURFACE_P1_EXECUTION.md](./GITHUB_SURFACE_P1_EXECUTION.md) | code done · dogfood pending |
| P2 — L1 presence | G10 lifecycle + optional ack | [GITHUB_SURFACE_P2_EXECUTION.md](./GITHUB_SURFACE_P2_EXECUTION.md) | code done · dogfood pending |
| P3 — L3 inline | Warnings on diff | [GITHUB_SURFACE_P3_EXECUTION.md](./GITHUB_SURFACE_P3_EXECUTION.md) | code done · dogfood pending |
| P4 — Doc sync | PRODUCT_PATTERNS, dogfood, README | [GITHUB_SURFACE_P4_EXECUTION.md](./GITHUB_SURFACE_P4_EXECUTION.md) | done |

**Peer review:** `execution-peer-review` on P0–P4 (2026-07-27) — medium findings addressed (named tests, PRODUCT_PATTERNS row map, human vs pytest gates). Re-review after edits if desired.

**Dogfood log:** [GITHUB_SURFACE_DOGFOOD.md](./GITHUB_SURFACE_DOGFOOD.md)
