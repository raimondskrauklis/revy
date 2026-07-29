# Judge JSON contract — program index

**Status:** **code-complete (P0–P5)** on `feat/judge-json-contract` — operator staging sign-off pending ([validation memo](./JUDGE_JSON_CONTRACT_STAGING_VALIDATION.md)).

**Problem:** Anthropic judge returns HTTP 200 but Revy often fails to parse/persist `outcome` → no `github_finding_judge_outcomes` row → RG-6 withholds escalation inline publish.

**Not in scope:** Moonshot review JSON (healthy on staging); finding-resolution closure schema (`0028`).

| Doc | Purpose |
|-----|---------|
| [JUDGE_JSON_CONTRACT_FINDINGS.md](./JUDGE_JSON_CONTRACT_FINDINGS.md) | Baseline — where we are, goals, locked decisions, API smoke |
| [JUDGE_JSON_CONTRACT_GENERAL_PLAN.md](./JUDGE_JSON_CONTRACT_GENERAL_PLAN.md) | P0–P5 phases (general — no execution steps) |
| [waves/JUDGE_JSON_CONTRACT_EXECUTION.md](./waves/JUDGE_JSON_CONTRACT_EXECUTION.md) | LOOP index + locked decisions |
| [JUDGE_JSON_CONTRACT_STAGING_VALIDATION.md](./JUDGE_JSON_CONTRACT_STAGING_VALIDATION.md) | Operator staging gate (P5 human sign-off) |

**Incident / staging evidence:** [FINDING_RESOLUTION_TECHNICAL_FINDINGS.md](../finding-resolution/FINDING_RESOLUTION_TECHNICAL_FINDINGS.md) (PR #57 dogfood).

**Related programs**

| Program | Link |
|---------|------|
| Judge input quality (shipped) | [judge/README.md](../judge/README.md) |
| Finding resolution (shipped) | [finding-resolution/README.md](../finding-resolution/README.md) |
| RC-D13 / RC-D17 (Moonshot modes) | [REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md](../REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md) |

**Related code**

| Area | Path |
|------|------|
| Judge LLM + parse | `backend/app/integrations/anthropic_review.py` |
| Judge loop + manifest | `backend/app/services/github_finding_judge.py` |
| Prompt + evidence context | `backend/app/services/github_review.py` |
| RG-6 publish gate | `backend/app/services/github_publish.py` |
| Gateway smoke script | `backend/scripts/test_anthropic_judge_gateway.py` |

**Staging DB** — `PRODUCTION_DATABASE_URL` → `revy-staging` ([DATABASE_CONNECTION_GUIDE.md](../../utils/DATABASE_CONNECTION_GUIDE.md)).

**LLM path (keep simple):** Revy judge uses **RTU Anthropic Messages API** — `ANTHROPIC_BASE_URL` + `ANTHROPIC_AUTH_TOKEN` → `{base}/v1/messages`. No extra proxy layer required for the app. [llm-rdi-services-runbook.md](../../utils/llm-rdi-services-runbook.md) is a separate LiteLLM stack for Cursor; optional for Revy workers.

## Execution (LOOP order)

| Phase | Focus | File | Status |
|-------|--------|------|--------|
| P0 | API smoke + structured-output feasibility | [P0](./waves/JUDGE_JSON_CONTRACT_P0_EXECUTION.md) | done (`b7cadcc`) |
| P1 | Failure observability (G1) | [P1](./waves/JUDGE_JSON_CONTRACT_P1_EXECUTION.md) | done (`af32999`) |
| P2 | Snippet-first prompts (G3) | [P2](./waves/JUDGE_JSON_CONTRACT_P2_EXECUTION.md) | done (`9f8b7b3`) |
| P3 | Structured output + parse fallback | [P3](./waves/JUDGE_JSON_CONTRACT_P3_EXECUTION.md) | done (`24dd54e`) |
| P4 | Targeted retry (G5) | [P4](./waves/JUDGE_JSON_CONTRACT_P4_EXECUTION.md) | done (`60eb2ca`) |
| P5 | Staging validation + doc sync | [P5](./waves/JUDGE_JSON_CONTRACT_P5_EXECUTION.md) | code-complete — human gate pending |

**Next step:** Deploy `main` to staging → dogfood PR → fill [validation memo](./JUDGE_JSON_CONTRACT_STAGING_VALIDATION.md) (metrics script in [BACKEND_SCRIPTS_RUNBOOK.md](../../utils/BACKEND_SCRIPTS_RUNBOOK.md)).
