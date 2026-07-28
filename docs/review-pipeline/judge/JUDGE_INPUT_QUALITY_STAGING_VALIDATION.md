# Judge input quality — staging validation

**Date:** pending deploy to `revy-staging`  
**Program:** [JUDGE_INPUT_QUALITY_EXECUTION.md](./waves/JUDGE_INPUT_QUALITY_EXECUTION.md) P5  
**Cross-program:** [FINDING_RESOLUTION_STAGING_VALIDATION.md](../finding-resolution/FINDING_RESOLUTION_STAGING_VALIDATION.md) — Pass 3 verification judge reuses discovery judge gateway + `file_patch_chars` (fill both on same dogfood PR when finding-resolution P2+ lands).

## Baseline (investigation 2026-07-28)

| Metric | Value |
|--------|-------|
| Judge-eligible findings with `evidence_snippet` | 53% (10/19) |
| Judge `user_prompt` avg chars | ~1,107 |
| Review `prompt` avg chars | ~147,211 |

## After deploy (fill on staging)

| Metric | Before | After | Notes |
|--------|--------|-------|-------|
| Evidence % on judge-eligible | 53% | _TBD_ | P2 SQL |
| Judge `user_prompt` avg chars | ~1,107 | _TBD_ | expect ↑ with `file_patch_chars` |
| `file_patch_chars` when present | 0 | _TBD_ | P3 manifest |
| Smoke script (gateway) | — | _TBD_ | `scripts/test_anthropic_judge_gateway.py` |
| Smoke script (direct) | — | _TBD_ | |

## Human gate

- [ ] SQL metrics recorded with date
- [ ] Smoke script result documented
- [ ] No regression in judge outcomes (small N)
- [ ] If finding-resolution P2 deployed: verification judge outcomes on same PR noted in [finding-resolution validation](../finding-resolution/FINDING_RESOLUTION_STAGING_VALIDATION.md) § P2
