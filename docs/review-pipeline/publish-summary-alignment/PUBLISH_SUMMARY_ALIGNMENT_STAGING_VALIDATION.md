# Publish summary alignment — staging validation

**Program:** [README.md](./README.md) · **Baseline:** [PUBLISH_SUMMARY_ALIGNMENT_FINDINGS.md](./PUBLISH_SUMMARY_ALIGNMENT_FINDINGS.md)

**Status:** **PSA formatter sign-off PASS** — dogfood complete on [#63](https://github.com/raimondskrauklis/revy/pull/63) (pushes 1–4). G9/collapse deferred to finding-resolution dogfood.

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
# Staging operator only — droplet DB uses a self-signed cert; not for production.
DATABASE_SSL_INSECURE=1 pipenv run sh -c \
  'python -m scripts.judge_json_contract_staging_metrics --since 2026-07-29T11:38:12Z --rcx-gate --json'
```

**Post-#62 deploy window (2026-07-29T11:38:12Z):** 6 completed publishes (PR #63 rev 2–4, 6–8); `--rcx-gate` **PASS**.

| Field | Value |
|-------|-------|
| `runs_with_context_stats` | 8 |
| `engineering_context_injected` | 8/8 |
| `engineering_context_bytes_p50` | 18662 |
| `diff_truncated_pct` | 0.0% |

## Dogfood PR

| PR | Role | Status |
|----|------|--------|
| #62 (merged) | Feature PR — pre-deploy runs only | excluded |
| [#63](https://github.com/raimondskrauklis/revy/pull/63) | Post-deploy PSA dogfood | **ready to merge** |

## Dogfood steps

1. ~~Open post-deploy dogfood PR~~ — **done** (#63).
2. ~~Push 1 — two-block + inline + `summary_json`~~ — **done** (`ed95a5c`, rev 2).
3. ~~Push 2 — probe files + behavior tests~~ — **done** (`d52e790`, rev 4); probes removed in cleanup commit.
4. ~~Push 3 — wire marker + drop bogus test call~~ — **done** (`61f8b5f` code; published on rev 6 `0e0e60a`).
5. ~~Push 4 — unwired marker~~ — **done** (`d84b83b`, rev 8).
6. **Post-merge** — `chore/finding-resolution-staging-dogfood`; one push per agent cycle.

## Pass criteria (push 1 — rev 2)

| Check | Pass | Evidence |
|-------|------|----------|
| Issue comment has `### This generation` + `### Still open on PR` | **yes** | Moonshot headings `### This generation findings` / `### Still open on PR findings` (substring match) |
| Check summary matches issue two-block tables (same rows) | **yes** | Check uses canonical headings; same 1 + 2 table rows |
| Confidence / merge use PR-wide open | **yes** | Narrative: "2 findings remain open on PR overall"; merge warns; `pr_active_count=2` |
| Check conclusion may differ from merge line (PSA-D12) | **yes** | Check `neutral`; merge warns with PR-wide open |
| Inline count ≈ generation publishable | **yes** | 1 inline thread; 1 generation table row |
| Thread collapse after fix push | **no** | push 3 — deferred to finding-resolution |
| `summary_json.generation_active_count` + `pr_active_count` | **yes** | `1` + `2` on run `019fadb4-…` |

## Results (operator)

| Push | `head_sha` | Block 1 rows | Block 2 rows | Open inline threads | Merge line | Notes |
|------|------------|--------------|--------------|---------------------|------------|-------|
| — | `56963dc` | — | — | — | — | PR #62 rev5 pre-deploy — **excluded** |
| 0 | `a6c03d1` | — | — | — | — | PR #63 rev1 — publish superseded |
| 1 | `ed95a5c` | 1 | 2 | 1 | Review warnings | rev 2; run `019fadb4-…` |
| 1b | `c57a9c0` | 1 | 3 | 3 | Review warnings | rev 3; `pr_active_count=3` |
| 2 | `d52e790` | 1 | 4 | 4 | Fix before merge | rev 4; Moonshot FP on `generation_groups` kwarg |
| 3 | `0e0e60a` | 3 | 7 | 6 | Fix before merge | rev 6; G9 `n/a`, resolution `0/0` |
| 4 | `d84b83b` | 2 | 8 | 9 | Fix before merge | rev 8; GH≡DB parity **yes**; `gen=2`, `pr=8` |

## Pass criteria (push 4 — rev 8)

| Check | Pass | Evidence |
|-------|------|----------|
| `generation_active_count` ≥ 1 | **yes** | `2` (DB + issue comment + check run) |
| Two-block shape holds | **yes** | issue + check both two-block |
| Single revision published | **yes** | rev 8 publish `completed` |
| GitHub ≡ DB `summary_json` | **yes** | `gen=2`, `pr=8`, `head_sha=d84b83b` |
| Unused marker flagged | **no** | probe marker not in block 1 |

## Pass criteria (push 3 — rev 6)

| Check | Pass | Evidence |
|-------|------|----------|
| G9 addressed prose after fix | **no** | `Since last push: n/a`; `resolution.addressed: 0` |
| Block 2 shrink vs push 2 | **no** | `pr_active_count` 4 → 7 |
| Two-block shape + trace fields | **yes** | `generation_active_count=3`, `pr_active_count=7` |

**Operator sign-off (PSA #62 formatter):** Two-block surface + PR-wide verdict + trace fields **PASS** on post-deploy worker (pushes 1–4). G9/collapse deferred to finding-resolution dogfood.

**Merge gate (#63):** **cleared** after cleanup commit — merge when rev publishes.
