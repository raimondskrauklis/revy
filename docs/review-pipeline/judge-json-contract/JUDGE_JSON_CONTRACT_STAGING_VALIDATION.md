# Judge JSON contract — staging validation

**Purpose:** Human gate for program closeout (P5). Fill after P3 deploy to staging.

**Baseline:** [JUDGE_JSON_CONTRACT_FINDINGS.md](./JUDGE_JSON_CONTRACT_FINDINGS.md) — 13/15 judge manifest candidates failed parse (2026-07-28).

---

## P4 gate (operator — before retry code ships)

| Check | Required | Result | Date |
|-------|----------|--------|------|
| P3 staging outcome persistence ≥95% | If yes → P4 doc-only skip | pending | — |

---

## Success metrics (post-P3 deploy)

| Metric | Baseline | Target | After deploy |
|--------|----------|--------|--------------|
| Judge candidates → valid `outcome` row | ~13% (2/15 manifest) | ≥95% | pending |
| Judge `user_prompt` p50 (snippet + line) | ~10k failed case | ≤2k | pending |
| RG-6 `judge_candidate_unpublished_missing_outcome` | frequent on parse fail | rare | pending |

---

## P0 smoke matrix (final)

| Path | `--structured` | Result | Notes |
|------|----------------|--------|-------|
| RTU gateway | no | pass | plain JSON 240–10k chars |
| RTU gateway | yes | fail | `structured_outputs not supported in your workspace` |
| Direct API | — | n/a locally | `anthropic_direct_enabled=False` |

**P3 lock:** `REVY_JUDGE_STRUCTURED_OUTPUT=false` on RTU; `parse_llm_json_object` + snippet-first prompts primary.

---

## SQL repro

See [FINDING_RESOLUTION_TECHNICAL_FINDINGS.md](../finding-resolution/FINDING_RESOLUTION_TECHNICAL_FINDINGS.md).

---

## Sign-off

| Role | Date | Outcome persistence % | Notes |
|------|------|----------------------|-------|
| Operator | — | — | pending dogfood PR after deploy |
