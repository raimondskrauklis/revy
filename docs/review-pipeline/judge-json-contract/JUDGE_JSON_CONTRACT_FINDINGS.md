# Judge JSON contract — findings

**Date:** 2026-07-28  
**Purpose:** Baseline for the **next review-pipeline wave** — reliable judge outcome JSON, observability, and prompt policy. **No execution steps.**

**When to start:** After [finding-resolution](../finding-resolution/README.md) merges. Docs may land on the finding-resolution branch for agent handoff; **implementation** starts on a fresh branch from `main`.

**Evidence:** Staging DB `revy-staging`; [FINDING_RESOLUTION_TECHNICAL_FINDINGS.md](../finding-resolution/FINDING_RESOLUTION_TECHNICAL_FINDINGS.md); code on `main` (`9dbaf96` judge) + PR #57 dogfood (`c0522ec`).

---

## Summary

Judge escalation is **broken often on staging**: of judge-manifest candidates in recent runs, most end with `outcome=null` and **no** `github_finding_judge_outcomes` row. Moonshot findings JSON is **fine** (0 drops in last 30 review runs). The active gap is **judge output contract + observability + prompt bloat**, not discovery.

**Operator thesis (validated):** models do not always follow prompt-only JSON; fix with API structured output + snippet-first prompts + failure trace — not by relaxing RG-6 or adding retry storms.

---

## Where we are

### Staging metrics (2026-07-28)

| Metric | Value |
|--------|------:|
| Completed runs with judge candidates | 16 |
| Runs with ≥1 persisted outcome | 5 |
| Runs with candidates, 0 outcomes | 11 |
| Judge manifest candidates (last 30 steps) | 15 total — **2** ok, **13** failed |
| Moonshot `parse_report` drops (last 30 reviews) | 0 / 69 parsed |

### Repro run — PR #57 head `c0522ec`

| Item | State |
|------|--------|
| Moonshot | 1 finding parsed |
| Judge | 1 candidate, `judged_count=0`, manifest `raw_response=null` |
| `judge_status` | `skipped_unavailable` |
| RG-6 | Escalation finding **not** inline-published |
| Prompt size | **10,360** chars (`file_patch_chars=8186` + evidence snippet) |
| Successful judges (historical) | ~**995** chars avg prompt |

### Code today

| Layer | Behavior | Gap |
|-------|----------|-----|
| **Moonshot review** | `response_format: json_object` | OK on staging |
| **Judge API** | Prompt-only JSON; `json.loads(text)` | No structured output, no fence strip |
| **On parse fail** | `github_finding_judge_failed`; manifest clears `raw_response` | Cannot post-mortem from DB |
| **Run status** | Missing any candidate outcome → `skipped_unavailable` | Correct |
| **Publish** | RG-6 withholds escalation without outcome row | **Locked — keep** |
| **Judge prompt** | `evidence_snippet` **and** up to 8k `file_patch` | Redundant; violates find→verify thesis |

### Programs already shipped

| Program | Relevance |
|---------|-----------|
| [Judge input quality](../judge/README.md) P0–P5 | Added `file_patch` to judge prompt + trace — **overshot** (full file, not hunk-only) |
| [Finding resolution](../finding-resolution/README.md) | Surfaces judge failure via RG-6 on dogfood; `0028` orthogonal to parse |

---

## Locked decisions (discussion 2026-07-28)

| ID | Decision |
|----|----------|
| **JC-D1** | **RG-6 withhold stays** — do not publish escalation inline without a judge outcome row. Fix reliability upstream. |
| **JC-D2** | **Keep LLM path simple** — Revy uses RTU/direct Anthropic Messages (`ANTHROPIC_BASE_URL` + token). No requirement to route workers through `llm.rdi.services` LiteLLM proxy. |
| **JC-D3** | **Moonshot unchanged** unless `parse_report` regresses; RC-D17 separate modes already shipped for issue comments. |
| **JC-D4** | **Snippet-first prompt** — when `evidence_snippet` exists, do not attach full `file_patch`; patch is fallback for line-less / thin-evidence cases only (lower cap). |
| **JC-D5** | **Measure before heavy parse hacks** — persist failure bodies first; then structured output + light fence strip. |
| **JC-D6** | **Timing** — optional tiny hotfix to `main` only if blocking merge; else full wave after finding-resolution ships. Implementation branch off `main`, not `feat/finding-resolution`. |

---

## What we need to achieve

### Success criteria (staging)

1. **≥95%** judge candidates persist a valid `outcome` row on dogfood PRs with escalation findings.
2. Judge manifest always records **success or failure body** — no more `raw_response=null` on failed HTTP 200.
3. Judge `user_prompt` p50 **≤2k chars** when `start_line` + snippet present (down from 10k+ failure case).
4. RG-6 warnings (`judge_candidate_unpublished_missing_outcome`) rare and only on genuine judge `dismissed`/policy cases — not parse noise.

### Deliverables (for general plan)

