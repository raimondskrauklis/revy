# Publish summary alignment — staging validation

**Program:** [README.md](./README.md) · **Baseline:** [PUBLISH_SUMMARY_ALIGNMENT_FINDINGS.md](./PUBLISH_SUMMARY_ALIGNMENT_FINDINGS.md)

**Status:** **push 1 PASS** (2026-07-29) — post-deploy dogfood PR [#63](https://github.com/raimondskrauklis/revy/pull/63); push 2–3 pending for resolution/collapse dogfood.

**Parallel tracks (do not block):**

| Track | Memo | Status |
|-------|------|--------|
| RCX | [REVIEW_ENGINEERING_CONTEXT_STAGING_VALIDATION.md](../review-engineering-context/REVIEW_ENGINEERING_CONTEXT_STAGING_VALIDATION.md) | pass 2 **PASS** |
| Judge JSON contract | [JUDGE_JSON_CONTRACT_STAGING_VALIDATION.md](../judge-json-contract/JUDGE_JSON_CONTRACT_STAGING_VALIDATION.md) | unchanged |
| Meta workflow | [staging-validation/README.md](../staging-validation/README.md) | findings baseline |

## Deploy

| Item | Status |
|------|--------|
| `main` + PSA #62 merged | done (`880a949`, 2026-07-29T11:33:37Z) |
| Worker deploy | done — workflow `30448037218`, deploy finished **2026-07-29T11:38:12Z** |
| `--since` ISO (PSA window) | `2026-07-29T11:38:12Z` |

**Pre-deploy note:** PR #62 rev 4–5 reviews (11:12–11:33Z) ran **before** worker picked up PSA — issue comment showed legacy `### Findings table`. **Excluded** from PSA sign-off.

## Metrics script (PSA window)

```bash
cd backend
DATABASE_SSL_INSECURE=1 pipenv run sh -c \
  'python -m scripts.judge_json_contract_staging_metrics --since 2026-07-29T11:38:12Z --rcx-gate --json'
```

**Post-#62 deploy window (2026-07-29T11:38:12Z):** 2 completed runs (PR #63); `--rcx-gate` **PASS**; PSA `active_program` inject on both runs.

| Field | Value |
|-------|-------|
| `runs_with_context_stats` | 2 |
| `engineering_context_injected` | 2/2 |
| `engineering_context_bytes_p50` | 18662 |
| `diff_truncated_pct` | 0.0% (2 runs — INCONCLUSIVE for &lt;5% rule; 0 truncated) |

## Dogfood PR

| PR | Role | Status |
|----|------|--------|
| #62 (merged) | Feature PR — pre-deploy runs only | excluded |
| [#63](https://github.com/raimondskrauklis/revy/pull/63) | Post-deploy PSA dogfood | **open** — push 1 done |

## Dogfood steps

1. ~~Open post-deploy dogfood PR~~ — **done** (#63).
2. ~~Push 1 — two-block + inline + `summary_json`~~ — **done** (`ed95a5c`, rev 2).
3. **Push 2** — fix one flagged doc finding; confirm G9 prose, GH-1v2 thread collapse, block 2 shrink.
4. **Push 3** — re-introduce issue; block 1 new row; block 2 reflects PR-wide state.

## Pass criteria (push 1 — rev 2)

| Check | Pass | Evidence |
|-------|------|----------|
| Issue comment has `### This generation` + `### Still open on PR` | **yes** | Moonshot headings `### This generation findings` / `### Still open on PR findings` (substring match) |
| Check summary matches issue two-block tables (same rows) | **yes** | Check uses canonical headings; same 1 + 2 table rows |
| Confidence / merge use PR-wide open | **yes** | Narrative: "2 findings remain open on PR overall"; merge warns; `pr_active_count=2` |
| Check conclusion may differ from merge line (PSA-D12) | **yes** | Check `neutral`; merge warns with PR-wide open |
| Inline count ≈ generation publishable | **yes** | 1 inline thread; 1 generation table row |
| Thread collapse after fix push | pending | push 2 |
| `summary_json.generation_active_count` + `pr_active_count` | **yes** | `1` + `2` on run `019fadb4-…` |

## Results (operator)

| Push | `head_sha` | Block 1 rows | Block 2 rows | Open inline threads | Merge line | Notes |
|------|------------|--------------|--------------|---------------------|------------|-------|
| — | `56963dc` | — | — | — | — | PR #62 rev5 pre-deploy — **excluded** |
| 0 | `a6c03d1` | — | — | — | — | PR #63 rev1 — review completed; publish job not completed (superseded) |
| 1 | `ed95a5c` | 1 | 2 | 1 | Review warnings | rev 2; run `019fadb4-f777-7445-bdb6-9aeab9da9a2b`; comment [#5117353181](https://github.com/raimondskrauklis/revy/pull/63#issuecomment-5117353181) |

**`summary_json` sample (push 1):**

```json
{
  "confidence": 4,
  "active_count": 2,
  "generation_active_count": 1,
  "pr_active_count": 2,
  "head_sha": "ed95a5cfac33fe975bd42a20c013193254dbdb2f",
  "revision_number": 2
}
```

**Operator sign-off (push 1):** PSA two-block + PR-wide verdict + trace fields **PASS** on post-deploy worker. Full 3-push sign-off pending push 2–3.
