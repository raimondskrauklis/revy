# Model policy — general plan

From [MODEL_POLICY_FINDINGS.md](./MODEL_POLICY_FINDINGS.md). **No file lists or steps** — use `create-execution-plan` per phase.

**Cross-cutting:** unit tests (`backend/tests/unit/`); hand-written Alembic for new tables; structured logging; EN+LV for new user-facing strings; API + resolver before UI; workspace audit events on policy changes.

---

## Locked decisions

| # | Decision |
|---|----------|
| MP-D1 | **Role-based policy** — slots: `embedding`, `reviewer_standard` / `reviewer_deep` / `reviewer_critical`, `judge`; `jury` reserved, not v1 |
| MP-D2 | **`(provider, model_id)` pairs** — Bedrock IDs ≠ Anthropic API IDs; no bare model string |
| MP-D3 | **Bedrock is first-class** — `bedrock` alongside `moonshot` and `anthropic`; IAM or keys via platform env |
| MP-D4 | **Moonshot stays direct for reviewer** — Kimi not on Bedrock; optional Bedrock Claude for reviewer is operator choice, not default |
| MP-D5 | **Voyage embeddings unchanged** — workspace embedding dropdown **out of v1** (dim migration risk) |
| MP-D6 | **Platform defaults via env** — workspace row overrides; **no row = platform default** (PATCH `null` clears) |
| MP-D7 | **Generator ≠ judge family** — UI discourages same provider for reviewer + judge; override allowed for dev |
| MP-D8 | **BYOK deferred** — platform credentials only; secrets stay on droplet / IAM, never in workspace UI |
| MP-D9 | **Settings route** — `/settings/review` (flat sibling; SETTINGS_IA); not PR findings UI |
| MP-D10 | **Jury / reranker / plan gates** — out of this program; map in findings §6 for later |
| MP-D11 | **Async session-aware resolver** — `async def resolve_model(session, workspace_id, role)` from M0 |
| MP-D12 | **`model_id` on wire** — dispatch passes `ModelRef.model_id` (and `region`) into all LLM integrations |
| MP-D13 | **Reviewer provider env** — `revy_reviewer_provider` canonical; `revy_llm_provider` deprecated alias one release |
| MP-D14 | **Split credential gates** — `reviewer_llm_enabled` / `judge_llm_enabled` (not Anthropic-key-only skip) |
| MP-D15 | **Run observability** — set `github_review_runs.provider` + `model_id` at **execution**; judge outcomes store `judge_provider` + `judge_model_id` |

---

## M0 — Model role foundations

**Goal:** Shared `ModelRole` + `ModelRef` types and a platform-level resolver; review and judge call resolver instead of hardcoded integrations.

**Scope:** In — `ModelRole` + `ModelRef`; **`async def resolve_model(session, workspace_id, role)`** (env-only in M0); `model_id` passed through dispatch into integrations; `reviewer_llm_enabled` / `judge_llm_enabled`; refactor R4/R5; migration `0022` adds `github_review_runs.model_id` + judge outcome model columns; persist provider/model at execution. Out — Bedrock adapter; workspace DB rows; UI.

**Deliverables:** Resolver module; refactored R4/R5 services; tests proving env fallback matches today’s defaults.

**Depends on:** Findings baseline.

---

## M1 — AWS Bedrock LLM provider

**Goal:** Operators with AWS accounts can run judge (and optionally reviewer) via Bedrock without `ANTHROPIC_API_KEY`.

**Scope:** In — `bedrock_review.py`; `revy_judge_provider`, `revy_reviewer_provider`; single `revy_bedrock_reviewer_model_id` for all reviewer profiles at platform level; `aws_region`; optional `revy_bedrock_inference_profile_arn` (documented, optional v1). Out — workspace overrides; UI.

**Deliverables:** Bedrock adapter; platform env wiring; staging smoke path documented.

**Depends on:** M0.

---

## M2 — Workspace model policy (API)

**Goal:** Per-workspace model overrides stored in PostgreSQL and applied by the resolver.

**Scope:** In — `workspace_model_policies` table; admin GET/PATCH; catalog from **shared registry** with resolver; resolver DB branch. Out — frontend; jury; embedding role in API v1.

**Deliverables:** Migration; schemas; API routes; resolver workspace branch; tests.

**Depends on:** M1.

---

## M3 — Review settings UI

**Goal:** Workspace admins configure reviewer and judge models from the app.

**Scope:** In — `/settings/review` route + sidebar (SETTINGS_IA); four model dropdowns + autostart; catalog-driven; EN+LV. Out — custom rules; jury; embedding; BYOK.

**Deliverables:** Settings page; i18n keys; integration with M2 API; admin-only gate.

**Depends on:** M2.

---

## Out of program (explicit)

| Item | Where |
|------|--------|
| Jury / majority voting | Future program after cost telemetry |
| Plan-tier model caps (Q9) | After M3 + billing metrics |
| Per-workspace BYOK | MP-Q1 defer |
| Local/HF embedding backend | R3 parallel track |
| Reranker model slot | R3-Q3 defer |
| Grounding judge enrichment | R9 defer — same `judge` slot later |

---

## Open item

**Bedrock reviewer in production:** default remains Moonshot reviewer + Bedrock or Anthropic judge; enabling `revy_reviewer_provider=bedrock` is operator opt-in after staging cost/latency smoke (MP-D4).

**Next step:** [`waves/README.md`](./waves/README.md) — **`phase-execution`** M0→M3 (peer-reviewed 2026-07-26).
