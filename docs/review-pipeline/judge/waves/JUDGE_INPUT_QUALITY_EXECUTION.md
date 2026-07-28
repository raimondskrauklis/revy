# Judge input quality — execution index

**Program:** [../README.md](../README.md) · **Baseline:** [JUDGE_INPUT_INVESTIGATION_FINDINGS.md](../JUDGE_INPUT_INVESTIGATION_FINDINGS.md) · **General plan:** [JUDGE_INPUT_QUALITY_GENERAL_PLAN.md](../JUDGE_INPUT_QUALITY_GENERAL_PLAN.md)

**Authority:** [REVIEW_PIPELINE_FINDINGS.md](../../REVIEW_PIPELINE_FINDINGS.md) R5-Q3 · [REVIEW_QUALITY_R4_EVIDENCE_JUDGE_GENERAL_PLAN.md](../../review-quality/REVIEW_QUALITY_R4_EVIDENCE_JUDGE_GENERAL_PLAN.md) (E1/E2)

**Goal:** Moonshot discovers on full diff; Claude **verifies** one Moonshot claim per call with scoped patch evidence — not a second full-PR review.

**Branch:** `feat/judge-input-quality` (merge `feat/anthropic-judge-gateway` first if gateway not on `main`)

## How we work (locked)

```text
P0 → P1 → P2 → P3 → P4 → P5
each phase: implement → pytest gate → Bugbot → commit
```

**Gap IDs (J-*):** findings catalog. **P0–P5:** program phases below.

## Decisions locked for execution

- **R5-Q3:** Escalation gate unchanged — `error`/`critical`, or `security` + `severity ≥ warning`; max 10/run; skip when `judge_llm_enabled()` false.
- **No full PR diff to judge** — per-finding file patch capped (`JUDGE_FILE_PATCH_MAX_CHARS`, default 8192).
- **J-8:** `fetch_compare_patches_by_file` in `github_compare_patches.py` — `revision.base_sha` → `revision.head_sha` (not resolution-metrics delta).
- **J-4:** PR body via GitHub API at review time — **no** `body` DB column / migration in this program.
- **J-10 v1:** `modified` outcome → `group.severity = warning` only; no message/title edits in this program.
- **Gateway:** Do not re-implement — ship from `feat/anthropic-judge-gateway` if absent on `main`.
- **i18n:** backend-only — no new frontend strings.
- **Migrations:** none for P0–P3/P5; P4 uses GitHub API fetch — no `body` column on `github_pull_requests`.

## LOOP order

| Phase | Focus | Execution | Status |
|-------|--------|-----------|--------|
| P0 — Primitives | Hunk/snippet helpers + caps | [JUDGE_INPUT_QUALITY_P0_EXECUTION.md](./JUDGE_INPUT_QUALITY_P0_EXECUTION.md) | pending |
| P1 — Verifier prompts | Moonshot claim-only contract + tests | [JUDGE_INPUT_QUALITY_P1_EXECUTION.md](./JUDGE_INPUT_QUALITY_P1_EXECUTION.md) | pending |
| P2 — Review ingest | Evidence coverage + path/line fixes | [JUDGE_INPUT_QUALITY_P2_EXECUTION.md](./JUDGE_INPUT_QUALITY_P2_EXECUTION.md) | pending |
| P3 — Judge context | Compare re-fetch + patch in prompt | [JUDGE_INPUT_QUALITY_P3_EXECUTION.md](./JUDGE_INPUT_QUALITY_P3_EXECUTION.md) | pending |
| P4 — Moonshot PR body | Wire `pull_request.body` | [JUDGE_INPUT_QUALITY_P4_EXECUTION.md](./JUDGE_INPUT_QUALITY_P4_EXECUTION.md) | pending |
| P5 — Staging gate | Validation memo + doc sync | [JUDGE_INPUT_QUALITY_P5_EXECUTION.md](./JUDGE_INPUT_QUALITY_P5_EXECUTION.md) | pending |

**Peer review:** incorporated 2026-07-28 — P4 API fetch (no migration), P2 `_parse_finding_row`, P3 module path locked, findings J-8 aligned.

**Peer review:** run `execution-peer-review` again if execution files change materially.
