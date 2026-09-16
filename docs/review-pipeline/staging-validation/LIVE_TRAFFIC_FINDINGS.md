# Live traffic — findings (2-week window)

**Date:** 2026-08-21  
**Purpose:** Baseline for what actually happened after Revy ran on the staging droplet for ~1–2 weeks. **No execution steps.**  
**Evidence:** `revy-staging` via `PRODUCTION_DATABASE_URL` (queried 2026-08-21T18:43Z); alembic `2026_08_10_1300_0032_github_pipeline_runs_models_snapshot`; metrics scripts + ad-hoc SQL; code on `main`.  
**Companion memo:** [POST_MAIN production window](./POST_MAIN_STAGING_VALIDATION.md) (gate tables). This doc is the **why**.

**Environment fact (verified):** this DigitalOcean cluster has `revy-dev`, `revy-test`, `revy-staging`, `revy-sec-*`. There is **no** `revy` production database. Live review traffic **is** `revy-staging` — one tenant (`Raimonds Krauklis`), GitHub App `raimondskrauklis`, repos `revy` + `kp-platform` (+ `tender_pro` indexed, almost no recent reviews).

---

## Build principles

1. **Dogfood PASS ≠ fleet health** — 2-run RCX / MRC gates on chore PRs do not describe `kp-platform` PRs with 50–159 changed files.
2. **Name the failure, not the checkpoint** — `failure_stage=retrieve` on completed runs is a leftover checkpoint, not a retrieve bug.
3. **No silent embedding swap** — already locked in [VOYAGE_CODE_4_FINDINGS.md](../../models/voyage-embeddings/VOYAGE_CODE_4_FINDINGS.md); staging violated it.
4. **RG-6 withhold stays** — judge misses must be fixed upstream (JC-D1). Do not publish escalation without an outcome row.
5. **Real data only** — numbers below are SQL/script output, not estimates.

---

## Terminology

| Term | Meaning |
|------|---------|
| **Live window** | `--since 2026-08-07T00:00:00Z` through query time (411 review runs) |
| **Post-#99 window** | `--since 2026-08-11T07:40:23Z` — fair MRC (after snapshot writer + trace API) |
| **Checkpoint leftover** | `commit_review_run_observability_checkpoint` sets `failure_stage='retrieve'` then commits; success path never clears it |
| **Thinking-first message** | Anthropic/RTU `content[0].type = thinking` before any `text` block |
| **Open attempt** | `github_llm_call_attempts` row with `completed_at` null (started, never completed/failed) |

---

## Fleet snapshot (verified)

| Metric | All-time | Live window (from 7 Aug) |
|--------|----------|--------------------------|
| Review runs | 760 (27 Jul → 20 Aug) | 411 (351 completed / 37 failed / 22 superseded / 1 processing / 5 pending leftovers) |
| Findings / groups | 1759 / 1756 | 893 findings |
| Publish jobs | 659 (619 completed) | 336 completed |
| Code chunks | 252,534 | — |
| Week of 17 Aug | 18 runs | quiet vs 200–280 in prior weeks |

By repo in the live window: `kp-platform` 252 runs, `revy` 159. Review model: `moonshot` / `kimi-k2.7-code`.

---

## What exists vs genuinely new

### Shipped and working (verified)

| Asset | Evidence |
|-------|----------|
| Index → review → publish loop | 351 completed runs; 619 completed publish jobs |
| Finding-resolution Pass 1–2 in the wild | 566 groups `resolved`; publish `resolution.addressed` sum **265** across 170 jobs |
| MRC P0 after #99 | embed manifest + step model **147/147**; `models_snapshot` 155/159 |
| PO P0 schema | `github_llm_call_attempts` present; 606 rows in window |
| RG-15 supersede | 22 superseded review runs + 2 superseded index jobs |
| RCX inject | `engineering_context_injected` **124/351**; bytes p50 **19,014** |

### Genuinely broken or drifted (this baseline)

These are **not** in the July dogfood memos as fleet facts.

