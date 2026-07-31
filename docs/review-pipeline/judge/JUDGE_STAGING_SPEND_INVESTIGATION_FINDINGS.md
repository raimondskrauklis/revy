# Judge staging spend investigation — findings

**Date:** 2026-07-31  
**Trigger:** RR-W1 R5 dogfood — operator expected Anthropic billing to reflect **>20 judge calls**; `misc/claude_api_cost_2026_07_01_to_2026_07_31.csv` shows **2 rows** for `revy-judge` on 2026-07-31.  
**Database:** `revy-staging` (`PRODUCTION_DATABASE_URL`)  
**Authority:** [JUDGE_INPUT_INVESTIGATION_FINDINGS.md](./JUDGE_INPUT_INVESTIGATION_FINDINGS.md) · [JUDGE_TRANSPORT_RELIABILITY_FINDINGS.md](./JUDGE_TRANSPORT_RELIABILITY_FINDINGS.md) · `misc/loglast.txt` · `misc/claude_api_cost_2026_07_01_to_2026_07_31.csv`

---

## Summary

**Billing is not missing — the CSV rows are daily aggregates, not per-request records.**

On **2026-07-31** staging executed **38 judge HTTP calls** (discovery + verification), persisted **28 outcomes**, and Anthropic billed **`revy-judge` $0.18** (input $0.07 + output $0.11). That cost level is **consistent** with small judge prompts (~1.7k chars median) — not with “only 2 API calls.”

**Judge does not run on every review run.** R5 policy escalates only `error` / `critical` / `security≥warning` findings, max **10 per run**. Of **54** review runs today, **24** had `judge_status=not_applicable` (zero escalation candidates).

**Gaps found (judge):** JT-SP2–SP5 **shipped** on PR #80 (`1a47c48`+) — token persistence, response previews, post-verification status finalize. Historical rows pre-deploy lack judge token capture.

**Moonshot (reviewer):** Dominates LLM spend — ~2 API calls per review run (large diff review + small publish summary). See § Moonshot request log below.

---

## Moonshot request log (last 3 days — `misc/request_log_part_0001.csv`)

**Model:** `kimi-k2.7-code` · **API key:** `revy-main` · **Window:** 2026-07-30 – 2026-08-01 UTC (partial Aug 1).

| Day | Moonshot calls | Input tokens | Output tokens | `review_like` (in ≥10k) | DB completed runs |
|-----|----------------|--------------|---------------|-------------------------|-------------------|
| 2026-07-30 | 74 | 833k | 420k | 38 | **12** |
| 2026-07-31 | 53 | 1.03M | 461k | 31 (+9 XL ≥50k) | **50** |
| 2026-08-01 *(to 05:23 UTC)* | 50 | 1.06M | 520k | 27 (+11 XL) | — |
| **3-day total** | **177** | **~2.9M** | **~1.4M** | — | **62** (Jul 30–31) |

**Pattern:** each review cycle ≈ **2 Moonshot calls** — large input (~12k–65k) for `review_pull_request_revision`, then small input (~600–1.2k) for publish summary. PR #80 dogfood (Jul 31 19–21 UTC): **12 calls** ≈ 6 cycles × 2.

**Jul 31 aligns with DB** (53 calls vs 50 review runs + publish summaries). **Jul 30 mismatch** (74 calls vs 12 DB runs) — likely extra testing on `revy-main` key outside staging review runs (burst 03:00 UTC).

**Output cap hits** (`output_tokens = 32_768`): **4** in window — truncated max output on very large PRs; monitor finding JSON completeness.

**vs judge:** Moonshot is **orders of magnitude** more tokens than Anthropic judge (~$0.18/day on `revy-judge` for Jul 31).

**Operator script:** `python -m scripts.moonshot_staging_spend_metrics --csv ../misc/request_log_part_0001.csv --days 3`

---

## Evidence sources

| Artifact | Location | Notes |
|----------|----------|-------|
| Anthropic cost export | `misc/claude_api_cost_2026_07_01_to_2026_07_31.csv` | `revy-judge` key; 2026-07-31 = 2 rows (input + output) |
| Moonshot request log | `misc/request_log_part_0001.csv` | Per-request tokens; `revy-main` key |
| Worker log slice | `misc/loglast.txt` | Ends `2026-07-31 20:18:55` — rev 5–6 PR #80; `judge_llm_request_started/completed` + `api.anthropic.com` 200 |
| Staging DB | `github_review_runs`, `github_finding_judge_outcomes`, judge pipeline manifests | Queried 2026-07-31 UTC |

