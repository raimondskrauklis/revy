# Revy review — cross-repo staging dogfood

**Status:** **general plan ready** (peer-review tightened 2026-07-31) — case study [TenderPro PR #130](https://github.com/raimondskrauklis/tender_pro/pull/130); execution **not started**.

**Thesis:** Finding-resolution (FR-DG*, wave C, wave D) proved closure **mechanisms** on Revy's own repo. Cross-repo dogfood exposes **operator UX**, **publish hygiene**, and **ingestion reliability** gaps that block trusting resolution metrics on real customer PRs.

| Doc | Purpose |
|-----|---------|
| [REVY_REVIEW_DOGFOOD_FINDINGS.md](./REVY_REVIEW_DOGFOOD_FINDINGS.md) | Gap catalog **RR-DG*** |
| [REVY_REVIEW_DOGFOOD_GENERAL_PLAN.md](./REVY_REVIEW_DOGFOOD_GENERAL_PLAN.md) | **RR-W1** phases R0–R5 (general — no execution steps) |
| [REVY_REVIEW_DOGFOOD_STAGING_VALIDATION.md](./REVY_REVIEW_DOGFOOD_STAGING_VALIDATION.md) | TenderPro #130 evidence + RR-V gates |

## Relationship to prior iteration

| Program | What it proved | What cross-repo still breaks |
|---------|----------------|------------------------------|
| [finding-resolution](../finding-resolution/README.md) P0–P5 + wave C | Pass 1 stamp, Pass 2 close, G9 metrics, inline Option B | 0% resolution rate on TenderPro; threads stay open |
| [finding-resolution-dogfood](../finding-resolution-dogfood/README.md) FR-DG1/2 | Revy-repo probes, cohort hygiene | Different failure modes on long-lived external PRs |
| [judge transport](../judge/JUDGE_TRANSPORT_RELIABILITY_STAGING_VALIDATION.md) | Direct judge + T1 logging | **Works** on TenderPro (`judge_llm_request_completed` in worker log) |

**Operator notes:** [finding-resolution README § Revy PR review](../finding-resolution/README.md) — findings **RR-DG7**.

## RR-W1 phases (LOOP order)

| Phase | Focus | Gaps |
|-------|--------|------|
| R0 | Baseline + RR-V gates | — |
| R1 | Revision ingest idempotency | RR-DG3, RR-DG11 |
| R2 | Thread resolve hygiene | RR-DG1, RR-DG7, RR-DG9 |
| R3 | Resolution stamp unblock (compare vs pairing vs line-region) | RR-DG4, RR-DG11 |
| R4 | HEAD contradiction suppression + inline 422 | RR-DG6, RR-DG2 |
| R5 | Cross-repo sign-off + publish coherence | RR-DG5, RR-DG10, RR-V1–V5 |

**Next:** `create-execution-plan` → `waves/REVY_REVIEW_DOGFOOD_EXECUTION.md`.
