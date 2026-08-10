# Staging validation — program index

**Status:** **findings baseline** — operator workflow for post-deploy dogfood PRs + parallel metrics tracks.

**Gap:** Per-program `*_STAGING_VALIDATION.md` memos exist, but there is no shared contract for **when** to run validation, **how** to open dogfood PRs, or **how** to run metrics in parallel as deploy velocity increases.

**Thesis:** Treat staging validation as a **repeatable operator program** — chore dogfood PRs, deploy-boundary `--since` windows, shared metrics script, per-program pass tables — so multiple shipped features can be verified in parallel without conflating pre/post-deploy evidence.

| Doc | Purpose |
|-----|---------|
| [STAGING_VALIDATION_FINDINGS.md](./STAGING_VALIDATION_FINDINGS.md) | Baseline — gaps, SV-Q registry, deploy-window rules, parallel-track model |
| [TEMPLATE_STAGING_VALIDATION.md](./TEMPLATE_STAGING_VALIDATION.md) | Stub for new per-program `*_STAGING_VALIDATION.md` memos |
| [TEMPLATE_VALIDATION_INDEX.md](./TEMPLATE_VALIDATION_INDEX.md) | Optional index stub (this README is the live index on Revy) |
| *(later)* `STAGING_VALIDATION_GENERAL_PLAN.md` | Phased rollout (script extensions, memo templates, CI hooks) |
| *(later)* `waves/STAGING_VALIDATION_EXECUTION.md` | LOOP when implementation is needed |

## Active dogfood PRs

| PR | Program | Branch | Status |
|----|---------|--------|--------|
| *(open)* | Model run capture (post-#96) | `chore/mrc-staging-dogfood` | [#97](https://github.com/raimondskrauklis/revy/pull/97) — **MRC-P0 PASS** push 1 |
| *(open)* | Agent workflow pack E2E | `chore/agent-workflow-e2e-validation` | [#73](https://github.com/raimondskrauklis/revy/pull/73) push 1 |
| [#87](https://github.com/raimondskrauklis/revy/pull/87) | PR summary rollup (post-#85) | `chore/psr-staging-dogfood` | **sign-off PASS** — pushes 1–2 |
| *(open)* | Finding resolution dogfood | `chore/finding-resolution-staging-dogfood` | P0 pushed — staging validation in progress |
| [#63](https://github.com/raimondskrauklis/revy/pull/63) | PSA post-#62 deploy | `chore/psa-staging-dogfood` | **sign-off complete** — merged |

## Next validation PRs

| Program | Branch | Findings |
|---------|--------|----------|
| Model run capture (post-#96) | `chore/mrc-staging-dogfood` | [MODEL_RUN_CAPTURE_STAGING_VALIDATION.md](../models/model-run-capture/MODEL_RUN_CAPTURE_STAGING_VALIDATION.md) |
| PR summary rollup (post-#85 deploy) | `chore/psr-staging-dogfood` | **done** — [#87](https://github.com/raimondskrauklis/revy/pull/87) PASS |
| Finding resolution dogfood | `chore/finding-resolution-staging-dogfood` | [FINDING_RESOLUTION_DOGFOOD_FINDINGS.md](../finding-resolution-dogfood/FINDING_RESOLUTION_DOGFOOD_FINDINGS.md) |
| Moonshot formatter signature | `chore/moonshot-formatter-signature` | MR-DG1 in same doc |

## Related per-program validation memos

| Program | Memo |
|---------|------|
| Publish summary alignment | [PUBLISH_SUMMARY_ALIGNMENT_STAGING_VALIDATION.md](../publish-summary-alignment/PUBLISH_SUMMARY_ALIGNMENT_STAGING_VALIDATION.md) |
| Review engineering context | [REVIEW_ENGINEERING_CONTEXT_STAGING_VALIDATION.md](../review-engineering-context/REVIEW_ENGINEERING_CONTEXT_STAGING_VALIDATION.md) |
| Judge JSON contract | [JUDGE_JSON_CONTRACT_STAGING_VALIDATION.md](../judge-json-contract/JUDGE_JSON_CONTRACT_STAGING_VALIDATION.md) |
| Finding resolution | [FINDING_RESOLUTION_STAGING_VALIDATION.md](../finding-resolution/FINDING_RESOLUTION_STAGING_VALIDATION.md) |
| PR summary rollup | [PR_SUMMARY_ROLLUP_STAGING_VALIDATION.md](../pr-summary-rollup/PR_SUMMARY_ROLLUP_STAGING_VALIDATION.md) |
| Model run capture | [MODEL_RUN_CAPTURE_STAGING_VALIDATION.md](../models/model-run-capture/MODEL_RUN_CAPTURE_STAGING_VALIDATION.md) |
| Agent workflow pack E2E | [AGENT_WORKFLOW_PACK_E2E_VALIDATION.md](./AGENT_WORKFLOW_PACK_E2E_VALIDATION.md) |

## Shared tooling

| Tool | Path |
|------|------|
| Staging metrics + RCX gate | `backend/scripts/judge_json_contract_staging_metrics.py` |
| Model run capture gate | `backend/scripts/model_run_capture_staging_metrics.py` |
| Pipeline observability gate | `backend/scripts/pipeline_observability_staging_metrics.py` |
| Generation lifecycle gate | `backend/scripts/generation_lifecycle_staging_metrics.py` |
| SSOT / Greptile gate | `backend/scripts/generate_greptile_files_from_review_context.py` + `tests/unit/test_generate_greptile_files.py` |

**Next step:** merge #63 → [finding-resolution dogfood](../finding-resolution-dogfood/README.md) (one push per agent cycle).