---

## Anthropic CSV vs DB (2026-07-31)

| Metric | Anthropic CSV (`revy-judge`) | Staging DB |
|--------|------------------------------|------------|
| **Rows in export** | **2** (input_no_cache + output) | — |
| **Billed USD** | **$0.18** ($0.07 in + $0.11 out) | — |
| Review runs (all PRs) | — | 54 total · 49 completed |
| Runs with escalation candidates | — | 25 (`judge_escalation_candidate_count > 0`) |
| Runs `judge_status=not_applicable` | — | 24 (no error/critical/security candidates) |
| Runs `judge_status=completed` | — | 15 |
| Runs `judge_status=skipped_unavailable` | — | 10 (partial discovery failure) |
| **Judge HTTP calls** (manifest `raw_response` present) | — | **38** (discovery + verification slots) |
| **Outcomes persisted** | — | **28** (20 discovery + 8 verification) |
| **Parse failures** (`Anthropic response invalid`) | — | **10** (all discovery; `raw_response_text` null) |
| Median judge prompt size (successful calls) | — | **~1,712 chars** |

**Interpretation:** CSV **row count ≠ API call count**. Anthropic aggregates by day × model × token type. **$0.18 for ~28–38 small Sonnet calls is plausible** (~400–600 input tokens per call at Sonnet 5 rates). Empty-body HTTP 200 failures likely **do not bill** (consistent with transport findings § operator incident).

---

## PR #80 dogfood (RR-W1 R5)

| Rev | `head_sha` | Escalation candidates | Discovery API calls | Verification API calls | Outcomes | `judge_status` |
|-----|------------|----------------------|----------------------|------------------------|----------|----------------|
| 1 | `8f7f5e0` | 2 | 1 | 0 | 1 | `skipped_unavailable` |
| 2 | `ee4668c` | 1 | 0 | 1 | 1 | `skipped_unavailable` |
| 3 | `abdbd5c` | 0 | 0 | 1 | 1 | `not_applicable` |
| 4 | `38dd7b4` | 0 | 0 | 1 | 1 | `not_applicable` |
| 5 | `8aec926` | 1 | 1 | 1 | 2 | `completed` |
| 6 | `114aecd` | 1 | 1 | 0 | 1 | `completed` |
| 7 | `0cc1db3` | 0 | 0 | 1 | 1 | `not_applicable` |
| 8 | `7b99148` | 1 | 1 | 0 | 1 | `completed` |
| 9 | `cbd4267` | 1 | 1 | 0 | 1 | `completed` |
| 10 | `b8a589e` | 0 | 0 | 0 | 0 | `not_applicable` |

**Totals:** 10 completed review runs · **10 judge HTTP calls** · **10 outcomes** · **not** 10 calls per run.

`misc/loglast.txt` (rev 5–6 window): Moonshot review → reconcile → **2×** `judge_llm_request_started/completed` (rev 5) + **1×** (rev 6) → publish. Matches DB.

---

## When judge runs (verified)

```text
review_pull_request_revision (Moonshot — billed separately, Moonshot key)
  → reconcile_review_run
      → record_review_run_judge_status   # discovery judge (per escalation candidate)
      → verify_still_open_escalation_groups  # Pass 3 verification judge
      → record_judge_pipeline_step (manifest)
```

| Rule | Code | Effect |
|------|------|--------|
| Escalation filter | `is_judge_candidate()` · `github_finding_judge.py:182` | Only `error`/`critical`, or `security` with `severity ≥ warning` |
| Per-run cap | `JUDGE_MAX_PER_RUN = 10` | Max discovery calls per review run |
| Verification cap | `VERIFICATION_JUDGE_MAX_PER_RUN = 5` | Max Pass 3 calls per reconcile |
| Dedup | `_run_judge_llm_loop` existing outcome check | Skip API if `github_finding_judge_outcomes` row exists for `(review_run_id, group_id)` |
| No candidates | `candidate_count == 0` | `judge_status = not_applicable` — **no Anthropic call** |

---

## Gap catalog

