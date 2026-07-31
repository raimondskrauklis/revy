# Revy review — cross-repo staging dogfood

**Status:** **RR-W1 complete** — shipped `deda3c9` ([#78](https://github.com/raimondskrauklis/revy/pull/78)); R5 sign-off ([#79](https://github.com/raimondskrauklis/revy/pull/79)) Revy rev 1 PASS.

**Thesis:** Finding-resolution proved closure **mechanisms** on Revy's own repo. TenderPro #130 supplied **real-world symptom evidence**; all RR-V proofs and sign-off run on **`raimondskrauklis/revy`** staging dogfood PRs.

| Doc | Purpose |
|-----|---------|
| [REVY_REVIEW_DOGFOOD_FINDINGS.md](./REVY_REVIEW_DOGFOOD_FINDINGS.md) | Gap catalog **RR-DG*** |
| [REVY_REVIEW_DOGFOOD_GENERAL_PLAN.md](./REVY_REVIEW_DOGFOOD_GENERAL_PLAN.md) | **RR-W1** phases R0–R5 (general — no execution steps) |
| [waves/REVY_REVIEW_DOGFOOD_EXECUTION.md](./waves/REVY_REVIEW_DOGFOOD_EXECUTION.md) | LOOP index + phase execution files |
| [REVY_REVIEW_DOGFOOD_STAGING_VALIDATION.md](./REVY_REVIEW_DOGFOOD_STAGING_VALIDATION.md) | RR-V gates + Revy-repo staging evidence |

## Relationship to prior iteration

| Program | What it proved | What RR-W1 fixed |
|---------|----------------|------------------|
| [finding-resolution](../finding-resolution/README.md) P0–P5 + wave C | Pass 1 stamp, Pass 2 close, G9 metrics, inline Option B | Resolution stamp unblock (R3) |
| [finding-resolution-dogfood](../finding-resolution-dogfood/README.md) FR-DG1/2 | Revy-repo probes, cohort hygiene | Ingest idempotency (R1) |
| [judge transport](../judge/JUDGE_TRANSPORT_RELIABILITY_STAGING_VALIDATION.md) | Direct judge + T1 logging | Unchanged — worked cross-repo |

**External evidence (not validation venue):** TenderPro #130 — operator matrix + worker log in `misc/`.

## RR-W1 phases (LOOP order)

| Phase | Focus | Gaps | Execution | Status |
|-------|--------|------|-----------|--------|
| R0 | Baseline + RR-V gates | — | [R0](./waves/REVY_REVIEW_DOGFOOD_R0_EXECUTION.md) | done |
| R1 | Revision ingest idempotency | RR-DG3, RR-DG11 | [R1](./waves/REVY_REVIEW_DOGFOOD_R1_EXECUTION.md) | done |
| R2 | Thread resolve hygiene | RR-DG1, RR-DG7, RR-DG9 | [R2](./waves/REVY_REVIEW_DOGFOOD_R2_EXECUTION.md) | done |
| R3 | Resolution stamp unblock | RR-DG4, RR-DG11 | [R3](./waves/REVY_REVIEW_DOGFOOD_R3_EXECUTION.md) | done |
| R4 | HEAD suppression + inline 422 | RR-DG6, RR-DG2 | [R4](./waves/REVY_REVIEW_DOGFOOD_R4_EXECUTION.md) | done |
| R5 | Staging sign-off | RR-V1–V5 | [R5](./waves/REVY_REVIEW_DOGFOOD_R5_EXECUTION.md) | done |

**RR-V gate order:** V1 ingest · V2 resolution rate · V3 publish SHA parity · V4 thread taxonomy · V5 matrix suppression — all **PASS** on Revy PR #78/#79 ([validation memo](./REVY_REVIEW_DOGFOOD_STAGING_VALIDATION.md)).

**Ship SHA:** `deda3c9` ([#78](https://github.com/raimondskrauklis/revy/pull/78))
