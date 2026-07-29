# Review engineering context P8 — Staging validation closeout (execution)

Phase **P8** of [REVIEW_ENGINEERING_CONTEXT_GENERAL_PLAN.md](../REVIEW_ENGINEERING_CONTEXT_GENERAL_PLAN.md). Baseline: [REVIEW_ENGINEERING_CONTEXT_FINDINGS.md](../REVIEW_ENGINEERING_CONTEXT_FINDINGS.md) § Wave 2 staging snapshot, RCX-G13–G15. **P8 only — program human gate.**

**Goal:** Prove RCX on staging; fill validation memos; operator sign-off; sync program docs; sibling judge re-validation.

**Prerequisite:** P6+P7 merged to `main` and deployed to staging (`revy-worker` image = merge SHA).

## Decisions locked for P8

- **`--since`** = ISO timestamp of P6+P7 deploy on staging (not full history).
- **Sign-off requires:**
  - `context_stats` populated on dogfood run(s) — API + script (`runs_with_context_stats` ≥ 1)
  - `engineering_context_injected` true on same run(s) — **context_stats column** (primary)
  - `engineering_context_bytes` > 0 on same run(s)
  - `runs_with_omitted_md` = 0 on post-deploy window
  - `diff_truncated_pct` < 5% when **≥ 3** completed runs in window; **INCONCLUSIVE OK** when only 1–2 runs (RCX-D15 single PR) — document run IDs
  - revybot issue comment matches P6 sections (see P8.5 — fallback vs Moonshot path)
  - **Contradict locks %** = 0% on dogfood findings (manual)
- **Judge sibling:** Refresh stale RCX rows in judge validation memo before fill; post-deploy `--since` outcome persistence.
- **No production tag** in P8 — staging sign-off only.
- **P5.4 doc sync** moves here (README shas, recovery Track M, PRODUCT_PATTERNS).

## Out of scope for P8

- RC4 `workspace_review_policy` DB
- Frontend trace UI
- Program tag / changelog.json

---

## P8.1 — Deploy verify (operator)

**What:** After `main` push deploy succeeds, confirm on droplet:

```bash
docker inspect revy-worker --format '{{.Config.Image}}'
docker ps --filter name=revy --format 'table {{.Names}}\t{{.Status}}'
```

Record merge SHA in RCX validation memo § Deploy.

**Deliverable:** Deploy table rows marked done in [REVIEW_ENGINEERING_CONTEXT_STAGING_VALIDATION.md](../REVIEW_ENGINEERING_CONTEXT_STAGING_VALIDATION.md).

---

## P8.2 — Dogfood review run (operator)

**What:** **Primary:** post-merge autostart on P6+P7 PR after `main` deploy. Comment `@revy review` if autostart did not fire.

1. Confirm workspace `review_autostart_enabled` or `@revy review` on PR head.
2. Wait for `revy/review` check **completed** on latest `head_sha`.
3. Note `review_run_id` from Revy UI or API.

**Deliverable (human gate):** ≥1 completed run in `--since` window with non-null `context_stats`.

---

## P8.3 — Metrics + RCX gate (operator)

**What:** Run staging script; **refresh stale RCX rows** in [JUDGE_JSON_CONTRACT_STAGING_VALIDATION.md](../../judge-json-contract/JUDGE_JSON_CONTRACT_STAGING_VALIDATION.md) § Review context (still says key absent / pending RCX P2) before pasting new numbers.

```bash
cd backend
DEPLOY_ISO="<P6+P7-deploy-iso>"
DATABASE_SSL_INSECURE=1 pipenv run sh -c \
  "python -m scripts.judge_json_contract_staging_metrics --since ${DEPLOY_ISO} --rcx-gate --json" \
  | tee /tmp/rcx-staging-metrics.json
```

**Fill:**

| Doc | Section |
|-----|---------|
| [REVIEW_ENGINEERING_CONTEXT_STAGING_VALIDATION.md](../REVIEW_ENGINEERING_CONTEXT_STAGING_VALIDATION.md) | Metrics post-deploy; `context_stats`; Publish surface |
| [JUDGE_JSON_CONTRACT_STAGING_VALIDATION.md](../../judge-json-contract/JUDGE_JSON_CONTRACT_STAGING_VALIDATION.md) | § Review context (refresh stale); § Post-deploy judge |

