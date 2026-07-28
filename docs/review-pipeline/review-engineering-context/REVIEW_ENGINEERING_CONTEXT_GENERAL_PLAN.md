# Review engineering context — general plan

**Baseline:** [REVIEW_ENGINEERING_CONTEXT_FINDINGS.md](./REVIEW_ENGINEERING_CONTEXT_FINDINGS.md) (peer-reviewed, 2026-07-29)  
**Prerequisite:** `main` with judge-json-contract (#58) + review pipeline R3–R8; **supersedes RQ-RC-1** dogfood items (RC1, RC2, RC5 inject).

**Thesis:** Revy Moonshot needs a **manifest-driven engineering-context layer** — SSOT JSON pointer, MD content, bounded inject before diff (P2). Greptile consumes **generated** `files.json` (P3). Bugbot stays manual.

**Gap IDs:** **RCX-*** in findings; **P0–P5** below are **execution authority** (overrides findings deliverable phase labels).

**Locked:** RCX-D1–D12; inject **P2**; cap default **512 KB in P0 config** (RCX-D10); SSOT `.greptile/review-context.json` (RCX-D11); dedupe RCX-D12.

---

## Cross-cutting (every phase)

- **Tests:** `backend/tests/unit/` — manifest parse, extractor fixtures from real program MD, inject/dedupe, `context_stats`, staging script.
- **Trace:** Single retrieve manifest — `engineering_context_*` keys **alongside** existing SC3 fields (`structural_context_mode`, `caller_files_*`); no second manifest. `github_review_runs.context_stats` (P0 migration, P2 populate).
- **Module owner:** `app/services/engineering_context/` — manifest schema, extract, loader; shared by Moonshot (P2) and judge (P4).
- **Tenancy:** manifest read from repo at `head_sha` via GitHub API (P1 adds `fetch_repository_file_at_sha`).
- **i18n:** backend-only.
- **Validation:** staging metrics script; P5 requires **deliberate dogfood PR** after deploy (`--since` window; post-#58 = 0 runs today).

---

## P0 — Foundations: SSOT schema, caps, metrics migration

**Goal:** Primitives every later phase depends on — manifest contract, config caps (512 KB default), `context_stats` column, retrieve-manifest key contract (empty until P2).

**Scope — in:** Alembic **`0029_review_context_stats`** — nullable `context_stats JSONB` on `github_review_runs`; config `revy_diff_max_bytes` (default **524288**), `revy_engineering_context_max_bytes`, `revy_pr_body_max_bytes`; SSOT schema `.greptile/review-context.json` + typed parser in `engineering_context`; retrieve manifest + `context_stats` **field contract** documented in code; CI path-exists on SSOT paths; staging script reads `context_stats` when present.

**Scope — out:** GitHub file fetch; inject; Greptile `files.json` generation; judge.

**Deliverables:** Migration; settings + tests (behavior unchanged until P2); SSOT + path-exists validation; manifest key stubs in `build_retrieval_manifest`.

**Depends on:** `main` at `0028`.

---

## P1 — Extractor, loader, GitHub file at SHA

**Goal:** Resolve pointed `.md` at `head_sha`; extract bounded locks + smoke.

**Scope — in:** `fetch_repository_file_at_sha` in `github_api.py` (Contents API or git blob — align rate limits with `compare_commits`); load SSOT from repo; scope filter vs `changed_files`; tolerant parse of `## Locked decisions` (+ dated suffixes) and smoke tables; byte-budget truncate; fixtures from `JUDGE_JSON_CONTRACT_FINDINGS.md`, RCX findings, one execution MD.

**Scope — out:** Prompt assembly; Greptile generation.

**Deliverables:** `EngineeringContextPack` (`active_program`, `lock_ids`, `extracted_text`, `source_paths`); loader errors for trace.

**Depends on:** P0.

---

## P2 — Moonshot inject & instrumentation populate

**Goal:** `prepare_review_context` prepends engineering block; dedupe per RCX-D12; populate manifest + `context_stats`.

**Scope — in:** RCX-D8 in `github_review.py`; review instruction treats block as authoritative; dedupe table (locks always, body skip when in diff and not omitted); populate retrieve engineering fields + `context_stats`; use `revy_diff_max_bytes` from config.

**Scope — out:** Greptile trim; judge.

**Deliverables:** Moonshot inject on scoped PRs; trace fields populated; unit tests inject order + dedupe + truncation fallback.

**Depends on:** P1.

**Note:** With P0 default 512 KB, omitted-`.md` rate should drop vs 128 KB baseline before P3 Greptile trim.

---

## P3 — Active program trim & Greptile sync

**Goal:** One SSOT edit → Revy + Greptile; generated `files.json` only.

**Scope — in:** Generate `.greptile/files.json` from SSOT (exactly 3 RCX entries; no workflow refs); replace legacy 15-entry file; generator `--check` in pytest; phase-execution skill note.

**Scope — out:** `BUGBOT.md` generator; nested `.greptile/` (RC3).

**Deliverables:** Greptile loads 3 RCX docs on `backend/**`; `files.json` never hand-edited after P3.

**Depends on:** P2.

---

## P4 — Judge context reuse

**Goal:** Judge shares P1 lock extract on escalation runs.

**Scope — in:** Re-fetch `build_engineering_context_pack` in judge path via `compare_commits` for changed/omitted files; lock block max 2048 chars; optional `lock_ids_cited` on judge manifest.

**Scope — out:** Moonshot changes; judge parse contract.

**Deliverables:** Judge prompts include lock IDs on program PRs; no judge-json-contract regression.

**Depends on:** P2.

---

## P5 — Staging validation & closeout

**Goal:** Human gate after **dogfood PR** on staging.

**Scope — in:** Metrics `--since` post-RCX deploy; fill validation tables; **sign-off requires P2–P4** (Moonshot inject + cap + Greptile trim + judge locks); manual contradict-locks check; program README + recovery checklist Track M; **P5.5** Greptile-shaped PR issue comment (RQ7 G3+ narrative parity).

**Scope — out:** RC4 DB spike; disposition helpers (RCX-G7).

**Deliverables:** Filled validation memo; operator sign-off; richer revybot issue comment before dogfood sign-off.

**Depends on:** P3–P4 on staging + at least one program dogfood PR.

### P5.5 — Greptile-shaped issue comment (subphase)

**Goal:** revybot PR issue comment matches Greptile triage depth — narrative paragraph, confidence **rationale**, files needing attention, findings table, optional `<details>` for security + important files (no mermaid).

**Why now:** PR #60 showed revybot summary is thin because `ISSUE_COMMENT_FORMAT_SYSTEM_PROMPT` asks for a **short narrative**; dogfood PR triage should read like Greptile before operator sign-off.

**Scope — in:** `moonshot_review.ISSUE_COMMENT_FORMAT_SYSTEM_PROMPT`; `build_pr_review_comment_fallback` + `build_pr_review_comment` user prompt in `github_publish_formatter.py`; pytest in `test_github_publish_formatter.py`.

**Scope — out:** Check-run body (stays compact G3); mermaid sequence diagrams.

**Deliverables:** Issue comment sections aligned with Greptile Summary shape on next staging dogfood push.

**Execution:** [waves/REVIEW_ENGINEERING_CONTEXT_P5_EXECUTION.md](./waves/REVIEW_ENGINEERING_CONTEXT_P5_EXECUTION.md) § P5.5.

---

## Open calibration

None — cap default **512 KB** locked from staging baseline (25% truncated at 128 KB).

**Next step:** **`phase-execution`** complete for code — operator human gate: [REVIEW_ENGINEERING_CONTEXT_STAGING_VALIDATION.md](./REVIEW_ENGINEERING_CONTEXT_STAGING_VALIDATION.md).
