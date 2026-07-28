# Judge input quality — general plan

**Baseline:** [JUDGE_INPUT_INVESTIGATION_FINDINGS.md](./JUDGE_INPUT_INVESTIGATION_FINDINGS.md) (staging + web research, 2026-07-28)  
**Prerequisite:** Review-pipeline **R5** shipped ([#29](https://github.com/raimondskrauklis/revy/pull/29)); review-quality **R4** evidence snippet + grounding judge shipped (PR #50).

**Thesis:** Moonshot **discovers** on full diff (~147k chars); Claude **verifies** one Moonshot claim per call with **scoped code evidence** (hunk/patch), not a second full-PR review. Thin judge input (~1k chars) is the quality bottleneck — not model choice alone.

**Gap IDs:** **J-*** in findings; **P0–P5** = program phases below.

**Locked:** [R5-Q3](../REVIEW_PIPELINE_FINDINGS.md) escalation gate unchanged (`error`/`critical`, or `security` + `severity ≥ warning`, max 10/run, skip when no judge LLM path); no full unified diff to judge; verifier role forbids scope creep; direct `ANTHROPIC_API_KEY` preserved — gateway additive only.

**Already shipped (do not re-implement in execution):** Anthropic gateway profile + direct fallback (`anthropic_review.py`, `config.judge_llm_enabled`, smoke script, unit tests on `feat/anthropic-judge-gateway`). P1 verifier prompts in **working tree** (not yet on `main`).

---

## Cross-cutting (every phase)

- **Tests:** `backend/tests/unit/` per phase; fixtures for line-less findings, compare-failure, patch-only evidence, patch reload at judge time.
- **Trace:** Judge step manifest records verifier framing + scoped context (`user_prompt`, `evidence_snippet`, `file_patch_chars` when P3 ships).
- **Tenancy:** workspace scope unchanged on all reads.
- **i18n:** backend-only — no new user-facing UI strings.
- **Publish:** grounded `dismissed` / `modified` outcomes flow through existing reconcile + publish filters — see J-10 product note under P1.

---

## P0 — Evidence & hunk primitives (J-1, J-2, J-3, J-11)

**Goal:** Shared helpers to resolve **file patch / diff hunk** and evidence snippets from compare patches — usable at review ingest and judge time.

**Scope — in:** Extend `resolve_evidence_snippet` / `extract_evidence_from_patch` (include `-` lines for removed-code findings); add `resolve_judge_code_context(file_path, start_line, patches_by_file)` returning snippet + capped file patch; calibrated caps as constants; fail-soft when `start_line` missing but patch exists; unit test for group vs finding severity alignment at judge candidate selection.

**Scope — out:** enclosing-symbol / LSP read; schema migrations; compare re-fetch (P3).

**Deliverables:** Primitive API + unit tests for anchored, line-less, deleted-hunk, and missing-patch cases; documented cap constants for execution calibration.

**Depends on:** R5 + R4 evidence column on `github_findings`.

---

## P1 — Verifier prompt contract (J-5, J-7, J-10)

**Goal:** Judge LLM contract states **Moonshot verifier** role — validate this claim only; no full PR review; conservative `dismissed`/`modified` when evidence thin.

**Scope — in:** Ship `JUDGE_SYSTEM_PROMPT` + `_build_judge_prompt` header (already in working tree); retain E2 entailment rubric; Bedrock judge reuses same system string; **unit tests assert verifier framing** in built prompt.

**Scope — out:** Hunk attachment (P3); changing `modified` application logic unless product locks J-10 decision.

**Product note (J-10):** Verifier prompt allows severity downgrade via `modified`; code today always sets `group.severity = warning`. **Lock v1** (warning-only) in execution unless explicitly expanded.

**Deliverables:** Prompts on `main`; tests for Moonshot verifier header + system prompt strings; documented J-10 decision.

**Depends on:** None for prompt-only — may ship before P0.

---

## P2 — Evidence capture at review ingest (J-2, J-3, J-9, J-12)

**Goal:** Raise staging coverage of `evidence_snippet` and `start_line` on judge-eligible findings (baseline ~53% with evidence).

**Scope — in:** Wider context window (e.g. 5 → 15 lines); fail-soft file patch when line anchor fails; `start_line` coercion (`0` handling, optional string → int); path normalization vs compare `filename` keys; diagnose NULL evidence when `file_path` missing or `patches_by_file` empty (compare failure / index-only).

**Scope — out:** Judge prompt changes beyond ingest; PR body (P4).

**Deliverables:** Improved evidence coverage on diff-backed findings; unit tests; staging SQL checklist with `missing_file_path` + index_mode breakdown vs baseline.

**Depends on:** P0.

---

## P3 — Scoped context in judge step (J-1, J-6, J-8)

**Goal:** Each judge candidate receives **per-finding file patch** (~2–8k chars) plus evidence snippet — not whole PR diff.

**Scope — in:** `_build_judge_prompt` includes capped patch block; **patch reload:** re-fetch via `_fetch_compare_patches` (`github_resolution_metrics.py`) using review run base/head revisions at judge entry (review context is gone in reconcile). Shared helper or import — do not parse truncated full review prompt artifact. Pipeline trace stores patch length / preview in judge manifest.

**Scope — out:** Full PR diff to judge; persist `patches_by_file` on review manifest unless compare re-fetch proves too costly in staging.

**Deliverables:** Judge `user_prompt` bounded but > message-only (~1k); trace replay shows claim + code slice; unit tests for patch reload + prompt assembly.

**Depends on:** P0, P1. **Must not ship without P0 + J-8 reload design.**

---

## P4 — Moonshot reviewer input (J-4)

**Goal:** Primary reviewer sees PR description — persist `body` on `github_pull_requests` via webhook ingest.

**Scope — in:** Alembic `body` column; `_extract_pr_fields` + `_upsert_pull_request`; `edited` webhook action; wire `pull_request.body` in `prepare_review_context`.

**Scope — out:** Per-review API fetch workaround; judge changes; index/retrieval changes.

**Deliverables:** Review pipeline trace `prompt` includes PR body when present; unit test on `_build_review_prompt`.

**Depends on:** None (may parallel P2).

---

## P5 — Staging validation gate

**Goal:** End-to-end proof on staging after P1–P3 — judge quality improves vs investigation baseline; gateway path works without breaking direct Anthropic.

**Scope — in:** Staging runs with judge candidates; SQL replay (evidence %, prompt sizes); smoke script green; short validation note (findings appendix or recovery checklist). Optional: RTU Opus model id on gateway if not already configured.

**Scope — out:** Re-implementing gateway client, config, or smoke script (already on gateway branch); R5-Q3 threshold changes; Reviewer UI.

**Deliverables:** Documented before/after metrics (small N); gateway + direct paths verified on staging.

**Depends on:** P1–P3.

---

## Open calibration (after P2–P3)

Exact **hunk cap** and **context line** counts — tune from staging replay (illustrative: 2–8k patch, 10 candidates × ~4k ≪ 147k review).

---

## Next step

**`create-execution-plan`** → [waves/JUDGE_INPUT_QUALITY_EXECUTION.md](./waves/JUDGE_INPUT_QUALITY_EXECUTION.md) (**done**). Next: **`execution-peer-review`** → `phase-execution`.
