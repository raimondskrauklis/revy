# Publish summary alignment — staging validation

**Program:** [README.md](./README.md) · **Baseline:** [PUBLISH_SUMMARY_ALIGNMENT_FINDINGS.md](./PUBLISH_SUMMARY_ALIGNMENT_FINDINGS.md)

**Status:** **push 1–2 PASS**, **push 3 mixed** (2026-07-29) — post-deploy dogfood PR [#63](https://github.com/raimondskrauklis/revy/pull/63); G9/collapse **not observed** on fix push.

**Validation priority:** exercise two-block / G9 / collapse / `summary_json` on staging; fixing Greptile doc nits is **out of scope**.

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

**Post-#62 deploy window (2026-07-29T11:38:12Z):** 5 completed publishes (PR #63 rev 2–4, 6); `--rcx-gate` **PASS**; PSA `active_program` inject on all runs.

| Field | Value |
|-------|-------|
| `runs_with_context_stats` | 5 |
| `engineering_context_injected` | 5/5 |
| `engineering_context_bytes_p50` | 18662 |
| `diff_truncated_pct` | 0.0% (5 runs — INCONCLUSIVE for &lt;5% rule; 0 truncated) |

## Dogfood PR

| PR | Role | Status |
|----|------|--------|
| #62 (merged) | Feature PR — pre-deploy runs only | excluded |
| [#63](https://github.com/raimondskrauklis/revy/pull/63) | Post-deploy PSA dogfood | **open** — push 3 done; G9/collapse gap logged |

## Dogfood steps

1. ~~Open post-deploy dogfood PR~~ — **done** (#63).
2. ~~Push 1 — two-block + inline + `summary_json`~~ — **done** (`ed95a5c`, rev 2).
3. ~~Push 2 — probe files + behavior tests~~ — **done** (`d52e790`, rev 4).
4. ~~Push 3 — wire marker + drop bogus test call~~ — **done** (`61f8b5f` code; published on rev 6 `0e0e60a` after docs commit superseded rev 5).
5. **Push 4 (optional)** — re-introduce unused marker; block 1 shows new generation row again.

## Pass criteria (push 1 — rev 2)

| Check | Pass | Evidence |
|-------|------|----------|
| Issue comment has `### This generation` + `### Still open on PR` | **yes** | Moonshot headings `### This generation findings` / `### Still open on PR findings` (substring match) |
| Check summary matches issue two-block tables (same rows) | **yes** | Check uses canonical headings; same 1 + 2 table rows |
| Confidence / merge use PR-wide open | **yes** | Narrative: "2 findings remain open on PR overall"; merge warns; `pr_active_count=2` |
| Check conclusion may differ from merge line (PSA-D12) | **yes** | Check `neutral`; merge warns with PR-wide open |
| Inline count ≈ generation publishable | **yes** | 1 inline thread; 1 generation table row |
| Thread collapse after fix push | **no** | push 3 — FP inline orphaned (`line: null`) but still in block 2; 3 new probe inlines added |
| `summary_json.generation_active_count` + `pr_active_count` | **yes** | `1` + `2` on run `019fadb4-…` |

## Results (operator)

| Push | `head_sha` | Block 1 rows | Block 2 rows | Open inline threads | Merge line | Notes |
|------|------------|--------------|--------------|---------------------|------------|-------|
| — | `56963dc` | — | — | — | — | PR #62 rev5 pre-deploy — **excluded** |
| 0 | `a6c03d1` | — | — | — | — | PR #63 rev1 — review completed; publish job not completed (superseded) |
| 1 | `ed95a5c` | 1 | 2 | 1 | Review warnings | rev 2; run `019fadb4-f777-7445-bdb6-9aeab9da9a2b`; comment [#5117353181](https://github.com/raimondskrauklis/revy/pull/63#issuecomment-5117353181) |
| 1b | `c57a9c0` | 1 | 3 | 3 | Review warnings | rev 3; run `019fadb9-…`; `pr_active_count=3` (doc findings accumulated) |
| 2 | `d52e790` | 1 | 4 | 4 | Fix before merge | rev 4; run `019fadbe-…`; gen=error on `format_summary_comment` kwarg (Moonshot FP); unused marker **not** flagged |
| 3 | `0e0e60a` | 3 | 7 | 6 | Fix before merge | rev 6 publish (rev 5 `61f8b5f` `skipped_not_head`); run `019fadc6-…`; G9 `n/a`, resolution `0/0`; `pr_active_count` 4→7 |

## Pass criteria (push 3 — rev 6)

| Check | Pass | Evidence |
|-------|------|----------|
| G9 addressed prose after fix | **no** | `Since last push: n/a`; `resolution.addressed: 0` |
| Resolution metrics show closed-as-fixed | **no** | `Closed as fixed: 0`; rate `0.0% (0/0 prior active)` |
| Block 2 shrink vs push 2 | **no** | `pr_active_count` 4 → 7 |
| Stale FP removed from block 2 | **no** | `format_summary_comment` kwarg error still listed |
| Inline thread collapse (GH-1v2) | **no** | Old test inline `line: null` (orphaned); 3 new probe inlines |
| Two-block shape + trace fields | **yes** | Block 1=3, block 2=7; `generation_active_count=3`, `pr_active_count=7` |

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

**`summary_json` sample (push 2 / rev 4):**

```json
{
  "confidence": 3,
  "active_count": 4,
  "generation_active_count": 1,
  "pr_active_count": 4,
  "head_sha": "d52e790ffd4f71b69ea84126316e5cd1f3b0549f",
  "revision_number": 4
}
```

**Operator notes (push 2):** Two-block shape holds; `pr_active_count` tracks doc findings across pushes. Generation finding was Moonshot false positive on valid `generation_groups` kwarg — not the unused-marker probe. Push 3 targets collapse of that inline + marker wire.

**Operator notes (push 3):** Fix push did **not** exercise G9/collapse as expected. Likely factors: (1) rev 5 superseded before publish — resolution manifest may have lost prior-active pairing (`0/0 prior active`); (2) removed test code left stale fingerprint in block 2; (3) probe refactor surfaced 3 new generation findings instead of shrinking PR-wide set. **Action item:** investigate resolution pairing on rapid successive pushes + stale group retirement (finding-resolution track).

**`summary_json` sample (push 3 / rev 6):**

```json
{
  "confidence": 3,
  "active_count": 7,
  "generation_active_count": 3,
  "pr_active_count": 7,
  "head_sha": "0e0e60a2a1647a4a772aaf62db9b3bf1f9b44031",
  "revision_number": 6,
  "resolution": {
    "addressed": 0,
    "still_open": 0,
    "human_dismissed": 0,
    "judge_dismissed": 0,
    "verification_dismissed": 0
  }
}
```

**Operator sign-off (push 1):** PSA two-block + PR-wide verdict + trace fields **PASS** on post-deploy worker.

**Operator sign-off (push 3):** Two-block surface **PASS**; G9 / collapse / block-2 shrink **FAIL** — log for finding-resolution follow-up. PSA core (#62) ship criteria met for formatter shape; resolution lifecycle needs separate dogfood.
