# Judge transport reliability — execution index

**Program:** [../README.md](../README.md) · **Baseline:** [JUDGE_TRANSPORT_RELIABILITY_FINDINGS.md](../JUDGE_TRANSPORT_RELIABILITY_FINDINGS.md) · **General plan:** [JUDGE_TRANSPORT_RELIABILITY_GENERAL_PLAN.md](../JUDGE_TRANSPORT_RELIABILITY_GENERAL_PLAN.md)

**Authority:** [JUDGE_JSON_CONTRACT_FINDINGS.md](../../judge-json-contract/JUDGE_JSON_CONTRACT_FINDINGS.md) · [BACKEND_SCRIPTS_RUNBOOK.md](../../../utils/BACKEND_SCRIPTS_RUNBOOK.md)

**Goal:** One judge workflow; RTU gateway + direct Anthropic transport hardened with worker-visible logging and gateway→direct fallback on real failure modes.

**Branch:** `feat/judge-transport-reliability` (suggested)

## Out of scope (program)

- FR-CS4 Pass 3 supersede / finding-resolution closure logic
- `REVY_JUDGE_STRUCTURED_OUTPUT` on direct (defer to parking lot unless T3 metrics require)
- Moonshot reviewer transport; `llm.rdi.services` proxy
- Migrations; frontend / i18n

## How we work (locked)

```text
T0 → T1 → T2 → T3
each phase: implement → pytest gate (when code) → Bugbot → commit
```

**Gap IDs (JT-*):** findings catalog. **T0–T3:** program phases below.

## Decisions locked for execution

- **JT-Q1:** One workflow — transport profiles only; no forked discovery vs Pass 3 loops.
- **JT-Q3:** Gateway `JudgeParseError` or empty/invalid body → try direct profile when configured.
- **JT-Q4:** Worker logs: `profile`, `url`, `model_id`, `duration_ms`, usage summary, `parse_error` — never full prompt.
- **JT-Q5:** `REVY_JUDGE_STRUCTURED_OUTPUT` on direct — **defer** unless T3 metrics show parse failures remain.
- **JT-Q6:** Staging judge path: RTU gateway **and** `ANTHROPIC_API_KEY` both set.
- **RG-6:** Withhold publish without judge outcome — unchanged.
- **FR-CS4:** Supersede-before-Pass-3 — **out of scope** (finding-resolution).
- **i18n:** Backend-only — no new frontend strings.
- **Migrations:** None in this program.

## LOOP order

| Phase | Focus | Execution | Status |
|-------|--------|-----------|--------|
| T0 — Baseline | Incident manifest + env gate + metrics snapshot | [JUDGE_TRANSPORT_RELIABILITY_T0_EXECUTION.md](./JUDGE_TRANSPORT_RELIABILITY_T0_EXECUTION.md) | done |
| T1 — Logging | Worker-visible judge transport events | [JUDGE_TRANSPORT_RELIABILITY_T1_EXECUTION.md](./JUDGE_TRANSPORT_RELIABILITY_T1_EXECUTION.md) | done |
| T2 — Fallback | Gateway parse/empty → direct profile | [JUDGE_TRANSPORT_RELIABILITY_T2_EXECUTION.md](./JUDGE_TRANSPORT_RELIABILITY_T2_EXECUTION.md) | done |
| T3 — Staging gate | Smoke + metrics + validation memo + doc sync | [JUDGE_TRANSPORT_RELIABILITY_T3_EXECUTION.md](./JUDGE_TRANSPORT_RELIABILITY_T3_EXECUTION.md) | **closed partial PASS** — T3.3 direct verified ([#76](https://github.com/raimondskrauklis/revy/pull/76) evidence); T3.1/T3.2 deferred |

**Peer review:** Incorporated 2026-07-31 (manifest SQL, T1 started event, T2.1 wording, gates).
