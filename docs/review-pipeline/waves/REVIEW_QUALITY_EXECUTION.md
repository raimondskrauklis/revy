# Review quality — execution (single PR)

**Branch:** merged to `main` (PR #50) · **Active:** RQ9 hardening on `docs/agent-work` · **Tag:** `review-quality-v1` after human gate (AS2 + staging `0026` + RQ9)

**Baseline:** [REVIEW_QUALITY_FINDINGS.md](../review-quality/REVIEW_QUALITY_FINDINGS.md) · **Architecture peer review:** [REVIEW_QUALITY_PEER_REVIEW.md](../review-quality/REVIEW_QUALITY_PEER_REVIEW.md) · **Execution peer review:** § below · **General plans:** [index](../review-quality/REVIEW_QUALITY_GENERAL_PLAN.md).

**Goal:** Ship diff-first review (D13), pipeline trace (O), incremental index (C1), Greptile publish (G), evidence judge (E), resolution metrics (M) in **one PR** — one migration chain, one LOOP.

## Decisions locked for execution

- **S1:** One PR / one migration `0026` — no per-slice branches.
- **AS1 / index timing:** `index_mode` set on **`GitHubIndexJobORM` at job create** — not from review profile inside `run_index_job` (review does not exist yet). `autostart` / `command` → `diff`. `manual` admin index → `full` default; optional `IndexTriggerRequest.mode` for `full` \| `diff`. Admin `POST …/review` with `deep`/`critical` → enqueue **new** index job with `index_mode=full` before review (or reject if index job `index_mode` mismatch).
- **D5:** 128KB unified diff cap; `truncated=true` + `omitted_files[]` in retrieval manifest when capped.
- **D6:** ≤15 supplemental chunks (diff); ≤30 (full).
- **D7:** Exclude `**/tests/**` from supplemental RAG unless PR touches tests.
- **D10:** `sha256(workspace_id + pull_request_id + file_path + category + title + start_line_key)`; message excluded; **D10-M:** no backfill.
- **D13-F:** Compare fallback → `full` + `fallback_reason` column **and** manifest **and** publish footer/check warning.
- **O2 / O6:** Raw LLM I/O and prompts live in **`github_pipeline_artifacts` only** — no `raw_response` on `github_review_runs`. Prompt artifacts use chunk refs where possible (O6).
- **M2:** `resolution_status` = `addressed` \| `still_open` \| `judge_dismissed` only — no human dismiss (R7.6 defer).
- **G3:** Compact check run body; full Greptile narrative in issue comment only.
- **G2 vs R6-Q2:** `compute_check_conclusion` stays severity-derived; confidence 0–5 comment-only.
- **O4-v1:** 90d global retention (`PIPELINE_RETENTION_DAYS`); no workspace override column in v1.
- **O8:** `workers/pipeline_purge_tasks.py` on **maintenance** queue + **single** `beat_schedule` entry in `celery_app.py` (daily purge). Do not use nonexistent `maintenance_tasks.py`.
- **O9:** Pipeline read API — `items_view`; admin bulk export **out of scope** v1.
- **Pipeline GET route (locked):** `GET /{workspace_id}/repositories/{repository_id}/pull-requests/{pull_request_id}/revisions/{revision_id}/review-runs/{review_run_id}/pipeline` — matches `installation_review.py` revision-scoped pattern (no `installations/` segment).
- **SC3:** Manifest fields `changed_symbols`, `structural_context_mode`, `caller_files_*` — default `structural_context_mode=none`. **v1 stub:** `changed_symbols=[]`, caller fields empty; real population → **RQ-STRUCT-1**.
- **AS1 default vs create:** ORM/migration `server_default=full` for backfill; pipeline jobs set `index_mode=diff` explicitly at create (`review_pipeline.py`).
- **G5 formatter LLM:** `services/github_publish_formatter.py` calling existing Moonshot client (`integrations/moonshot_review.py` pattern) — structured JSON in/out; no new vendor.
- **G10:** GitHub check run **`in_progress` at pipeline start** (RQ3) → **`completed` at publish** (RQ7). Parity with Greptile/Bugbot PR check UX — today `create_check_run` posts only `completed` in one shot.
- **PR review context (dogfood):** Ship `.revy/review-context.json` (SSOT) + generated `.greptile/files.json` + `.cursor/BUGBOT.md` in **RQ0** (first commit). Set `active_program`; three doc paths per program; run `test_generate_greptile_files.py` + generator `--check`. Per-phase commits: code + minimal doc status (execution table row) — not full doc tree every push.

## PR review context (Greptile + Bugbot + Moonshot)

Changed `.md` files are in the PR diff, but bots and Moonshot do **not** treat planning docs as authoritative unless wired:

| Consumer | Mechanism | Ship in RQ0 |
|------|-----------|-------------|
| **Moonshot inject** | `.revy/review-context.json` — `active_program` + `programs[]` | SSOT — edit first |
| **Greptile** | `.greptile/files.json` — **generated** from SSOT (`generate_greptile_files_from_review_context`) | execution + findings + general plan |
| **Bugbot** | `.cursor/BUGBOT.md` — markdown links to same docs | execution + findings + orchestration (RQ9) |

**Gate:** `cd backend && python -m scripts.generate_greptile_files_from_review_context --check && pipenv run pytest tests/unit/test_generate_greptile_files.py -q`

**Never hand-edit `files.json` after RCX P3.** See `phase-execution` skill § PR review context.

**Per-phase commit pattern:** RQn code + update `waves/README.md` / execution status for that slice only. Avoid re-touching all peer-review/findings files each push (Bugbot context budget).

**Strategy (post-v1 improvements):** [REVIEW_QUALITY_REVIEW_CONTEXT.md](../review-quality/REVIEW_QUALITY_REVIEW_CONTEXT.md) — RQ-RC-1 track after tag.

**Not** general `.cursor/rules/` — those are IDE-agent only; Bugbot does not read them.

## Out of scope (this execution)

- Human dismiss/ack UI → **R7.6**
- Workspace retention override / admin export API → **v1.1**
- Full LSP / reference graph → [STRUCTURAL_CONTEXT](../review-quality/REVIEW_QUALITY_STRUCTURAL_CONTEXT.md)
- Reviewer UI pipeline tab
- Multi-agent generators (Track A)
- Mermaid in publish
- Langfuse / OTel
- **RQ-RC-1** — scoped review context (RC1–RC3) → [REVIEW_CONTEXT](../review-quality/REVIEW_QUALITY_REVIEW_CONTEXT.md)

## LOOP order

**Shipped:** `RQ0` → … → `RQ8` (PR #50).

**Active:** `RQ9` — post-merge hardening ([general plan](../review-quality/REVIEW_QUALITY_R9_HARDENING_GENERAL_PLAN.md)).

**Hard gates:** RQ6 before RQ7 (resolution before G9 prose). RQ2 before RQ5 (diff before evidence hunk). **O2 raw capture** ships in **RQ3** (not RQ2). **RQ9** before human gate tag if G10 parking items matter for AS2.

---

## RQ0 — Schema migration

**What:** Hand-written Alembic `0026_review_quality.py` — single revision:

| Object | Columns / notes |
|--------|-----------------|
| `github_pull_request_revisions` | `base_sha` VARCHAR nullable (D8) |
| `github_index_jobs` | `index_mode` (`diff` \| `full`); **`server_default=full`** (backfill); pipeline jobs set `diff` at create (AS1); `fallback_reason` TEXT nullable; `warning_message` TEXT nullable (D3); `index_incremental` BOOL default true (I3) |
| `github_pipeline_runs` | `workspace_id` FK → `workspaces` **ON DELETE CASCADE**; `revision_id` ON DELETE CASCADE; `head_sha`, `index_mode`; nullable FKs: `index_job_id`, `review_run_id`, `publish_job_id` — all **ON DELETE SET NULL**; indexes: `workspace_id`, `revision_id`, `created_at` (O8 purge), **`index_job_id`**, **`review_run_id`**, `(workspace_id, revision_id)` |
| `github_pipeline_steps` | `pipeline_run_id` ON DELETE CASCADE; `step_type`, `status`, `duration_ms`, `model_provider`, `model_id`, `input_tokens`, `output_tokens`, `error` |
| `github_pipeline_artifacts` | `step_id` ON DELETE CASCADE; `kind`, `content_text`, `content_json`, `content_hash`; **CHECK** `content_text IS NOT NULL OR content_json IS NOT NULL` |
| `github_code_chunks` | `content_hash` VARCHAR(64) nullable |
| `github_findings` | `evidence_snippet` TEXT nullable |
| `github_finding_groups` | `resolution_status` VARCHAR nullable; **D10-M:** migration `UPDATE … SET state='superseded' WHERE state='active'` (no fingerprint backfill) |
| `github_publish_jobs` | `summary_json` JSONB nullable |

Enums in `constants/enums.py`: `GitHubIndexMode`, `PipelineStepType`, `PipelineArtifactKind`, `ResolutionStatus` (or string columns per existing pattern).

**Review context (dogfood — same commit as migration):**

1. **`.greptile/files.json`** — scope `backend/**`:
   - `docs/review-pipeline/waves/REVIEW_QUALITY_EXECUTION.md` (active contract)
   - `docs/review-pipeline/review-quality/REVIEW_QUALITY_FINDINGS.md` (locked Q#)
2. **`.cursor/BUGBOT.md`** — links to the same two files (relative paths from `.cursor/`).

**Files:** `alembic/versions/2026_07_27_*_0026_review_quality.py`, `models/github_pipeline_*.py`, `models/github_index_job.py`, `models/github_pull_request.py`, `models/github_code_chunk.py`, `models/github_finding.py`, `models/github_finding_group.py`, `models/github_publish_job.py`, `constants/enums.py`, `.greptile/files.json`, `.cursor/BUGBOT.md`, `tests/unit/test_review_quality_models.py` (new — import ORM + enum round-trip)

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_review_quality_models.py -q
```

**LOOP pause:** hand-written Alembic revision — agent stops after commit until human runs migration on staging.

---

## RQ1 — Compare API + base_sha + diff index (D8, D9, D13, AS1)

**What:**

1. **`github_api.compare_commits`** — `GET /repos/{owner}/{repo}/compare/{base}...{head}`; changed files + patches; typed errors for 404/rate-limit.
2. **`_extract_pr_fields`** — persist `base_sha` from `pull_request.base.sha` on revision rows (D8).
3. **`index_mode` at job create** (AS1) — in `maybe_enqueue_pipeline_for_revision`: `autostart` / `command` → `index_mode=diff`. In `create_index_job` (admin manual): default `index_mode=full`; accept optional `IndexTriggerRequest.mode` (`diff` \| `full`).
4. **`run_index_job`** — read `job.index_mode` only; never review profile. On compare failure: set `index_mode=full`, `fallback_reason` on job row. **`_fail_index_job_after_chunk_work`:** preserve `index_mode` + `fallback_reason` across `session.rollback()` (reapply after `session.get`) — tarball failure must not lose D13-F diagnostics.
5. **D13 hybrid index** — compare → `changed_files`; tarball at `head_sha` → chunk/embed changed paths only; index step manifest via pipeline (RQ3) — no extra JSON column on job.
6. **D3 job warning** — when `index_mode=full`, set `warning_message` on job row (file count; p50 duration if history exists). GitHub footer for D3/D13-F in **RQ7**.
7. **AS1 deep/critical admin review** — in `post_review_pull_request_revision` (`installation_review.py`): if `body.profile` is `deep`/`critical`, require completed index job with `index_mode=full` or enqueue new full index job before `create_review_run`; reject `409` on mismatch. Mirror guard in `create_review_run` if needed.

**Files:** `integrations/github_api.py`, `services/github_pull_requests.py`, `services/github_indexing.py`, `services/github_review.py` (`create_review_run` index_mode guard), `services/review_pipeline.py`, `api/v1/workspaces/installation_review.py`, `api/v1/workspaces/installation_indexing.py` (optional `mode` on POST body), `schemas/github_indexing.py`, `models/github_index_job.py`, `tests/unit/test_github_api.py`, `tests/unit/test_github_indexing.py`, `tests/unit/test_github_pull_requests.py`, `tests/unit/test_review_pipeline.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest \
  tests/unit/test_github_api.py \
  tests/unit/test_github_indexing.py \
  tests/unit/test_github_pull_requests.py \
  tests/unit/test_review_pipeline.py -q
```

---

## RQ2 — Diff-first review + retrieval + fingerprint (D, D7, D10, SC3)

**What:**

1. **Context pack** — rewrite `_build_review_prompt`: metadata + body (4KB D12) → changed files → unified diff (128KB D5) → supplemental chunks (D6); diff-first system instruction.
2. **Compare for review** — re-call `compare_commits(revision.base_sha, revision.head_sha)` in review worker (same helper as index); do not depend on index job row for patches. After RQ3, index step artifact may duplicate for trace only.
3. **D5 truncate** — when diff capped: `truncated=true`, `omitted_files[]` in retrieval manifest JSON (passed to trace in RQ3).
4. **Scoped retrieval** — lenses on `changed_files` chunks; D7 test exclusion; manifest fields per findings O3 + SC3 (**v1 stub:** `changed_symbols=[]`, `structural_context_mode=none`).
5. **D10 fingerprint** — `compute_fingerprint` per peer-review formula; `start_line_key` from latest finding at reconcile.
6. **`parse_report` dict** — extend `_parse_finding_row` to return drop reasons/counts for pipeline `parse_report` artifact (**persisted in RQ3**). **No** `raw_response` on `github_review_runs` (O2).

**Files:** `services/github_review.py`, `services/github_finding_reconcile.py`, `tests/unit/test_github_review.py`, `tests/unit/test_github_finding_reconcile.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest \
  tests/unit/test_github_review.py \
  tests/unit/test_github_finding_reconcile.py -q
```

---

## RQ3 — Pipeline trace + read API + purge (O)

**What:**

1. **`services/github_pipeline_trace.py`** — `github_pipeline_runs` links `index_job_id`, `review_run_id`, `publish_job_id`, `revision_id`, `head_sha`, `index_mode`; steps + artifacts per findings § storage model.
2. **Wire capture** — hook all worker entrypoints:
   - `workers/index_tasks.py`
   - `workers/review_tasks.py`
   - `workers/reconcile_tasks.py` + `services/github_finding_reconcile.py`
   - `workers/judge_tasks.py` / judge path in reconcile
   - `workers/publish_tasks.py`
   - Persist **review** `prompt`, `raw_response` (always), `parse_report`, retrieval `manifest` (O2, O6 chunk refs).
   - Record **`retrieve`** as its own `step_type` before `review` (even though logic lives in `github_review.py`).
3. **GET pipeline** — `installation_review.py`:

   `GET /{workspace_id}/repositories/{repository_id}/pull-requests/{pull_request_id}/revisions/{revision_id}/review-runs/{review_run_id}/pipeline`

   `items_view`; `ensure_revision_access`; return steps + artifacts.

4. **O8 purge** — `workers/pipeline_purge_tasks.py` → maintenance queue; register in `celery_app.py` imports + routes; `beat_schedule` daily `purge_old_pipeline_artifacts`; `PIPELINE_RETENTION_DAYS=90` in `config.py` / `.env.example`.
5. **G10 check lifecycle** — on pipeline enqueue / first worker start: `create_check_run` with `status=in_progress` (store `github_check_run_id` on publish job or pipeline run). **TX split (RQ3):** `index_tasks` opens check in **first** `get_db_context()` session, runs `run_index_job` in **second** — check survives index rollback. Publish path uses `update_check_run` → `completed` + conclusion (RQ7). On pipeline failure: `completed` + `failure`/`neutral` — never leave orphan `in_progress`. **Draft/closed benign skip** → `neutral` finalize (**RQ9**).
6. **Schemas** — `PipelineRunResponse`, `PipelineStepResponse`, `PipelineArtifactResponse`.

**Files:** `services/github_pipeline_trace.py`, `schemas/github_pipeline.py`, `api/v1/workspaces/installation_review.py`, `integrations/github_api.py`, `workers/index_tasks.py`, `workers/review_tasks.py`, `workers/reconcile_tasks.py`, `workers/publish_tasks.py`, `services/github_finding_reconcile.py`, `services/github_finding_judge.py`, `workers/pipeline_purge_tasks.py`, `workers/celery_app.py`, `core/config.py`, `tests/unit/test_github_pipeline_trace.py`, `tests/unit/test_github_pipeline_routes.py`, `tests/unit/test_pipeline_purge_tasks.py`, `tests/unit/test_github_api_publish.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest \
  tests/unit/test_github_pipeline_trace.py \
  tests/unit/test_github_pipeline_routes.py \
  tests/unit/test_pipeline_purge_tasks.py -q
```

---

## RQ4 — Incremental copy-forward (C1, I)

**What:**

1. **`content_hash`** on chunk insert.
2. **`job.index_incremental`** — when false, skip copy-forward (full re-embed). Default true on pipeline jobs (I3).
3. **Parent revision** — prior row on same PR; **first push** = no-op copy-forward.
4. **Copy-forward** + delta embed + delete removed paths vs parent file set.
5. **Manifest** — `reused_count`, `new_count`, `embed_batches` via pipeline index step (RQ3).

**Files:** `services/github_indexing.py`, `tests/unit/test_github_indexing.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_indexing.py -q -k "incremental or copy_forward or content_hash"
```

---

## RQ5 — Evidence + grounding judge (E)

**What:**

1. **`evidence_snippet`** at parse from diff hunk or top retrieval chunk.
2. **`_build_judge_prompt`** — snippet + grounding instruction (E2).
3. **Judge dismissed** → existing `resolved` group state.
4. **Pipeline** — judge artifacts per candidate (RQ3 hooks).

**Files:** `services/github_review.py`, `services/github_finding_judge.py`, `tests/unit/test_github_review.py`, `tests/unit/test_github_finding_judge.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest \
  tests/unit/test_github_review.py \
  tests/unit/test_github_finding_judge.py -q
```

---

## RQ6 — Resolution metrics (M2)

**What:**

1. **`resolution_status`** on prior revision’s active groups when new revision created on `synchronize`:
   - `judge_dismissed` if `state=resolved`
   - `addressed` if compare diff touches `file_path` + line region (latest finding lines)
   - else `still_open`
2. **Hook** — `apply_resolution_status_for_synchronize` in `github_pull_requests.py` on `synchronize` action after new revision flush (inside webhook handler, before worker enqueues pipeline via `maybe_enqueue_pipeline_for_revision`). Requires compare from RQ1.
3. **G9 input** — counts from `resolution_status`; G8 `summary_json` prior delta is **RQ7** concern (load prior publish job for same PR).

**Files:** `services/github_resolution_metrics.py`, `services/github_pull_requests.py`, `tests/unit/test_github_resolution_metrics.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_resolution_metrics.py -q
```

---

## RQ7 — Greptile publish (G, G3, G9, D13-F, D3)

**What:**

1. **`services/github_publish_formatter.py`** — `build_pr_review_comment()` via Moonshot (`integrations/moonshot_review.py` pattern); Greptile sections; fallback to `build_summary_markdown`.
2. **G3** — `build_check_run_summary()` compact; full narrative on issue comment only.
3. **G2** — deterministic confidence 0–5 in comment; **not** in check `conclusion`.
4. **G9** — fixed-since-last-push from `resolution_status` (RQ6).
5. **G8** — `summary_json` on publish job.
6. **D13-F + D3** — footer/check warning for `fallback_reason` and intentional `index_mode=full` (deep/critical).
7. **G6/G7** — assert no regression: inline remains error/critical only; summary table without message column.
8. **G10 finalize** — publish uses `update_check_run` (not one-shot `create` with `completed`); compact G3 body on finalize.
9. **Pipeline** — publish artifacts for both markdown bodies.

**Files:** `services/github_publish.py`, `services/github_publish_formatter.py`, `integrations/moonshot_review.py` (extend if needed), `tests/unit/test_github_publish.py`, `tests/unit/test_github_publish_formatter.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest \
  tests/unit/test_github_publish.py \
  tests/unit/test_github_publish_formatter.py -q
```

---

## RQ8 — Doc sync + staging gates

**What:**

1. Update docs (table below).
2. `backend/.env.example` — `PIPELINE_RETENTION_DAYS=90`.
3. Deploy note: Celery **beat** process must run for O8 purge (first `beat_schedule` in repo).

| Doc | Change |
|-----|--------|
| [review-quality/README.md](../review-quality/README.md) | Execution Done + tag `review-quality-v1` |
| [waves/README.md](./README.md) | Review-quality row → done; RQ9 active |
| [REVIEW_PIPELINE_STAGING_SMOKE_VALIDATION.md](../REVIEW_PIPELINE_STAGING_SMOKE_VALIDATION.md) | AS2 autostart + diff replay + D10 + pipeline GET gates; § post–review-quality re-smoke |
| [REVIEW_PIPELINE_RECOVERY_CHECKLIST.md](../REVIEW_PIPELINE_RECOVERY_CHECKLIST.md) | Active track → post review-quality; migration `0026`; Track I RQ9 |
| [REVIEW_PIPELINE_PRODUCT_PATTERNS.md](../REVIEW_PIPELINE_PRODUCT_PATTERNS.md) | Precision metrics → review-quality M2 if shipped |
| [REVIEW_QUALITY_REVIEW_CONTEXT.md](../review-quality/REVIEW_QUALITY_REVIEW_CONTEXT.md) | RC0 done; dogfood metrics → RQ-RC-1 backlog |
| [agents/ORCHESTRATION.md](../agents/ORCHESTRATION.md) | Master/reviewer model; FIND/VALIDATE/CLOSE verbs |
| [agents/PROMPTS.md](../agents/PROMPTS.md) | Distilled prompt index |
| [agents/prompts/ROLES.md](../agents/prompts/ROLES.md) | Role boundaries + verb table |
| [CURSOR_AGENT_WORKFLOW.md](../../utils/CURSOR_AGENT_WORKFLOW.md) | Quick ref — attach first in new chats |
| `.cursor/BUGBOT.md` | Merged status; human gate; links quick ref + RQ9 |
| `backend/.env.example` | `PIPELINE_RETENTION_DAYS` |

**Deliverable:**

```bash
cd backend && pipenv run lint && pipenv run pytest tests/unit/ -q
```

**Human gate (S4 + AS2):**

1. Staging/prod: `alembic upgrade head` through **`0026`**.
2. Redeploy workers **and Celery beat** (`pipeline_purge_tasks` daily schedule).
3. Autostart toggle ON → open or sync PR → confirm index job `index_mode=diff`.
4. Smoke [#44](https://github.com/raimondskrauklis/revy/pull/44) diff replay (or equivalent tiny diff PR).
5. D10: no duplicate active groups on re-push; deletion-only sync → `resolution_status` (RQ6).
6. G3: compact check body; full Greptile narrative in issue comment only.
7. Pipeline GET returns steps + artifacts for completed run.
8. D13-F: optional fault test — compare fallback `fallback_reason` visible in publish footer after index failure path.
9. G10: check shows `in_progress` during run; open PR → draft/closed before review → `neutral` (RQ9).

**Optional:** `post-finish-gap-pass` after human gate.

---

## RQ9 — Post-merge hardening

**What:** Close corners cut in RQ0–RQ8 without new migration. Baseline: [REVIEW_QUALITY_R9_HARDENING_GENERAL_PLAN.md](../review-quality/REVIEW_QUALITY_R9_HARDENING_GENERAL_PLAN.md).

1. **G10 neutral finalize** — when `prepare_review_after_index` skips review for draft/closed PR, finalize check `completed` + `neutral` (not orphan `in_progress`, not `failure`).
2. **`ReviewAfterIndexOutcome`** — add `neutral_finalize_check` + summary; wire in `index_tasks.py`.
3. **`finalize_pipeline_github_check_neutral`** — `github_pipeline_trace.py` (reuse `update_check_run` with `conclusion=neutral`).
4. **G10 TX split test** — `test_index_tasks.py`: assert **two** `get_db_context` sessions for autostart pipeline; index failure still calls `finalize_pipeline_github_check_failure` with stashed check id.
5. **Review context wiring** — expand `.greptile/files.json` + `.cursor/BUGBOT.md`:
   - `docs/utils/CURSOR_AGENT_WORKFLOW.md`
   - `docs/review-pipeline/agents/prompts/ROLES.md`
6. **Doc fidelity** — this execution file gap fixes (RQ0 schema, RQ1 rollback, RQ6 hook); staging smoke § post–review-quality; recovery Track I.

**Files:** `services/review_pipeline.py`, `services/github_pipeline_trace.py`, `workers/index_tasks.py`, `tests/unit/test_index_tasks.py`, `tests/unit/test_review_pipeline.py`, `.greptile/files.json`, `.cursor/BUGBOT.md`, docs per §6.

**Deliverable:**

```bash
cd backend && pipenv run pytest \
  tests/unit/test_index_tasks.py \
  tests/unit/test_review_pipeline.py \
  tests/unit/test_github_pipeline_trace.py -q
```

**Human gate addition:** open PR autostart → index completes → convert to draft (or close) before review enqueue → check `neutral` (not stuck spinner). *Not* draft-at-open — autostart skips draft PRs at enqueue.

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint && pipenv run pytest \
  tests/unit/test_review_quality_models.py \
  tests/unit/test_github_api.py \
  tests/unit/test_github_indexing.py \
  tests/unit/test_github_pull_requests.py \
  tests/unit/test_github_review.py \
  tests/unit/test_github_finding_reconcile.py \
  tests/unit/test_github_pipeline_trace.py \
  tests/unit/test_github_pipeline_routes.py \
  tests/unit/test_pipeline_purge_tasks.py \
  tests/unit/test_github_finding_judge.py \
  tests/unit/test_github_resolution_metrics.py \
  tests/unit/test_github_publish.py \
  tests/unit/test_github_publish_formatter.py \
  tests/unit/test_review_pipeline.py \
  tests/unit/test_github_tasks_autostart.py -q
```

**Deploy:** Single PR → `main`; tag `review-quality-v1` after human gate (+ RQ9 if not merged separately).

**Next:** RQ9 hardening on `docs/agent-work` → human gate AS2 + staging `0026` → tag `review-quality-v1`.

---

## Execution peer review

**Pass 1 (2026-07-27):** critical/high incorporated. **Pass 2 (2026-07-27):** medium/low doc fixes below. **Pass 3 (2026-07-27):** post-merge gap pass → RQ9 phase + execution fidelity updates. **Verdict:** RQ0–RQ8 **shipped** (PR #50); RQ9 active before human gate.

| # | Topic | Resolution |
|---|--------|------------|
| 1 | `index_mode` from review profile in `run_index_job` | Set at job create (AS1) |
| 2 | Wrong `installations/…` pipeline path | Revision-scoped `installation_review.py` route |
| 3 | Raw LLM on `review_run` vs pipeline | O2 pipeline artifacts only; RQ3 wires capture |
| 4 | RQ0 incomplete schema | FKs + `fallback_reason` + `index_incremental` + `warning_message` |
| 5 | Worker hooks missing | All task modules in RQ3 |
| 6 | O8 fork | `pipeline_purge_tasks.py` + `beat_schedule` (not `maintenance_tasks.py`) |
| 7 | I3 missing from RQ4 | `index_incremental` flag |
| 8 | RQ6 hook location | After revision create, before pipeline enqueue |
| 9 | G5 LLM module | `github_publish_formatter.py` + Moonshot pattern |
| 10 | `test_migrations.py` missing | `test_review_quality_models.py` |
| 11 | `warning_message` not in RQ0 | Added to `github_index_jobs` (pass 2) |
| 12 | AS1 deep/critical admin path | `installation_review.py` + `create_review_run` in RQ1 |
| 13 | Compare handoff RQ1→RQ2 | Re-call `compare_commits` in review (pass 2) |
| 14 | RQ8 doc table vague | Restored explicit doc list (pass 2) |
| 15 | Celery beat for O8 | Human gate + RQ8 deploy note (pass 2) |
| 16 | `retrieve` step_type | Explicit in RQ3 (pass 2) |
| 17 | Workspace delete cascade | `pipeline_runs.workspace_id` ON DELETE CASCADE (pass 2) |
| 18 | PR review context wiring | `.greptile/files.json` + `.cursor/BUGBOT.md` in RQ0 (pass 2) |
| 19 | RQ0 schema incomplete post-ship | Indexes on `index_job_id`/`review_run_id`; FK ondelete; artifact CHECK; D10-M supersede (pass 3) |
| 20 | Compare fallback lost on rollback | Preserve in `_fail_index_job_after_chunk_work` (pass 3) |
| 21 | G10 draft/closed orphan check | RQ9 `neutral` finalize (pass 3) |
| 22 | G10 TX split undertested | RQ9 unit test for split `get_db_context` (pass 3) |
| 23 | Greptile scope missing agent docs | RQ9 wiring for `CURSOR_AGENT_WORKFLOW` + `ROLES` (pass 3) |

**Blocking questions — answered:**

1. **Pipeline route:** `…/revisions/{revision_id}/review-runs/{review_run_id}/pipeline`.
2. **O8:** `pipeline_purge_tasks.py` on maintenance queue + `beat_schedule` in `celery_app.py`.
