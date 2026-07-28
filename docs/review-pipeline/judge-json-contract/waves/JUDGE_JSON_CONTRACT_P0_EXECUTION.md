# Judge JSON contract P0 — API smoke & structured-output feasibility (execution)

Phase **P0** of [JUDGE_JSON_CONTRACT_GENERAL_PLAN.md](../JUDGE_JSON_CONTRACT_GENERAL_PLAN.md). Baseline: [JUDGE_JSON_CONTRACT_FINDINGS.md](../JUDGE_JSON_CONTRACT_FINDINGS.md) § LLM API path, G6. **P0 only.**

**Goal:** Confirm RTU gateway (`ANTHROPIC_BASE_URL` `/v1/messages`) accepts judge `json_schema` before production wiring in P3.

## Decisions locked for P0

- Smoke script: `backend/scripts/test_anthropic_judge_gateway.py` — extend in place, no new script file.
- Judge schema fields: `outcome` enum (`upheld`, `dismissed`, `modified`) + optional `notes` string — matches `parse_judge_outcome`.
- Flags: `--structured`, `--prompt-file PATH`, `--chars N`, `--print-raw`; `--compare-direct` when both gateway + direct keys present (P0.2).
- P0 documents pass/fail matrix in `JUDGE_JSON_CONTRACT_FINDINGS.md` § P0 smoke results (dated subsection) — no worker code changes.
- `judge_finding()` signature unchanged in P0 — structured call uses private `anthropic_review._post_structured_judge_smoke` (script + P3 promotes to production path).

## PR review context (first commit)

- **Greptile:** `.greptile/files.json` — add `docs/review-pipeline/judge-json-contract/**`, `scope: ["backend/**"]`
- **Bugbot:** `.cursor/BUGBOT.md` — add judge-json-contract program links

## Out of scope for P0

- Worker manifest fields → **P1**
- Prompt policy changes → **P2**
- Production `judge_finding()` structured output → **P3**

---

## P0.1 — Program PR review context

**What:** Add Greptile + Bugbot entries for `judge-json-contract/` program docs.

**Files:** `.greptile/files.json`, `.cursor/BUGBOT.md`

**Deliverable:**

```bash
python -m json.tool .greptile/files.json > /dev/null
```

---

## P0.2 — Smoke script CLI flags

**What:** Add `argparse` to `test_anthropic_judge_gateway.py` — `--structured`, `--prompt-file`, `--chars`, `--print-raw`, `--compare-direct` (runs gateway then direct when both configured, prints side-by-side parse result); default prompt unchanged for backward compat.

**Files:** `backend/scripts/test_anthropic_judge_gateway.py`

**Deliverable (non-gate):** `pipenv run sh -c 'python -m scripts.test_anthropic_judge_gateway --help'` prints flags.

---

## P0.3 — Structured-output smoke path

**What:** When `--structured`, POST with `output_config.format` / `json_schema` for judge outcome object; assert response parses and `outcome` in allowed set. Implement via private `anthropic_review._post_structured_judge_smoke` (reused by P3 production wiring).

**Files:** `backend/scripts/test_anthropic_judge_gateway.py`, `backend/app/integrations/anthropic_review.py`

**Deliverable (non-gate):** Operator runs with RTU creds in `backend/.env`:

```bash
cd backend && pipenv run sh -c 'python -m scripts.test_anthropic_judge_gateway --structured --print-raw'
```

---

## P0.4 — Large-prompt replay flag

**What:** `--prompt-file` loads text from staging manifest export; `--chars N` pads or truncates for size sweep. Print `len(prompt)` and response parse result.

**Files:** `backend/scripts/test_anthropic_judge_gateway.py`

**Deliverable (non-gate):** Script accepts `--chars 1000` and `--chars 10000` without crash (live call optional).

---

## P0.5 — Document feasibility matrix

**What:** Add dated **P0 smoke results** subsection to findings — gateway structured on/off, direct fallback on/off, notes for P3 lock.

**Files:** `docs/review-pipeline/judge-json-contract/JUDGE_JSON_CONTRACT_FINDINGS.md`

**Deliverable:** Matrix table exists with at least placeholder rows for operator to fill after smoke run.

---

**Phase gate** (from `backend/`):

```bash
pipenv run ruff check scripts/test_anthropic_judge_gateway.py app/integrations/anthropic_review.py
pipenv run pytest tests/unit/test_anthropic_review.py -q
```

**Human gate (non-blocking):** Operator fills P0 smoke matrix with live RTU credentials before P3 starts.

**Next:** [JUDGE_JSON_CONTRACT_P1_EXECUTION.md](./JUDGE_JSON_CONTRACT_P1_EXECUTION.md)