**Deliverable:** `--rcx-gate` all PASS or INCONCLUSIVE only on diff_truncated with 1–2 runs; no FAIL.

---

## P8.4 — API spot-check (operator)

**What:** `GET` review run for dogfood `review_run_id` — confirm `context_stats` matches P7.2 shape and `engineering_context_injected === true`.

**Deliverable:** One line in validation memo § `context_stats` with sample JSON snippet.

---

## P8.5 — Publish surface verify (operator)

**What:** On dogfood PR, compare revybot issue comment vs Greptile.

| Path | Verify |
|------|--------|
| **Moonshot enabled** (staging default) | LLM issue comment includes narrative, confidence + rationale, required `<details>` |
| **Moonshot disabled/failed** | Fallback (P6.2–P6.5) still passes same checklist — RCX-D14 |

| Check | Pass |
|-------|------|
| Narrative paragraph (not one-liner) | |
| Confidence + rationale sentence | |
| Security `<details>` if security finding | |
| Important files `<details>` table | |
| Findings table + metadata footer | |

**Deliverable:** Publish surface row in RCX validation memo; note which path (Moonshot vs fallback) was exercised.

---

## P8.6 — Contradict locks check (operator)

**What:** Review published active findings — any contradict locked ID from RCX extract (JC-D*, RCX-D*)?

**Target:** 0% contradict.

**Deliverable:** Sign-off table row in validation memo.

---

## P8.7 — Judge sibling re-validation (operator, non-blocking)

**What:** If dogfood PR triggered judge escalation, confirm engineering lock block + `lock_ids_cited`. Re-run metrics judge section `--since`.

If no escalation, note “judge RCX path not exercised” — optional follow-up PR.

**Deliverable:** Judge validation memo post-deploy row dated.

---

## P8.8 — Program doc sync

**What:** Update program status to **shipped** with commit shas (P6, P7, P8 sign-off date).

| Doc | Change |
|-----|--------|
| [README.md](../README.md) | P6–P8 Done + shas; status shipped |
| [waves/REVIEW_ENGINEERING_CONTEXT_EXECUTION.md](./REVIEW_ENGINEERING_CONTEXT_EXECUTION.md) | Status column |
| [REVIEW_ENGINEERING_CONTEXT_FINDINGS.md](../REVIEW_ENGINEERING_CONTEXT_FINDINGS.md) | Program status shipped |
| [REVIEW_ENGINEERING_CONTEXT_GENERAL_PLAN.md](../REVIEW_ENGINEERING_CONTEXT_GENERAL_PLAN.md) | Status done |
| [../../REVIEW_PIPELINE_RECOVERY_CHECKLIST.md](../../REVIEW_PIPELINE_RECOVERY_CHECKLIST.md) | Track M — RCX shipped + sign-off date |
| [../../REVIEW_PIPELINE_PRODUCT_PATTERNS.md](../../REVIEW_PIPELINE_PRODUCT_PATTERNS.md) | Planning-doc inject → shipped dogfood |

**Deliverable:**

```bash
grep "shipped" docs/review-pipeline/review-engineering-context/README.md
grep -A2 "Track M" docs/review-pipeline/REVIEW_PIPELINE_RECOVERY_CHECKLIST.md
```

---

## P8.9 — Operator sign-off

**What:** Complete sign-off table in [REVIEW_ENGINEERING_CONTEXT_STAGING_VALIDATION.md](../REVIEW_ENGINEERING_CONTEXT_STAGING_VALIDATION.md).

**Deliverable:** `_Operator sign-off: <date>_` line filled.

---

**Phase gate** (regression — uses **existing** test files; `test_engineering_context_pack.py` does **not** exist):

```bash
cd backend && pipenv run pytest \
  tests/unit/test_engineering_context_manifest.py \
  tests/unit/test_engineering_context_dedupe.py \
  tests/unit/test_engineering_context_extract.py \
  tests/unit/test_github_publish_formatter.py \
  tests/unit/test_github_review.py \
  tests/unit/test_judge_json_contract_staging_metrics.py \
  -q
```

**Human gate:** P8.2 + P8.3 + P8.5 + P8.6 + P8.9 complete.

**Next:** none — RCX program complete. Parking lot: RC4, RCX-G7, BUGBOT generator, metrics script rename.
