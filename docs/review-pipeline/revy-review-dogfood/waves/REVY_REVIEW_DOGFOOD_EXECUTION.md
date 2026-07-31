# Revy review cross-repo dogfood — execution index

**Program:** [../README.md](../README.md) · **Baseline:** [REVY_REVIEW_DOGFOOD_FINDINGS.md](../REVY_REVIEW_DOGFOOD_FINDINGS.md) · **General plan:** [REVY_REVIEW_DOGFOOD_GENERAL_PLAN.md](../REVY_REVIEW_DOGFOOD_GENERAL_PLAN.md)

**Authority:** [finding-resolution FINDINGS](../../finding-resolution/FINDING_RESOLUTION_FINDINGS.md) · [BACKEND_SCRIPTS_RUNBOOK.md](../../../utils/BACKEND_SCRIPTS_RUNBOOK.md)

**Goal:** Cross-repo operator trust — idempotent ingest, publish hygiene, resolution stamp, HEAD suppression — validated on TenderPro #130 class PRs.

**Branch:** `docs/revy-review-dogfood-findings` (docs + RR-W1 implementation in one PR — [README](../README.md))

## Out of scope (program)

- FR-CS4 Pass 3 supersede timing
- Judge transport (RR-DG8 — closed #75)
- Moonshot prompt retrain
- Frontend / i18n
- Product merge gate on resolution rate until **R5** (RR-Q4) — **defer** locked

## How we work (locked)

```text
R0 → R1 → R2 → R3 → R4 → R5
each phase: implement → pytest gate (when code) → Bugbot → commit
R3 may overlap R4 after R1 if suppression is independent — LOOP order still R3 before R4 commit
```

**Gap IDs (RR-DG*):** findings catalog. **R0–R5:** program phases below.

## Decisions locked for execution

- **RR-Q1:** Extend `github_pull_requests.py`, `github_publish.py`, `github_resolution_metrics.py`, `github_publish_formatter.py` — no parallel closure system.
- **RR-Q4:** Defer product FAIL on 0% resolution — **locked defer** (R5 recommendation).
- **RR-Q5:** R0 locks app dedupe vs migration; R1 implements locked choice only.
- **RR-DG4:** R0 tags root cause (API fail | pairing | line-region | stale); R3 implements per tag.
- **RG-6:** Unchanged.
- **Migrations:** Only if R0 locks RR-Q5 unique on `(pull_request_id, head_sha)` — hand-written Alembic.

## LOOP order

| Phase | Focus | Execution | Status |
|-------|--------|-----------|--------|
| R0 — Baseline | Evidence + RR-DG4 hypothesis + RR-V fixtures | [REVY_REVIEW_DOGFOOD_R0_EXECUTION.md](./REVY_REVIEW_DOGFOOD_R0_EXECUTION.md) | done |
| R1 — Ingest | Revision idempotency | [REVY_REVIEW_DOGFOOD_R1_EXECUTION.md](./REVY_REVIEW_DOGFOOD_R1_EXECUTION.md) | done `deda3c9` |
| R2 — Publish hygiene | Thread resolve taxonomy | [REVY_REVIEW_DOGFOOD_R2_EXECUTION.md](./REVY_REVIEW_DOGFOOD_R2_EXECUTION.md) | done `deda3c9` |
| R3 — Resolution | Stamp unblock | [REVY_REVIEW_DOGFOOD_R3_EXECUTION.md](./REVY_REVIEW_DOGFOOD_R3_EXECUTION.md) | done `deda3c9` |
| R4 — Accuracy | HEAD suppression + inline 422 | [REVY_REVIEW_DOGFOOD_R4_EXECUTION.md](./REVY_REVIEW_DOGFOOD_R4_EXECUTION.md) | done `deda3c9` |
| R5 — Sign-off | Staging RR-V + doc sync | [REVY_REVIEW_DOGFOOD_R5_EXECUTION.md](./REVY_REVIEW_DOGFOOD_R5_EXECUTION.md) | done `b8a589e` |

**Peer review:** Findings + general plan (2026-07-31); execution files peer-reviewed + tightened same day (RR-V gate order, R1 collision retry, R3 tag map, R4 reconcile hook).

| Phase | Merge SHA |
|-------|-----------|
| R0 | `f799dbe` |
| R1 | `cb6a1d1` |
| R2 | `2e7c4de` |
| R3 | `1ab7e4f` |
| R4 | `9777aee` |
| R5 | `b8a589e` ([#80](https://github.com/raimondskrauklis/revy/pull/80)) |
