# docs/review-pipeline/judge-thinking-blocks/waves/JUDGE_THINKING_BLOCKS_P3_EXECUTION.md

# P3 — Staging validation & doc sync (execution)

Phase **P3** of [`JUDGE_THINKING_BLOCKS_GENERAL_PLAN.md`](../JUDGE_THINKING_BLOCKS_GENERAL_PLAN.md). Baseline: [`JUDGE_THINKING_BLOCKS_FINDINGS.md`](../JUDGE_THINKING_BLOCKS_FINDINGS.md) JTB-D7, JTB-D9, JTB-Q5. **P3 only — final phase.**

**Goal:** Human gate — live `--since` candidate → `outcome` ≥95% **or** residual classified (thinking-only / invalid JSON / other). Extract-only ceiling on the 2026-08-07 window is **94.3%** (D9). Do not reopen JSON-contract or add retries to chase 0.7 points (D7).

## Decisions locked for P3

- Validation memo: `docs/review-pipeline/judge-thinking-blocks/JUDGE_THINKING_BLOCKS_STAGING_VALIDATION.md` (from [TEMPLATE_STAGING_VALIDATION.md](../../staging-validation/TEMPLATE_STAGING_VALIDATION.md)).
- Re-run `backend/scripts/judge_json_contract_staging_metrics.py` **and** add split evidence (text-later vs thinking-only). Today’s printer does not split — extend the script or add dated SQL in the memo; do not average the 45 vs 8 away.
- P3 **passes** at ≥95% **or** when residual is classified and JSON-contract is not reopened (D9). Treating 94.3% as hard fail is out of scope.
- Fill JTB-Q5 from staging (thinking-only recover rate after one retry). Do not add retries or a second model from this phase.
- `frontend/src/data/changelog.json` — skip (backend-only; no user-facing UI).
- **Before doc-sync:** optional `post-finish-gap-pass` on this plan folder.

## Out of scope for P3

- JSON-contract prompt/schema work, extra retries, second model (D7)
- LT-2–LT-6 (attempts `wait_ms`, stuck processing, Voyage mix, RCX cap, Moonshot JSON)
- Bedrock extract; new DB columns; droplet credential ops

---

## P3.1 — Post-finish gap pass (optional, before memo close)

**What:** Re-read findings + general plan vs shipped P0–P2 code; fix small gaps in-tree if any. Do not open JSON-contract work.

**Files:** plan folder + `backend/app/integrations/anthropic_review.py` (reference)

**Deliverable (non-gate):** Gap list empty or small fixes committed on this branch.

---

## P3.2 — Split evidence: text-later vs thinking-only

**What:** Extend `judge_json_contract_staging_metrics.py` **or** document a one-shot SQL in the memo that classifies remaining `parse_error` rows: thinking-first + later `text` vs thinking-only vs invalid JSON (`judge_json_invalid`) vs other. Use truncated `raw_response_text` already on the manifest.

**Files:** `backend/scripts/judge_json_contract_staging_metrics.py`, `docs/review-pipeline/judge-thinking-blocks/JUDGE_THINKING_BLOCKS_STAGING_VALIDATION.md`

**Deliverable:** Printer or memo SQL shows the 45 vs 8 split (or post-deploy equivalent), not a single blended %.

```bash
cd backend && pipenv run python -m py_compile scripts/judge_json_contract_staging_metrics.py
```

---

## P3.3 — Staging metrics + validation memo

**What:** After P0–P2 are on the staging worker, run:

```bash
cd backend
DATABASE_SSL_INSECURE=1 pipenv run python -m scripts.judge_json_contract_staging_metrics --since 2026-08-07T00:00:00Z
```

Fill `JUDGE_THINKING_BLOCKS_STAGING_VALIDATION.md`: persistence %, `parse_error` breakdown (`judge_empty_text` / `judge_json_invalid` / HTTP), retry_count, split evidence, D9 94.3% ceiling note, JTB-Q5 rate. Pass = ≥95% **or** classified residual.

**Files:** `docs/review-pipeline/judge-thinking-blocks/JUDGE_THINKING_BLOCKS_STAGING_VALIDATION.md`

**Deliverable (non-gate):** Dated results table in the memo. LOOP does not treat an empty memo as a test failure.

---

## P3.4 — Doc sync

**What:** Close program docs; point staging index at the memo; mark JTB-Q5 resolved in findings.

| Doc | Change |
|-----|--------|
| [waves/JUDGE_THINKING_BLOCKS_EXECUTION.md](./JUDGE_THINKING_BLOCKS_EXECUTION.md) | Status Done + commit sha per phase row |
| [README.md](../README.md) | Program status shipped / human-gate result; link validation memo |
| [JUDGE_THINKING_BLOCKS_FINDINGS.md](../JUDGE_THINKING_BLOCKS_FINDINGS.md) | JTB-Q5 filled; experiment table post-deploy |
| [JUDGE_THINKING_BLOCKS_GENERAL_PLAN.md](../JUDGE_THINKING_BLOCKS_GENERAL_PLAN.md) | Next step → shipped |
| [../staging-validation/README.md](../../staging-validation/README.md) | Thinking-blocks row → memo link |
| [../staging-validation/LIVE_TRAFFIC_FINDINGS.md](../../staging-validation/LIVE_TRAFFIC_FINDINGS.md) | LT-1 pointer to this program result |
| [../README.md](../../README.md) | Folder layout status if it still says plan-only |
| [../judge/README.md](../../judge/README.md) | Thinking-blocks row status |

**Files:** docs listed above

**Deliverable:** Grep of program README execution table shows Done (or human-gate pending with memo filled). No `frontend/src/data/changelog.json` edit.

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_anthropic_review.py tests/unit/test_github_finding_judge.py -q
```

**Human gate:** Staging validation memo signed — ≥95% outcome persistence **or** residual classified (thinking-only / `judge_json_invalid` / other) with D9 ceiling noted. LOOP **stops** here even if tests pass. Do not reopen JSON-contract to chase 0.7pt.

**Deploy:** Requires P0–P2 on the staging worker before filling the memo.

**Next:** none — program complete after human sign-off.
