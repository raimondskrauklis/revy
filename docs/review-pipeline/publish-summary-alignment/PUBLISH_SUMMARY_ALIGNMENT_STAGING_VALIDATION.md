# Publish summary alignment — staging validation

**Program:** [README.md](./README.md) · **Baseline:** [PUBLISH_SUMMARY_ALIGNMENT_FINDINGS.md](./PUBLISH_SUMMARY_ALIGNMENT_FINDINGS.md)

**Status:** stub — fill after P1 deploy.

**Parallel tracks (do not block):**

| Track | Memo |
|-------|------|
| RCX pass 2 | [REVIEW_ENGINEERING_CONTEXT_STAGING_VALIDATION.md](../review-engineering-context/REVIEW_ENGINEERING_CONTEXT_STAGING_VALIDATION.md) |
| Judge JSON contract | [JUDGE_JSON_CONTRACT_STAGING_VALIDATION.md](../judge-json-contract/JUDGE_JSON_CONTRACT_STAGING_VALIDATION.md) |

## Deploy

| Item | Status |
|------|--------|
| `main` + PSA branch merged | pending |
| Worker deploy | pending |
| `--since` ISO | TBD at deploy |

## Dogfood steps

1. Open or reuse multi-push PR (class: #61).
2. Push 1 — note issue comment block 1 + block 2 + inline count.
3. Fix one flagged item; push 2 — confirm:
   - G9 “Since last push” mentions addressed count
   - GH-1v2 collapses inline thread
   - Block 2 shrinks (or “No open findings”)
   - Merge recommendation not “ready” while block 2 has errors
4. Push 3 — re-introduce issue; confirm block 1 shows new finding; block 2 reflects PR state.

## Pass criteria

| Check | Pass |
|-------|------|
| Issue comment has `### This generation` + `### Still open on PR` | |
| Check summary matches issue two-block tables (same rows) | |
| Confidence / merge use PR-wide open (not generation-only when prior open exists) | |
| Check conclusion may be `success` while merge warns (PSA-D12 — expected) | |
| Inline count ≈ generation publishable (not block 2 row count) | |
| Thread collapse after fix push | |

## Results (operator)

| Push | `head_sha` | Block 1 rows | Block 2 rows | Open inline threads | Merge line | Notes |
|------|------------|--------------|--------------|---------------------|------------|-------|
| | | | | | | |

**Operator sign-off:** _______________ **Date:** _______________
