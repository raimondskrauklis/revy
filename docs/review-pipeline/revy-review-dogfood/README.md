# Revy review — cross-repo staging dogfood

**Status:** **findings baseline** (2026-07-31) — first case study [TenderPro PR #130](https://github.com/raimondskrauklis/tender_pro/pull/130); **next pass not started**.

**Thesis:** Finding-resolution (FR-DG*, wave C, wave D) proved closure **mechanisms** on Revy's own repo. Cross-repo dogfood exposes **operator UX**, **publish hygiene**, and **ingestion reliability** gaps that block trusting resolution metrics on real customer PRs.

| Doc | Purpose |
|-----|---------|
| [REVY_REVIEW_DOGFOOD_FINDINGS.md](./REVY_REVIEW_DOGFOOD_FINDINGS.md) | Gap catalog **RR-DG*** + recommended next wave |
| [REVY_REVIEW_DOGFOOD_STAGING_VALIDATION.md](./REVY_REVIEW_DOGFOOD_STAGING_VALIDATION.md) | TenderPro #130 evidence matrix + worker log |

## Relationship to prior iteration

| Program | What it proved | What cross-repo still breaks |
|---------|----------------|------------------------------|
| [finding-resolution](../finding-resolution/README.md) P0–P5 + wave C | Pass 1 stamp, Pass 2 close, G9 metrics, inline Option B | 0% resolution rate on TenderPro; threads stay open |
| [finding-resolution-dogfood](../finding-resolution-dogfood/README.md) FR-DG1/2 | Revy-repo probes, cohort hygiene | Different failure modes on long-lived external PRs |
| [judge transport](../judge/JUDGE_TRANSPORT_RELIABILITY_STAGING_VALIDATION.md) | Direct judge + T1 logging | **Works** on TenderPro (`judge_llm_request_completed` in worker log) |

**Operator notes** moved from [finding-resolution README § Revy PR review](../finding-resolution/README.md) — see findings **RR-DG7**.

## Next pass (planned — not execution)

One more product wave (**RR-W1**) scoped in findings § Recommended direction:

1. Idempotent PR revision ingest (**RR-DG3**)
2. Inline thread resolve reliability (**RR-DG1**)
3. Summary vs inline `head_sha` consistency (**RR-DG5**)
4. Compare-blocked cohort after merge-base disruption (**RR-DG4**)
5. Review false-positive rate on HEAD file content (**RR-DG6**)

General plan + execution files come after findings peer-review.