| ID | Finding | Confidence |
|----|---------|------------|
| **LT-1** | Judge extracts only `content[0]`; RTU returns thinking-first → `Anthropic response invalid` | **verified** (53/53 fail candidates) |
| **LT-2** | Review LLM success never closes the attempt row; `wait_ms` only on timeouts | **verified** (215/233 open) |
| **LT-3** | No reaper for `processing` after checkpoint; one #98 run stuck 10 days | **verified** |
| **LT-4** | `voyage-code-4` went live 16 Aug without re-index; mixed vectors in one column | **verified** (counts) / **assumption** (spaces incompatible) |
| **LT-5** | RCX 512 KB cap + drop-largest-first hits **only** `kp-platform`; 100% of truncations | **verified** |
| **LT-6** | Moonshot JSON unterminated / truncated on large prompts | **verified** (28+9 failed runs) |
| **LT-7** | `failure_stage=retrieve` left on successful runs — gate/SQL readers misread it | **verified** |

---

## Catalog — tracks

### LT-1 — Judge thinking-first responses (highest leverage)

**Symptom:** live-window outcome persistence **62.4%** (88/141 candidates). Target ≥95%. 53 parse errors, all `Anthropic response invalid`, retry_count **0**. Latest miss: review_run `01a020aa-…` on `revy` #102 (2026-08-20).

**Shape (verified, 53 fails):**

| Flag | n |
|-----|---|
| `"type": "thinking"` in `raw_response_text` | **53 / 53** |
| also has `"type": "text"` later | 45 |
| thinking only (no text block) | 8 |
| empty `content: []` | 0 |

Stored preview (truncated): `content: [{"type": "thinking", "thinking": "", "signature": "…"}]`. Model id in body: `claude-sonnet-5` (RTU gateway).

**Code (verified):**

- `_extract_message_text` uses **only** `content[0]` and requires `text` non-empty — `anthropic_review.py` ~208–230.
- That raises `ServiceUnavailableError("Anthropic response invalid")`, **not** `JudgeParseError`.
- `call_judge_with_optional_retry` retries only `JudgeParseError` / `judge_outcome_invalid` — `github_finding_judge.py` ~92–109. So these never retry.
- Profile fallback *would* catch `ServiceUnavailableError` if a second (direct) profile exists — `_post_judge_with_profile_fallback` ~513–524. Staging judge steps that ran used `anthropic` / `claude-sonnet-5`; whether direct Anthropic is configured on the droplet is **unknown** (not in local `.env` as a second profile).

**Contradiction with July findings:** [JUDGE_JSON_CONTRACT_FINDINGS.md](../judge-json-contract/JUDGE_JSON_CONTRACT_FINDINGS.md) blamed prompt-only JSON + missing structured output. That may still matter for the 8 thinking-only bodies, but **45/53 already contain a text block** the parser never reads. Persistence moved 21% → 62% and then stalled on this adapter bug.

**Do not:** relax RG-6; spray extra retries on `ServiceUnavailableError` without extracting text first.

