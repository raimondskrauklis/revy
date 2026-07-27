# Post review-quality — GitHub surface

**Status:** P0–P4 code shipped on `feat/revy-github` — dogfood rows pending (human gates P0.4/P0.5, P1–P3 L1/L2/L3 on real PR push).

**Ship model:** All program docs in this folder — findings → general plan → execution P0–P4.

**Prerequisite:** review-quality RQ0–RQ9 on `main` (PR #50, #51 merged). Validation on **PR branch pushes** (pre-merge autostart).

---

## Program thesis

**Track A (now):** GitHub **look and feel** — L1 presence, L2 triage comment, L3 inline. Greptile on every Revy PR is the visual bar.

**Track B (later):** Review **intelligence** — STRUCT, recall, prompts. Not mixed into surface polish.

Engine (L4) is on `main`. PR reviews run on **branch `head_sha` before merge**; `main` deploy refreshes worker code only.

---

## Execution (LOOP order)

| Phase | File | Status |
|-------|------|--------|
| P0 — Worker + first dogfood | [GITHUB_SURFACE_P0_EXECUTION.md](./GITHUB_SURFACE_P0_EXECUTION.md) | code done · dogfood pending |
| P1 — L2 triage | [GITHUB_SURFACE_P1_EXECUTION.md](./GITHUB_SURFACE_P1_EXECUTION.md) | code done · dogfood pending |
| P2 — L1 presence | [GITHUB_SURFACE_P2_EXECUTION.md](./GITHUB_SURFACE_P2_EXECUTION.md) | code done · dogfood pending |
| P3 — L3 inline | [GITHUB_SURFACE_P3_EXECUTION.md](./GITHUB_SURFACE_P3_EXECUTION.md) | code done · dogfood pending |
| P4 — Doc sync | [GITHUB_SURFACE_P4_EXECUTION.md](./GITHUB_SURFACE_P4_EXECUTION.md) | done |

Index: [GITHUB_SURFACE_EXECUTION.md](./GITHUB_SURFACE_EXECUTION.md)

---

## Docs (order)

| Step | Doc | Purpose |
|------|-----|---------|
| 1 | [POST_REVIEW_QUALITY_FINDINGS.md](./POST_REVIEW_QUALITY_FINDINGS.md) | Platform research — **start here** |
| 2 | [POST_REVIEW_QUALITY_GENERAL_PLAN.md](./POST_REVIEW_QUALITY_GENERAL_PLAN.md) | Phases P0–P4 + dogfood rubric |
| 3 | [GITHUB_SURFACE_DOGFOOD.md](./GITHUB_SURFACE_DOGFOOD.md) | Per-PR push log |
| 4 | [GITHUB_SURFACE_EXECUTION.md](./GITHUB_SURFACE_EXECUTION.md) | Execution index + locked decisions |

---

## How we work

```text
push PR branch → Revy + Greptile autostart on same PR (pre-merge) → dogfood row → fix P1–P3 if needed → merge
```

`main` deploy updates worker code for **future** PR reviews. Reviews always target PR `head_sha`.

---

## Progress signal

**Dogfood rows** in [GITHUB_SURFACE_DOGFOOD.md](./GITHUB_SURFACE_DOGFOOD.md) — not git tags.

---

## Related

| Doc | Role |
|-----|------|
| [review-quality/](../review-quality/) | Shipped engine (RQ) |
| [PRODUCT_PATTERNS](../REVIEW_PIPELINE_PRODUCT_PATTERNS.md) | Category map |
| [GITHUB_WEBHOOK_DEV.md](../GITHUB_WEBHOOK_DEV.md) | R8 autostart contract |
