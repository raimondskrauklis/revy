# Review engineering context — general plan

**Baseline:** [REVIEW_ENGINEERING_CONTEXT_FINDINGS.md](./REVIEW_ENGINEERING_CONTEXT_FINDINGS.md) (platform locked, 2026-07-29)  
**Prerequisite:** `main` with judge-json-contract (#58) + review pipeline R3–R8; absorbs RQ-RC-1 dogfood items (RC1–RC2, RC5 inject).

**Thesis:** Revy Moonshot needs a **manifest-driven engineering-context layer** — JSON pointer, MD content, bounded inject before diff. Greptile consumes the same manifest in parallel. Bugbot stays manual this program.

**Gap IDs:** **RCX-*** in findings; **P0–P5** = program phases below.

**Locked:** RCX-D1–D10; Moonshot inject in P0 path (RCX-D8); raise diff cap (RCX-D10); latest-run metrics only (RCX-D6); no `BUGBOT.md` generator; RC4 DB post-program.

---

## Cross-cutting (every phase)

- **Tests:** `backend/tests/unit/` — manifest parse, extractor, inject/dedupe, manifest JSON fields, `context_stats` persist, staging script fixtures.
- **Trace:** Retrieve-step manifest + `github_review_runs.context_stats` (P0 migration) — operator can verify inject/caps without parsing prompt artifacts.
- **Tenancy:** workspace scope unchanged; manifest read from repo at `head_sha` only.
- **i18n:** backend-only — no new UI strings.
- **Validation:** extend `judge_json_contract_staging_metrics.py` review-context block; fill findings § Post-RCX + [JUDGE_JSON_CONTRACT_STAGING_VALIDATION.md](../judge-json-contract/JUDGE_JSON_CONTRACT_STAGING_VALIDATION.md) § Review context (`--since` post-deploy only).

---

## P0 — Foundations: manifest schema, caps, metrics migration

**Goal:** Shared primitives every later phase depends on — manifest shape, configurable caps, denormalized metrics row for staging SQL.

**Scope — in:** Alembic **`0029_review_context_stats`** — nullable `context_stats JSONB` on `github_review_runs` (denormalized snapshot: `active_program`, `diff_max_bytes`, `unified_diff_bytes`, `diff_truncated`, `omitted_files_count`, `omitted_md_count`, `engineering_context_injected`, `engineering_context_bytes`, `engineering_context_deduped_paths`, `lock_ids_extracted`, `prompt_chars`); config `revy_diff_max_bytes`, `revy_engineering_context_max_bytes`, `revy_pr_body_max_bytes` in `config.py` + `.env.example` (replace hardcoded 128 KB / 4 KB); dogfood manifest schema (`active_program` + `programs[]` with `paths` + `scope`) — source file `.greptile/review-context.json` (or extended `files.json` shape documented in execution); retrieve manifest field contract in `build_retrieval_manifest`; staging metrics script reads `context_stats` when present (fallback to retrieve manifest JSON).

**Scope — out:** Moonshot inject logic; Greptile file rewrite; judge prompt changes.

**Deliverables:** Migration applied; caps env-driven; manifest schema doc + JSON schema or typed parser stub; empty `context_stats` contract tested; metrics script P0 queries documented.

**Depends on:** `main` at `0028`.

---

## P1 — Lock/smoke extractor & manifest loader

**Goal:** Resolve pointed `.md` at `head_sha` and extract bounded locks + operator smoke — not full findings.

**Scope — in:** `engineering_context` service module — load manifest from repo (GitHub tree/compare at revision `head_sha`); scope filter vs `changed_files`; parse `## Locked decisions` tables + smoke sections (stable heading conventions per findings); byte-budget truncate; unit tests on fixture MD files.

**Scope — out:** Prompt assembly; Greptile sync.

**Deliverables:** `EngineeringContextPack` (or equivalent) with `active_program`, `lock_ids`, `extracted_text`, `source_paths`; loader errors surfaced for trace (missing path, empty extract).

**Depends on:** P0.

---

## P2 — Moonshot inject & pipeline instrumentation

**Goal:** `prepare_review_context` prepends engineering block before unified diff; dedupe when MD already fully in diff; persist metrics.

**Scope — in:** RCX-D8 algorithm in `github_review.py` — inject before diff, update review instruction to treat block as authoritative; dedupe skip list; populate retrieve manifest engineering fields + `context_stats` on review run at context prepare; unit tests for inject order, dedupe, truncation fallback.

**Scope — out:** Greptile `files.json` trim; judge reuse.

**Deliverables:** Moonshot prompt includes engineering block on scoped program PRs; pipeline trace shows `engineering_context_injected` + cap fields; `context_stats` row on completed review runs.

**Depends on:** P1.

---

## P3 — Active program trim, cap raise, Greptile sync

**Goal:** One manifest edit feeds Revy + Greptile; active program only; raised diff cap deployed.

**Scope — in:** Trim dogfood manifest to current program (3 docs: execution, findings, general plan); generate or validate `.greptile/files.json` from manifest (RCX-D9); set staging/prod `revy_diff_max_bytes` per RCX-D10 (calibrate from P0 baseline truncation %); CI path-exists check on manifest paths; phase-execution skill note for LOOP manifest update.

**Scope — out:** `BUGBOT.md` generator; nested `.greptile/` (RC3).

**Deliverables:** Greptile loads one program on `backend/**` PRs; cap raised with config documented; manifest + `files.json` in sync.

**Depends on:** P2.

---

## P4 — Judge context reuse

**Goal:** Judge path shares extracted locks where prompt budget allows — symmetric intent layer.

**Scope — in:** Reuse P1 extractor output in `github_finding_judge` / `judge_prompt_context` when escalation runs on program-touched files; bounded lock block in judge user prompt; manifest/judge artifact notes `lock_ids_cited` optional field.

**Scope — out:** New judge parse contract; Moonshot changes.

**Deliverables:** Judge prompts include lock IDs on program PRs; unit tests; no regression to judge-json-contract persistence.

**Depends on:** P2.

---

## P5 — Staging validation & program closeout

**Goal:** Human gate — metrics prove inject + caps work on dogfood PRs.

**Scope — in:** Run staging metrics `--since` post-deploy; fill validation tables (diff truncated %, omitted `.md`, inject %, prompt p95, manual contradict-locks check); `REVIEW_ENGINEERING_CONTEXT_STAGING_VALIDATION.md` stub; program README done; recovery checklist Track M row.

**Scope — out:** RC4 `workspace_review_policy` spike (RCX-G8 — separate program); disposition helpers (RCX-G7 — optional follow-up).

**Deliverables:** Filled validation memo; pass/fail gates from findings; operator sign-off.

**Depends on:** P3–P4 on staging.

---

## Open calibration

**`revy_diff_max_bytes` value** — **baseline captured 2026-07-29:** 25% diff truncated, 9/40 runs omitted `.md`, prompt p95 164k chars. **Default to 512 KB** in P3 unless post-cap script shows <5% truncated at 256 KB trial.

**Next step:** **`create-execution-plan`** → `waves/REVIEW_ENGINEERING_CONTEXT_EXECUTION.md` starting at P0.