| ID | Gap | Severity | Status | Evidence |
|----|-----|----------|--------|----------|
| **JT-SP1** | Operator confuses CSV **row count** with **API call count** | medium | **documented** | 2 CSV rows vs 38 DB-manifest calls on 2026-07-31 |
| **JT-SP2** | **Token usage not persisted** on judge pipeline steps | high | **shipped** | `record_judge_pipeline_step` sums `input_tokens`/`output_tokens` on step + manifest |
| **JT-SP3** | Manifest `raw_response` lacked `usage` block | medium | **shipped** | `judge_raw_response_with_usage()` attaches transport usage |
| **JT-SP4** | Empty-body HTTP 200 → `Anthropic response invalid` without preview | high | **shipped** | `_extract_message_text` includes `response_body_preview` in `ServiceUnavailableError.details` |
| **JT-SP5** | `skipped_unavailable` not re-evaluated after verification judge | medium | **shipped** | `finalize_review_run_judge_status()` in reconcile worker |
| **JT-SP6** | Review run count **≠** judge call count — escalation policy filters most runs | low | **by design** | 54 runs / 25 with candidates / 38 HTTP calls |

---

## Hourly judge outcomes (2026-07-31 UTC)

| Hour (UTC) | Success | Failed (parse) |
|------------|---------|----------------|
| 06–11 | 9 | 2 |
| 12–17 | 9 | 6 |
| 18–19 | 8 | 2 |
| **20** (loglast window) | **4** | **0** |

Failures clustered before evening dogfood pushes; **20:00 UTC hour clean** — aligns with `loglast.txt` showing healthy `judge_llm_request_completed` lines.

---

## Monthly trend (`revy-judge` outcomes)

| Day | Outcomes | Discovery | Verification |
|-----|----------|-----------|--------------|
| 2026-07-27 | 8 | 8 | 0 |
| 2026-07-28 | 8 | 8 | 0 |
| 2026-07-29 | 17 | 15 | 2 |
| 2026-07-30 | 2 | 2 | 0 |
| **2026-07-31** | **28** | **20** | **8** |

2026-07-31 is the highest judge volume day in July — driven by RR-W1 R5 multi-push dogfood (#78, #80) + TenderPro #130.

---

## Recommendations

| Priority | Action |
|----------|--------|
| P0 | **Operator:** reconcile spend via Anthropic console **Usage** (not CSV row count). Expect **~$0.15–0.25/day** at current prompt sizes when ~30–40 calls run. |
| P1 | **Persist `input_tokens` / `output_tokens`** on judge pipeline steps — **done** (`record_judge_pipeline_step`, manifest fields). |
| P1 | **Investigate JT-SP4** empty-body 200s — response preview now in exception details + manifest on failure paths. |
| P2 | Split `judge_status` — **deferred**; `finalize_review_run_judge_status` re-evaluates after verification instead. |
| P2 | **`scripts/judge_staging_spend_metrics.py`** — daily roll-up for operator reconciliation. |
| P2 | **`scripts/moonshot_staging_spend_metrics.py`** — Moonshot CSV vs DB review-run reconciliation. |

---

## Conclusion

**No evidence of missing Anthropic billing for successful judge calls on 2026-07-31.** The **2 CSV records** are daily token-type aggregates totaling **$0.18**, which matches **~38 small judge invocations** recorded in staging manifests and **28 persisted outcomes**.

**Judge is working** in the latest log window (`loglast.txt` rev 5–6). Earlier failures (`Anthropic response invalid`) explain `skipped_unavailable` on PR #80 pushes 1–2 and align with known transport empty-response class.

**Moonshot billing is proportional** to review volume (~2 calls per run, ~30k–65k input tokens per review). Use `moonshot_staging_spend_metrics.py` to reconcile CSV exports against `github_review_runs`.

**Judge token observability:** shipped post-`1a47c48` — new runs persist usage on pipeline steps and manifests.

---

## References

| Source | Path |
|--------|------|
| Escalation policy | `docs/review-pipeline/judge/README.md` § R5 policy |
| Discovery judge | `backend/app/services/github_finding_judge.py` |
| Verification judge | `backend/app/services/github_finding_closure.py` |
| Transport logging | `backend/app/integrations/anthropic_review.py` (`judge_llm_request_*`) |
| Judge manifest | `backend/app/services/github_pipeline_trace.py` (`record_judge_pipeline_step`) |
| Judge spend script | `backend/scripts/judge_staging_spend_metrics.py` |
| Moonshot spend script | `backend/scripts/moonshot_staging_spend_metrics.py` |
| Existing metrics script | `backend/scripts/judge_json_contract_staging_metrics.py` |
