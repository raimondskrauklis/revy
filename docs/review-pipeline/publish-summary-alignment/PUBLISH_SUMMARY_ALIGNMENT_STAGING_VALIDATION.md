# Publish summary alignment — staging validation

**Program:** [README.md](./README.md) · **Baseline:** [PUBLISH_SUMMARY_ALIGNMENT_FINDINGS.md](./PUBLISH_SUMMARY_ALIGNMENT_FINDINGS.md)

**Status:** **in progress** — PSA #62 deployed 2026-07-29; post-deploy dogfood PR open.

**Parallel tracks (do not block):**

| Track | Memo | Pass 2 status |
|-------|------|----------------|
| RCX | [REVIEW_ENGINEERING_CONTEXT_STAGING_VALIDATION.md](../review-engineering-context/REVIEW_ENGINEERING_CONTEXT_STAGING_VALIDATION.md) | **PASS** (`--rcx-gate` since #61 deploy) |
| Judge JSON contract | [JUDGE_JSON_CONTRACT_STAGING_VALIDATION.md](../judge-json-contract/JUDGE_JSON_CONTRACT_STAGING_VALIDATION.md) | unchanged |

## Deploy

| Item | Status |
|------|--------|
| `main` + PSA #62 merged | done (`880a949`, 2026-07-29T11:33:37Z) |
| Worker deploy | done — workflow `30448037218`, deploy finished **2026-07-29T11:38:12Z** |
| `--since` ISO (PSA window) | `2026-07-29T11:38:12Z` |

**Pre-deploy note:** PR #62 rev 4–5 reviews (11:12–11:33Z) ran **before** worker picked up PSA — issue comment still showed legacy `### Findings table` (RCX P6 shape). Do **not** count toward PSA pass criteria.

## Metrics script (PSA window)

```bash
cd backend
DATABASE_SSL_INSECURE=1 pipenv run sh -c \
  'python -m scripts.judge_json_contract_staging_metrics --since 2026-07-29T11:38:12Z --rcx-gate --json'
```

**Post-#62 deploy window (2026-07-29T11:38:12Z):** 0 completed review runs — **INCONCLUSIVE** until dogfood PR autostart completes.

## Dogfood PR

| PR | Role | Status |
|----|------|--------|
| #62 (merged) | Development — pre-deploy runs only | legacy format on rev 4–5 |
| **dogfood** (`chore/psa-staging-dogfood`) | Post-deploy 3-push validation | **open** |

## Dogfood steps

1. Open post-deploy dogfood PR (`backend/**` touch → autostart).
2. Push 1 — note issue comment block 1 + block 2 + inline count.
3. Fix one flagged item; push 2 — confirm G9, GH-1v2 collapse, block 2 shrink, merge line.
4. Push 3 — re-introduce issue; block 1 new finding; block 2 PR-wide state.

## Pass criteria

| Check | Pass |
|-------|------|
| Issue comment has `### This generation` + `### Still open on PR` | pending (post-deploy) |
| Check summary matches issue two-block tables (same rows) | pending |
| Confidence / merge use PR-wide open (not generation-only when prior open exists) | pending |
| Check conclusion may be `success` while merge warns (PSA-D12 — expected) | pending |
| Inline count ≈ generation publishable (not block 2 row count) | pending |
| Thread collapse after fix push | pending |
| `summary_json.generation_active_count` + `pr_active_count` populated | pending |

## Results (operator)

| Push | `head_sha` | Block 1 rows | Block 2 rows | Open inline threads | Merge line | Notes |
|------|------------|--------------|--------------|---------------------|------------|-------|
| — | — | — | — | — | — | PR #62 rev5 `56963dc` pre-deploy: **legacy** `### Findings table` — excluded |
| 1 | TBD | | | | | post-deploy dogfood PR push 1 |

**Operator sign-off:** pending post-deploy dogfood completion