| # | Deliverable | Notes |
|---|-------------|--------|
| **G1** | Failure observability | `raw_response_text` + `parse_error` on judge manifest candidates; structured log field |
| **G2** | Anthropic structured output | `output_config.format` / `json_schema` on `judge_finding()` for gateway + direct paths |
| **G3** | Snippet-first prompt policy | Skip `file_patch` when snippet present; tiered fallback + lower cap (~2k) |
| **G4** | Light parse helper | Strip markdown fences, extract first JSON object — fallback when structured output unavailable |
| **G5** | Optional single retry | Max 1 retry with validation error in prompt — only if G2+G4 still show failures in smoke |
| **G6** | API smoke scripts | Extend `test_anthropic_judge_gateway.py` — plain vs structured vs 10k prompt |
| **G7** | Unit tests | Parse helper, prompt assembly tiers, manifest failure fields |
| **G8** | Staging validation memo | Human gate after deploy — same pattern as judge input quality |

### Explicitly out of scope (v1)

- Relaxing `outcome` enum or RG-6 publish rules
- Second judge model / Opus escalation
- Unbounded retry loops
- Moonshot schema migration
- `llm.rdi.services` proxy for Celery workers

---

## LLM API path (simple)

Revy worker config (`backend/.env.example`):

```text
ANTHROPIC_BASE_URL=https://llm.ai.rtu.lv
ANTHROPIC_AUTH_TOKEN=…
# optional direct fallback:
# ANTHROPIC_API_KEY=…
REVY_ANTHROPIC_GATEWAY_MODEL=azure_ai/claude-sonnet-5
```

Code: `anthropic_review.py` → `{ANTHROPIC_BASE_URL}/v1/messages`, gateway profile first, direct API fallback.

[llm-rdi-services-runbook.md](../../utils/llm-rdi-services-runbook.md) documents a **separate** LiteLLM OpenAI-compat proxy (`llm.rdi.services`) for Cursor — useful reference, **not** required for Revy judge.

**Structured output:** Anthropic GA + LiteLLM unified `/v1/messages` support `output_format` / `output_config.format` with `json_schema`. Verify on RTU with smoke script before coding G2.

---

## Local API testing (scripts)

Add judge credentials to **local** `backend/.env` (gitignored) — same vars as staging worker. No deploy needed to validate API shape.

From `backend/`:

```bash
# Basic judge smoke (existing)
pipenv run python scripts/test_anthropic_judge_gateway.py
```

**Planned extensions (G6 — implement in wave):**

| Script / flag | Purpose |
|---------------|---------|
| `test_anthropic_judge_gateway.py --structured` | Judge schema via `output_config.format`; assert `outcome` enum |
| `--prompt-file` / `--chars N` | Replay 1k vs 10k prompt sizes from staging manifest |
| `--print-raw` | Dump message text before parse (debug) |

Optional: one-off compare gateway vs direct when both keys present — confirm same schema behavior; pick one path in production (JC-D2: RTU gateway is enough).

---

## Industry alignment

| Pattern | Revy |
|---------|------|
| **Find → verify** (Moonshot discovers, judge verifies one claim) | R5 locked — [judge general plan](../judge/JUDGE_INPUT_QUALITY_GENERAL_PLAN.md) |
| **Verifier context = claim + anchor + excerpt** | `evidence_snippet` — not full file diff |
| **Level 3 JSON** (schema-constrained API) | Moonshot L2 (`json_object`); judge still L1 (prompt-only) |
| **Persist raw on failure** | Review step yes; judge step **no** — G1 fixes |
| **RC-D17** one completion shape per output | Issue comment vs findings split shipped; judge needs API schema |

---

## Root-cause hypotheses (ranked)

| Rank | Hypothesis | Evidence |
|------|------------|----------|
| 1 | Prompt-only JSON on judge (no structured output) | Code; industry failure rates |
| 2 | Prompt bloat — `file_patch` + snippet | 10k failed vs ~1k success prompts |
| 3 | Failure observability gap | Cannot confirm parse vs transport from DB |
| 4 | Gateway quirk | Less likely — HTTP 200; same path worked historically |

---

## Gap IDs (for general plan)

| ID | Gap |
|----|-----|
| **JC-1** | No structured output on judge Messages API |
| **JC-2** | Failure path discards response body in manifest |
| **JC-3** | Redundant full-file `file_patch` when snippet exists |
| **JC-4** | No shared `parse_llm_json_object` helper |
| **JC-5** | Smoke script does not test structured output or large prompts |
| **JC-6** | No staging validation memo for this wave |

---

## Reproduce staging

See SQL in [FINDING_RESOLUTION_TECHNICAL_FINDINGS.md](../finding-resolution/FINDING_RESOLUTION_TECHNICAL_FINDINGS.md) § Reproduce.

DB connect: [DATABASE_CONNECTION_GUIDE.md](../../utils/DATABASE_CONNECTION_GUIDE.md) — `PRODUCTION_DATABASE_URL`, asyncpg + relaxed SSL for DO locally.

---

## Next steps

1. ~~Merge finding-resolution PR (code + these docs).~~ ✓ merged #57 (`a73c9ff`).
2. ~~`create-general-plan`~~ → [JUDGE_JSON_CONTRACT_GENERAL_PLAN.md](./JUDGE_JSON_CONTRACT_GENERAL_PLAN.md) ✓
3. ~~`create-execution-plan`~~ → [waves/JUDGE_JSON_CONTRACT_EXECUTION.md](./waves/JUDGE_JSON_CONTRACT_EXECUTION.md) ✓
4. ~~`execution-peer-review`~~ ✓ (2026-07-28) — P1 integration-layer + P4.4 fixes applied → `phase-execution` on `feat/judge-json-contract`.
5. Optional: operator adds RTU env to local `backend/.env` and runs smoke script before wave starts.
