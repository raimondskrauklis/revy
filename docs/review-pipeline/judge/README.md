# Judge program — input quality & escalation

**Status:** P0–P5 **implemented** on `feat/judge-input-quality` — staging human gate pending ([validation memo](./JUDGE_INPUT_QUALITY_STAGING_VALIDATION.md)).

**Transport reliability (T0–T3):** **closed partial PASS** — [#75](https://github.com/raimondskrauklis/revy/pull/75) `1c416a0` merged; direct judge + T1 logging verified via evidence-only probe [#76](https://github.com/raimondskrauklis/revy/pull/76); gateway fallback deferred to JT-Q6 ops ([validation memo](./JUDGE_TRANSPORT_RELIABILITY_STAGING_VALIDATION.md)).

**Design direction (findings + web research):** Moonshot gets the full diff for discovery; the judge should **verify Moonshot’s specific claims** with scoped code evidence (hunk/patch), not re-review the entire PR. See findings § Industry practice.

| Doc | Purpose |
|-----|---------|
| [JUDGE_INPUT_INVESTIGATION_FINDINGS.md](./JUDGE_INPUT_INVESTIGATION_FINDINGS.md) | Staging DB + code-path analysis (2026-07-28) |
| [JUDGE_TRANSPORT_RELIABILITY_FINDINGS.md](./JUDGE_TRANSPORT_RELIABILITY_FINDINGS.md) | RTU/direct transport, fallback, worker logging (2026-07-31) |
| [JUDGE_TRANSPORT_RELIABILITY_GENERAL_PLAN.md](./JUDGE_TRANSPORT_RELIABILITY_GENERAL_PLAN.md) | T0–T3 transport hardening program |
| [waves/JUDGE_TRANSPORT_RELIABILITY_EXECUTION.md](./waves/JUDGE_TRANSPORT_RELIABILITY_EXECUTION.md) | Transport reliability LOOP index (T0–T3) |
| [JUDGE_INPUT_QUALITY_GENERAL_PLAN.md](./JUDGE_INPUT_QUALITY_GENERAL_PLAN.md) | P0–P5 program phases (general — no execution steps) |
| [waves/JUDGE_INPUT_QUALITY_EXECUTION.md](./waves/JUDGE_INPUT_QUALITY_EXECUTION.md) | LOOP index + P0–P5 execution files |

**Related code**

| Area | Path |
|------|------|
| Moonshot reviewer prompt | `backend/app/integrations/moonshot_review.py` |
| Review context assembly | `backend/app/services/github_review.py` (`prepare_review_context`, `_build_review_prompt`) |
| Evidence snippet extraction | `backend/app/services/github_review.py` (`resolve_evidence_snippet`, `extract_evidence_from_patch`) |
| Judge prompt + escalation | `backend/app/services/github_finding_judge.py` |
| Pipeline trace (prompts stored) | `backend/app/services/github_pipeline_trace.py` |
| Anthropic judge client | `backend/app/integrations/anthropic_review.py` |

**Staging DB** — `PRODUCTION_DATABASE_URL` → `revy-staging` (see [DATABASE_CONNECTION_GUIDE.md](../../utils/DATABASE_CONNECTION_GUIDE.md)).

**R5 policy (locked)** — judge runs only for `error` / `critical`, or `security` with `severity ≥ warning`; max 10 calls per review run; skipped when no judge LLM path (`judge_llm_enabled()` — direct `ANTHROPIC_API_KEY` **or** gateway `ANTHROPIC_BASE_URL` + token). See `REVIEW_PIPELINE_FINDINGS.md` R5-Q3.