**Program:** [judge-thinking-blocks](../judge-thinking-blocks/README.md) — **closed**. P0–P2 on [#103](https://github.com/raimondskrauklis/revy/pull/103); S0–S4: [JUDGE_THINKING_BLOCKS_STAGING_VALIDATION.md](../judge-thinking-blocks/JUDGE_THINKING_BLOCKS_STAGING_VALIDATION.md).

---

### LT-2 — Review attempt rows never complete on success

**Symptom:** PO P4 `--po-gate` **script-PASSes** because `review_wait_ms_p95=840152`. That p95 is **17 timeout rows at ~840s** (Celery/HTTP budget is 900s standard). Success-path `wait_ms` = **0**.

| Review attempts (from 7 Aug) | n |
|------------------------------|---|
| Total | 233 |
| `completed_at` set | 18 (all failed: 17 timeout + 1 rate_limit) |
| Open (`completed_at` null, `wait_ms` null) | **215** |
| Success with `wait_ms` | **0** |

Embed/publish attempts **do** complete (204/204 embed, 169/169 publish, wait populated).

**Code (verified):**

- `github_review._call_llm` `start_attempt(recorder)` then `llm_dispatch.call_review_llm` — `github_review.py` ~991–1002, ~1178–1195.
- On success it **never** calls `complete_attempt`. It only `fail_attempt` on `TimeoutException` / `HTTPError` (~1003–1031).
- Dispatch does **not** pass `recorder` into Moonshot — `llm_dispatch.py` ~29–36.
- `moonshot_review.complete_review` has no `recorder` argument (~328–344), so the inner `try_complete_attempt` path never runs for review.

**Effect:** SLO dashboards and `--po-gate` are lying. Timeout p95 looks like “reviews take 14 minutes”; real success latency is unmeasured.

---

### LT-3 — Stuck `processing` after retrieve checkpoint

**Row:** review_run `019fef5a-47ae-7f63-a78b-db8cd89afc2d` · `revy` #98 · sha `c630845` · created 2026-08-11T05:45:06Z · **updated 3s later, never again**.

**Not a hung retrieve.** Checkpoint already wrote:

- `context_stats.prompt_chars=107214`, `engineering_context_injected=true`, `diff_truncated=false`
- `timing_stats.retrieve_ms=3085`
- `failure_stage=retrieve` (checkpoint label — `review_run_observability.py` ~37–43)
- index job **completed** (`voyage-code-3.5`); pipeline steps: index only — **no review step**

Worker died (or task dropped) **after** `commit_review_run_observability_checkpoint` and **before** Moonshot. Resume exists (`processing` + `context_stats` → `resuming_after_checkpoint`, `github_review.py` ~1052–1106) but **no retry/reaper ran for 10 days**.

Five `pending` runs from 27–30 Jul (PRs #49/#52/#55/#57/#71) are older leftovers, never started.

**Observability lie:** completed runs also keep `failure_stage=retrieve` (latest `revy` #102 and `kp-platform` #518). Do not GROUP BY `failure_stage` for failure analysis without `status='failed'`.

System-wide `--rg15-gate` **FAIL** is this one orphan. Dogfood `--pr-number` gates would not see it.

---

### LT-4 — `voyage-code-4` live, mixed index

[VOYAGE_CODE_4_FINDINGS.md](../../models/voyage-embeddings/VOYAGE_CODE_4_FINDINGS.md) (10 Aug): API 503, “still unavailable”, lean wait / optional 3.5. Staging then:

| Date | Embed model on index manifest |
|------|-------------------------------|
| 10–15 Aug | `voyage-code-3.5` (successful jobs) |
| **16 Aug onward** | **`voyage-code-4`** (31 completed index jobs with model; 34 `index_embed` attempts) |

Chunks: **244,645** before 16 Aug vs **7,889** since. `github_code_chunks` has **no** `embedding_model` column — retrieval mixes old and new vectors.

**Code gap (verified):** `_FLEXIBLE_DIMENSION_MODEL_PREFIXES` includes `voyage-code-3` (matches 3.5) and `voyage-4*` (does **not** match `voyage-code-4`) — `voyage_embeddings.py` ~35–40. `voyage-code-4` is **not** sent `output_dimension`. Inserts still succeeded at `vector(1024)` → native dim is 1024 **or** Voyage defaulted to 1024. **Unknown** whether 3.5 and 4 share a space; the 10 Aug findings assumed they do **not**.

Violates that doc’s “no silent model swap / full re-index” principle. Repo default is still `voyage-code-3` (`config.py`); droplet env was changed under the docs.

---

### LT-5 — RCX truncation is a `kp-platform` cap problem

`--rcx-gate` **FAIL:** diff truncated **15.4%** (54/351), omitted `.md` on 54 runs. Split:

| Repo | Completed retrieve manifests | Truncated | omitted `.md` | changed_files p50 / p95 |
|------|------------------------------|-----------|---------------|-------------------------|
| `kp-platform` | 223 | **54 (24%)** | 54 | 50 / 159 |
| `revy` | 128 | **0** | 0 | 19 / 45 |

July RCX dogfood PASS (2 runs, 0% truncate) was `revy`-sized. Cap is `revy_diff_max_bytes=524288` (`config.py` ~185). `build_unified_diff` **drops largest patches first** (`github_review.py` ~230–236) — sample omitted lists mix huge `.md` findings docs **and** `etl_service.py` / `orchestrator.py`. The files most likely to contain bugs are the first dropped.

Prompt artifacts (truncated at 512 KB in trace): `kp-platform` p50 **268,164** / p95 **522,550** / max **522,699**; `revy` p50 115,365 / p95 195,621.

---

### LT-6 — Moonshot JSON die on big prompts

Failed runs in live window:

| n | `failure_class` | `failure_stage` | Sample `error_message` |
|---|-----------------|-----------------|------------------------|
| 28 | null | null | `Unterminated string starting at: line 1 column 657` |
| 9 | null | retrieve | `Moonshot review response truncated` |

28 JSON parse fails happen **after** HTTP success (not classified). 9 truncated responses sit on the checkpoint leftover stage. Together with LT-5 prompt sizes, this is the large-PR reliability track — distinct from judge LT-1.

---

### LT-7 — Finding resolution is live (with messy labels)

Not a dogfood-protocol PASS. Inventory:

| Pattern | n |
|---------|---|
| `resolved` | 566 |
| `judge_dismissed` + method `absent_and_addressed` | 395 |
| `addressed` + `absent_and_addressed` | 65 |
| `judge_dismissed` + method `judge_dismissed` | 43 |
| `addressed` but still `active` | 7 |
| `resolved` with null `resolution_status` | 63 |

Pass 3 / verification-dismissed volume is small vs fingerprint-absent closure. Dedicated [finding-resolution dogfood](../finding-resolution-dogfood/FINDING_RESOLUTION_DOGFOOD_STAGING_VALIDATION.md) protocol is still open.

---

## MRC / PO gates — how to read them on the fleet

| Gate | Dogfood (PR-scoped) | Fleet (this window) | Read as |
|------|---------------------|---------------------|---------|
| MRC P0 | PASS on #100 | **PASS** post-#99 | Real |
| MRC P1 judge step model | PARTIAL (skipped judge) | 61/141 with model; 290 judge steps null | **Mostly skipped / not_applicable**, not a new bug. 61 steps that ran used `anthropic`/`claude-sonnet-5` |
| MRC P1 publish model | 1/1 | 138/141 | Almost OK |
| PO P0 | PASS | PASS | Real |
| PO P4 wait p95 | INCONCLUSIVE then | Script PASS | **False PASS** — see LT-2 |
| RG-15 stuck | PASS on #93 | FAIL | One orphan — LT-3 |
| RCX truncate / omitted md | PASS (2 `revy` runs) | FAIL | LT-5, `kp-platform` only |
| Judge persistence | pending | 62.4% FAIL | LT-1 |

---

## Advice / options (directional, not execution)

**Lean next:** treat **LT-1** as the judge wave (extract text from non-leading `text` blocks; map empty-thinking to a parse error that can retry). Do **not** start with more RTU retries.

**Then LT-2** — one attempt recorder through dispatch; complete on success. Until then ignore `--po-gate` wait p95.

**LT-4** needs an operator decision before more indexing: stay on `voyage-code-4` and re-index, or revert to 3.5, or prove shared space. Mixing is already happening.

**LT-5** is a cap/policy issue for large foreign repos, not an RCX inject bug (inject 124/351 still works). Drop-largest-first is the wrong omit heuristic if the largest files are the ones under review.

**Defer:** finding-resolution label cleanup (LT-7) until the dogfood PR protocol runs; MRC judge-step-model gate on fleet-wide `--since` (too many skipped steps).

---

## Data scope & exclusions

**In:** `revy-staging` public schema; live window from 7 Aug; post-#99 MRC subset.  
**Out:** `revy-sec-staging` (not queried); true separate production DB (does not exist here); GitHub check UX / worker logs (not pulled this pass); Voyage billing dashboard; droplet `.env` contents.

---

## Edge cases

| Case | Notes |
|------|--------|
| Thinking-only (8/53) | Extracting later `text` blocks does not help — empty assistant text |
| Checkpoint + worker SIGKILL | Resume path is dead without Celery retry or a reaper |
| `voyage-code-4` 1024 inserts | Does not prove shared space with 3.5 |
| Quiet week of 17 Aug | Low n — do not read as quality improvement |
| `tender_pro` | 32 PRs in DB, ~0 recent review runs |

---

## Decisions registry

| ID | Question | Status | Resolution |
|----|----------|--------|------------|
| LT-Q1 | Is `revy-staging` the production database of record? | **resolved** | Yes, on this cluster — no `revy` prod DB |
| LT-Q2 | Is judge 62% a JSON-contract miss or an adapter miss? | **resolved** | Adapter: thinking-first `content[0]` (LT-1). JSON contract still relevant for 8 thinking-only |
| LT-Q3 | Is PO P4 wait p95 a real SLO? | **resolved** | No — timeout-only sample (LT-2) |
| LT-Q4 | Keep `voyage-code-4` on staging? | **open** | Live since 16 Aug; mixed vectors already stored |
| LT-Q5 | Re-index after LT-Q4? | **open** | Required if spaces differ (Voyage findings principle) |
| LT-Q6 | RCX cap / omit heuristic for `kp-platform`-class diffs? | **open** | 24% truncated; largest files dropped first |
| LT-Q7 | Reaper for stale `processing`? | **open** | One 10-day orphan; resume exists but unused |
| LT-Q8 | Clear `failure_stage` on success? | **open** | Currently pollutes every completed run |

---

## Parking lot

- Direct Anthropic fallback configured on droplet? (would have caught some LT-1 if profile 2 exists)
- Worker logs for #98 `019fef5a` (OOM vs deploy bounce vs Celery drop)
- Whether `voyage-code-4` Matryoshka `output_dimension=1024` is valid (prefix not in allow-list)
- `revy-sec-staging` contents
- Pass 3 verification-judge volume vs discovery judge

**Phase-0 prerequisites** (if a program is opened): LT-1 parser; LT-2 attempt complete; LT-Q4 embedding decision. Watchdog (LT-7/Q7) is ops-small but unblocks RG-15 fleet gates.

---

## Devil's advocate

- This is still **one operator’s GitHub user** and two private repos. `kp-platform` size dominates RCX/Moonshot numbers; a third-party tenant might look like `revy` (no truncation).
- Thinking-first may be RTU wrapping `claude-sonnet-5`, not Anthropic-direct. Fixing `_extract_message_text` is still correct (spec allows multiple content blocks).
- 62% persistence is **better** than July’s 21% — shipping structured output + snippets helped; the remaining miss is concentrated and fixable.
- `voyage-code-4` 1024 writes might mean Voyage aliases code-4 onto a 1024 Matryoshka slice compatible with 3.5. **Do not assume that** without a retrieval smoke on mixed vs rebuilt indexes.

---

## Experiment / verification (when work starts)

| Check | Pass | Fail |
|-------|------|------|
| Judge fail candidates with thinking-first | `content[0].type=thinking` but a later `text` block still yields `outcome` ≥95% | still `Anthropic response invalid` |
| Retry | `retry_count≥1` only after real JSON parse miss, not after thinking skip | retry storms on HTTP |
| Review attempts | success rows have `completed_at` + `wait_ms`; open≈0 | 215-style orphans remain |
| PO `--po-gate` | p95 from success `wait_ms`, not 840s timeouts | script PASS on timeouts only |
| Embeddings | one model id in index manifests after a chosen cutover; retrieval smoke vs held-out files | 3.5 and 4 chunks in one query |
| RG-15 system-wide | 0 `processing` older than N minutes | #98-class orphans |
| RCX | report **per repo**; `revy` 0% truncate must not mask `kp-platform` | fleet average only |

---

## References

- Snapshot tables: [POST_MAIN_STAGING_VALIDATION.md](./POST_MAIN_STAGING_VALIDATION.md) § Production window  
- Judge July baseline: [JUDGE_JSON_CONTRACT_FINDINGS.md](../judge-json-contract/JUDGE_JSON_CONTRACT_FINDINGS.md) · [JUDGE_TRANSPORT_RELIABILITY_FINDINGS.md](../judge/JUDGE_TRANSPORT_RELIABILITY_FINDINGS.md)  
- Voyage: [VOYAGE_CODE_4_FINDINGS.md](../../models/voyage-embeddings/VOYAGE_CODE_4_FINDINGS.md)  
- Code: `backend/app/integrations/anthropic_review.py` (`_extract_message_text`), `backend/app/services/github_finding_judge.py` (`call_judge_with_optional_retry`), `backend/app/services/github_review.py` (`_call_llm`, `build_unified_diff`), `backend/app/integrations/llm_dispatch.py`, `backend/app/services/review_run_observability.py`, `backend/app/integrations/voyage_embeddings.py`  
- Scripts: `judge_json_contract_staging_metrics.py`, `pipeline_observability_staging_metrics.py`, `generation_lifecycle_staging_metrics.py`, `model_run_capture_staging_metrics.py`
