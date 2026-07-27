# Review quality — findings (post-R8 program)

Baseline for post-R8 work: **diff-first review**, **pipeline explainability**, **Greptile-shaped GitHub publish**, incremental indexing, evidence + grounding, and resolution metrics. **No execution steps.**

**Date:** 2026-07-27 · **Status:** baseline-ready — devil's-advocate pass resolved; **single PR** ship (`feat/review-quality`).

**Program:** [review-quality/README.md](./README.md) · **Parent:** [REVIEW_PIPELINE_FINDINGS.md](../REVIEW_PIPELINE_FINDINGS.md) · **Greptile target:** [REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md](../REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md) · **Staging pain:** [REVIEW_PIPELINE_STAGING_SMOKE_VALIDATION.md](../REVIEW_PIPELINE_STAGING_SMOKE_VALIDATION.md).

**Depends on:** R0–R7 on `main`; R8 merged (`review-r8-v1`); polish wave shipped (suggestion blocks, judge-skipped badge).

---

## Goal

1. **Review the PR diff by default** (Bugbot / Greptile pattern) — not the whole repo haystack.
2. **Capture every pipeline step** (prompts, raw LLM I/O, retrieval manifest) so we can tune Moonshot, judge models (Sonnet 5 today), and index scope systematically.
3. **Publish Greptile-shaped output on GitHub** — primary user surface; Revy `/reviewer` UI unchanged in early slices.

**Parallel, not deleted:** today’s full-repo tarball index (`index_mode=full`) remains for `deep` / explicit opt-in, with cost/time warnings.

**Out of scope (this program):** multi-agent tool loops (Track A defer); sequence/mermaid diagrams; email digest; Greptile vendor config in-repo; **full LSP call graph** (defer v1 — see [REVIEW_QUALITY_STRUCTURAL_CONTEXT.md](./REVIEW_QUALITY_STRUCTURAL_CONTEXT.md)); autonomous merge; Reviewer UI trace **tab** (pipeline **API** yes — see O5).

---

## Shipping model (locked)

| Q# | Decision |
|----|----------|
| **S1** | **One PR** — all tracks D/O/I/G/E/M; general plans R1–R5 are doc slices, not merge order. |
| **S2** | One migration chain; one execution file `waves/REVIEW_QUALITY_EXECUTION.md`. |
| **S3** | Milestone tag after merge: `review-quality-v1` on `main`. |
| **S4** | Phase gate: smoke #44 replay in diff mode + Greptile-shaped comment on dogfood PR + autostart path verified. |

---

## Build principles

- **Diff-first default** — index + review scope centered on PR changed files; full-repo is opt-in with warnings.
- **GitHub = triage + action** — Greptile-shaped PR comment + check run; `/reviewer` secondary until signal is good.
- **See before tune** — ship diff scope **with** observability (Track D + O); no blind prompt tweaks.
- **Single PR** — R1–R5 doc phases are implementation sections; one branch `feat/review-quality`.
- **Iterative review is normal** — summary and confidence update per `head_sha` (Greptile [#35](https://github.com/raimondskrauklis/revy/pull/35)).
- **Generators exploratory; precision downstream** — reconcile + judge + publish filter; do not over-tighten R4 primary prompt.
- **Workspace-tenanted artifacts** — prompts contain customer code; admin API read; retention policy (not infinite by default).
- **Additive** — hand-written Alembic; unit tests; EN+LV only when user-facing strings added.

---

## Terminology

| Term | Meaning |
|------|---------|
| **Index mode** | `diff` (default) — changed files only; `full` — whole repo at `head_sha` (today’s R3) |
| **Context pack** | Structured inputs to the reviewer LLM: PR metadata + unified diff + optional retrieved chunks |
| **Retrieval manifest** | JSON list of chunks selected for review: lens, score, `in_diff`, rank |
| **Pipeline trace** | Per-run record of steps + artifacts (prompt, raw response, manifest) |
| **Publisher formatter** | Post-reconcile step building Greptile-shaped markdown |
| **Confidence score** | Deterministic 0–5 merge-readiness; LLM writes prose only |
| **Evidence snippet** | Code excerpt tied to a finding for judge grounding (Track E) |
| **Chunk copy-forward** | On `synchronize`, unchanged `(file_path, chunk_index, content_hash)` rows copied from parent revision before delta embed |
| **RQ** | Shorthand for review-quality program phase (R1–R5 in docs) — not review-pipeline R0–R8 |
| **Copy-forward** | On `synchronize`, clone unchanged chunk rows from parent `revision_id` before delta embed |

### Autostart (verified)

| Piece | Location | Today |
|-------|----------|-------|
| UI toggle | `ReviewSettingsPage` | `review_autostart_enabled` — “Autostart review on pull request open and update” |
| Backend gate | `review_pipeline.py` | Skips enqueue when toggle off |
| Webhook path | `github_tasks.py` | `opened` / `synchronize` → `trigger=autostart` |
| Dogfood reality | Staging | **`@revy review` works; AS2 = staging e2e gate** (toggle on → `opened`/`synchronize` full pipeline; fix only if gate fails) |

---

## What exists today (verified)

### Index (R3) — full repo, not diff

| Piece | Location | Behavior |
|-------|----------|----------|
| Input | `github_indexing.py` | Tarball at `revision.head_sha`; all indexable files |
| Embedder | `voyage_embeddings.embed_texts` | Raw chunk text batched |
| Stored | `github_code_chunks` | `content` + `embedding` per revision |
| Missing | — | No `index_mode`, no changed-file list, no compare API usage |

### Review (R4) — RAG haystack, not diff

| Piece | Location | Behavior |
|-------|----------|----------|
| Lenses | `github_review.py` `SEARCH_LENSES` | 3 fixed queries × `top_k=10` |
| Cap | `CONTEXT_CHUNK_CAP = 30` | Merged chunk contents in prompt |
| Prompt | `_build_review_prompt` | PR title + chunk bodies — **no unified diff** |
| Stored | `github_findings`, `review_run.model_id` | Raw LLM response **not** stored |
| Parse | `_parse_finding_row` | Drops `style`; no drop audit |

### Judge (R5)

| Piece | Behavior |
|-------|----------|
| Input | Title, severity, category, file, message — **no code snippet** |
| Stored | `judge_outcome`, `judge_notes`, `judge_model_id` — **not** full prompt/response |

### Publish (R6)

| Piece | Behavior |
|-------|----------|
| GitHub | Table-only summary; inline error/critical; update in place per `head_sha` |
| Missing | Greptile narrative, confidence, files needing attention |

### Observability gap

| Stage | Logged today | Needed for tuning |
|-------|--------------|-------------------|
| Index | `chunk_count`, errors | `index_mode`, file manifest, embed batches, duration |
| Retrieve | — | Lens queries, hits + scores, `in_diff` |
| Review | status, error | Full prompt, raw response always, parse drops |
| Judge | per-group errors | Full prompt + raw response + tokens |
| Publish | job status | Summary markdown snapshot |

### Staging smoke (#44) root cause

| Symptom | Cause | Track |
|---------|-------|--------|
| Test-file nits on 1-line PR | Full-repo index + generic RAG lenses | **D** diff-first |
| ~9 min latency | Embed + review whole haystack | **D** + **I** |
| Duplicate table rows | Fingerprint includes full `message` | **D10** reconcile tweak |
| Can’t debug | No stored prompt/response | **O** |

---

## Catalog — tracks

### Track D — Diff-first review (P0)

**Rationale:** Bugbot analyzes the **diff in context of the codebase**; Greptile focuses on changed files + impact. Revy today indexes and retrieves from the **entire repo** — wrong default ([smoke #44](../REVIEW_PIPELINE_STAGING_SMOKE_VALIDATION.md)).

**Industry pattern:** Trigger on PR diff; broaden context only when needed — not embed-everything-first.

#### Index modes (parallel — do not delete `full`)

| Mode | When | What is indexed / embedded |
|------|------|---------------------------|
| **`diff` (default)** | `standard` profile, autostart, `@revy review` | Changed paths only — see **D13** hybrid strategy |
| **`full` (parallel)** | `deep` / `critical` profile, admin `POST …/index?mode=full` | Today’s tarball behavior |

**Profile → index_mode (locked AS1):** `standard` → `diff`; `deep` / `critical` → `full`. No workspace profile picker before ship — autostart and `@revy review` always use `standard` → `diff`.

#### Diff-mode index strategy (locked D13)

**Advice adopted:** hybrid — **compare API for truth**, **tarball for content**, **no extract-all-then-filter**.

| Step | Source | Why |
|------|--------|-----|
| Changed file list + unified diff | `GET …/compare/{base}…{head}` | Authoritative paths + patches; full observability in trace manifest |
| File bytes for chunking | Tarball at `head_sha` | Same extractor/chunker as today; **only paths in `changed_files`** are read from tarball |
| Supplemental RAG | Current revision chunks | Lenses scoped to changed-path chunks (+ D4 radius when >0) |
| Token spend | Diff in prompt is primary | Supplemental cap D6; burn tokens on diff + evidence, not whole-repo embed |

**Not default:** download tarball → extract entire repo → filter — wastes I/O and obscures which files were indexed.

**Compare fallback:** If compare fails → `index_mode=full` for that job; manifest + GitHub footer include `fallback_reason` (visible, not silent).

#### Chunk lineage (locked C1)

Per **revision** (each `head_sha`), chunk set = **copy-forward** + **delta**:

1. On `synchronize`, resolve parent revision (prior `head_sha` on same PR).
2. **Copy-forward** rows where `(file_path, chunk_index, content_hash)` unchanged from parent → new `revision_id`, same embedding.
3. **Delta:** chunk + embed only changed/new paths from compare (tarball bytes at `head_sha`).
4. **Delete** chunks for paths removed from compare vs parent.
5. Retrieval + review always use **current** `revision_id` chunk set (includes inherited + new).

R2 incremental (I) implements C1; diff mode and full mode both use copy-forward on re-push.

#### Changed-file detection

| Piece | Method |
|-------|--------|
| API | `GET /repos/{owner}/{repo}/compare/{base}...{head}` (new in `github_api.py`) |
| `base_sha` | **Primary:** PR webhook `pull_request.base.sha` at revision create (**D8**). Compare validates/refreshes if drift. |
| Fallback | If compare fails → `index_mode=full` + `fallback_reason` in manifest + GitHub footer |

**User warnings (`full` mode):** Before enqueue, estimate file count + prior p50 duration from workspace history; surface in GitHub summary footer and index job metadata: *“Full repository index — ~N files, typically X–Y min. Use diff mode for faster reviews.”*

#### Context pack — user prompt structure (locked v1)

Order matters — model sees **the change first**:

```text
1. PR metadata
   - title, body (truncated), head_sha, base_ref…head_ref
   - index_mode: diff | full

2. Changed files (manifest)
   - path list from compare

3. Unified diff (primary)
   - GitHub compare patch or aggregated file patches
   - Cap: D5 token/char budget; truncate largest files last

4. Supplemental context (optional, bounded)
   - Retrieved chunks ONLY from changed paths (+ D4 context radius)
   - Each block: file_path, chunk_index, score, lens, in_diff flag
   - Cap: D6 chunk count (default ≤15 in diff mode, ≤30 in full)

5. Review instruction footer
   - Existing R4-Q5 actionable-only; focus on introduced/changed logic
```

**System prompt:** Keep `REVIEW_SYSTEM_PROMPT`; add explicit instruction: *“Prioritize issues in the diff hunks below; use supplemental context only to validate cross-file impact.”*

#### Retrieval in diff mode

| Today | Target |
|-------|--------|
| 3 global lenses on all revision chunks | Lenses run **scoped** to changed-file chunks first |
| Merge to 30 chunks anywhere in repo | Fill remaining budget from context-radius files only |
| No diff in prompt | Diff section is mandatory in diff mode |

#### Test / generated file policy (D7 — locked)

**Not CI / pytest** — this is **supplemental RAG retrieval only**. Changed test files always appear in the **unified diff** when the PR touches them.

| Rule | Value |
|------|-------|
| Exclude `**/tests/**` from supplemental retrieval | **Yes** in `standard` unless PR changes tests |
| Always include changed test files in diff section | **Yes** — if in compare, diff shows them |

#### Reconcile tweak (smoke duplicates — locked D10)

| Today | Target |
|-------|--------|
| Fingerprint includes normalized `message` | `sha256(workspace_id + pull_request_id + file_path + category + title + start_line_key)` — message excluded; [D10-M](./REVIEW_QUALITY_PEER_REVIEW.md) |

---

### Track O — Pipeline explainability (P0)

**Rationale:** Flow works; tuning (Moonshot, Sonnet 5 judge, diff scope) requires seeing what was sent and returned. Postgres-first — no mandatory Langfuse; optional later for internal eval.

#### Storage model (v1)

| Table | Purpose |
|-------|---------|
| `github_pipeline_runs` | Links `index_job_id`, `review_run_id`, `publish_job_id`, `revision_id`, `head_sha`, `index_mode` |
| `github_pipeline_steps` | `step_type`, `status`, `duration_ms`, `model_provider`, `model_id`, `input_tokens`, `output_tokens`, `error` |
| `github_pipeline_artifacts` | `step_id`, `kind`, `content_json` or `content_text`, `content_hash` |

**`step_type` values:** `index` · `retrieve` · `review` · `reconcile` · `judge` · `publish`

**`artifact kind` values:** `manifest` · `prompt` · `raw_response` · `parse_report` · `summary_markdown` · `retrieval_hits`

#### Capture rules (locked)

| Step | Always store |
|------|--------------|
| **Review** | Full assembled `prompt` (chunk text by ref where possible); **raw LLM response on success and failure**; `parse_report` (`parsed_count`, `dropped_count`, reasons) |
| **Retrieve** | Manifest: `{chunk_id, file_path, chunk_index, score, lens, in_diff, rank}`; `index_mode`; `changed_files[]` |
| **Judge** | Per candidate: `prompt`, `raw_response`, `outcome`; model_id + token counts |
| **Index** | `manifest`: file paths, chunk_count, embed_batch_count, `index_mode`, duration |
| **Publish** | Final `summary_markdown` body |

**Prompt size:** Store full text up to cap (e.g. 512KB/step); overflow → compress or external blob column — implement in execution.

#### Retention (locked)

| Tier | Policy |
|------|--------|
| **Default** | **90 days** hot in Postgres (global v1 — O4-v1) |
| **Workspace override** | **v1.1** — longer retention config (e.g. 180d) |
| **Eval export** | Curated PR subset export — separate from “keep all traffic forever” |
| **Compliance** | Workspace delete cascades pipeline artifacts |

**Not default:** infinite retention without explicit workspace opt-in.

#### Read surface (locked)

| Surface | v1 |
|---------|-----|
| Revy Reviewer UI trace tab | **No** |
| API `GET …/review-runs/{id}/pipeline` | **Yes** — **`items_view`** on workspace (same PR access as reviewer routes); members tune without SQL |
| Retention config / bulk export | **`admin_users`** only |
| GitHub publish footer | `Revy run {id}` link (optional internal) |
| Raw SQL | Ops/staging only |

#### Retention purge (locked O8)

Celery beat task (or existing maintenance worker): delete `github_pipeline_*` rows older than workspace retention (default 90d). Log purge counts; workspace delete cascades artifacts.

---

### Track G — GitHub publish (Greptile-shaped)

Same PR as D/O/I/E/M. Narrative, confidence 0–5 (deterministic), files needing attention, important files changed (`<details>`), metadata footer, revision-aware delta. **No mermaid.**

**G3 (locked):** **Split bodies** — check run = compact (verdict + confidence + severity table); issue comment = full Greptile narrative. Avoids GitHub check output size limits while keeping rich PR comment.

**G10 (locked):** **Check run lifecycle** — create `revy/review` with `status=in_progress` when pipeline starts (RQ3); `update_check_run` → `completed` at publish (RQ7). Parity with Greptile/Bugbot PR check UX. Today only one-shot `completed` at publish end — [dogfood RC-D1](./REVIEW_QUALITY_REVIEW_CONTEXT.md#dogfood-log-pr-50).

**R3 vs R5 “fixed since last review” (locked G9):** **R5 owns** `resolution_status` on groups at next revision; **R3 reads** it for prose. Fingerprint delta from publish snapshot is secondary signal only.

---

### Track I — Incremental index (efficiency)

**C1 copy-forward** on `synchronize` — hash chunks, re-embed delta only. Makes diff mode fast on every push. Not a substitute for D: incremental full-repo still reviews haystack if `index_mode=full`.

---

### Track E — Evidence + grounding judge

Same PR: `evidence_snippet` on findings; judge checks claim vs snippet. Depends on **review-pipeline R5 reconcile** (fingerprints, groups) — not review-quality R5 metrics.

---

### Track A — Multi-agent (defer)

Parallel category generators, devil’s advocate — after trace + diff-first stable.

---

### Track M — Resolution metrics

Bugbot-style resolution rate at next revision. **v1 (M2):** diff heuristic + judge-dismissed — **not** human dismiss (R7.6 deferred). See [peer review](./REVIEW_QUALITY_PEER_REVIEW.md).

---

## External research — adopt / defer / reject

| Pattern | Adopt | Defer | Reject |
|---------|-------|-------|--------|
| Diff-first review (Bugbot/Greptile) | **D** | — | — |
| Full-repo index with warning | **D** `full` mode | — | Delete R3 tarball path |
| Pipeline trace / prompt store | **O** | Langfuse overlay | — |
| Greptile PR summary | **G** | — | Mermaid |
| Incremental chunk hash | **I** | — | — |
| Evidence + grounding judge | **E** | — | — |
| Multi-agent loops | — | **A** | — |

---

## Data scope & exclusions

| In scope | Excluded |
|----------|----------|
| Open PRs, workspace-tenanted traces | Closed PR backfill |
| Admin pipeline API | Reviewer UI trace tab v1 |
| GitHub as primary output surface | Email digest |

---

## Edge cases

| Case | Handling |
|------|----------|
| Compare API 404 / rate limit | Fallback `index_mode=full` + `fallback_reason` in manifest **and** publish footer (D13-F) |
| Huge PR (500+ files) | Cap diff size; warn in GitHub footer; optional skip autostart |
| Empty diff (merge commit / label-only) | Skip review or minimal pass; confidence 5/5 |
| `full` mode on monorepo | Warning + workspace `max_index_files` |
| Parse OK but zero findings | Still store raw response |
| Judge all calls fail | Store each raw response; existing `judge_status=completed` (polish J5) |
| Prompt > size cap | Truncate supplemental context before review; record `truncated=true` in manifest |

---

## Decisions registry

### Track O — Observability

| Q# | Question | Status | Resolution |
|----|----------|--------|------------|
| **O1** | Store full prompts? | **locked** | **Yes** — workspace-scoped |
| **O2** | Store raw LLM response? | **locked** | **Always** — success + failure |
| **O3** | Retrieval manifest? | **locked** | **Yes** — chunk_id, file_path, score, lens, `in_diff`, rank, `index_mode`, `changed_files` |
| **O4** | Retention | **locked** | **90d global default** v1; workspace override **v1.1** (O4-v1) |
| **O5** | Reviewer UI trace? | **locked** | **No** tab; **`items_view` read API** yes |
| **O6** | Duplicate chunk text in prompt artifact? | **locked** | Prefer chunk refs + assembled prompt; avoid triple-storing |
| **O7** | Judge prompt/response capture? | **locked** | **Yes** per candidate |
| **O8** | Retention purge job? | **locked** | **Yes** — Celery periodic; workspace retention |
| **O9** | Pipeline API auth? | **locked** | Read: `items_view`; retention/export: `admin_users` |

### Track D — Diff-first

| Q# | Question | Status | Resolution |
|----|----------|--------|------------|
| **D1** | Default index mode? | **locked** | **`diff`** for `standard` + autostart + command |
| **D2** | Keep full-repo index? | **locked** | **Yes** — `full` parallel; not deleted |
| **D3** | Warn on `full` mode? | **locked** | **Yes** — file count + typical duration in job + GitHub footer |
| **D4** | Context radius | **locked** | **0** v1 (changed files only); v1.1: +1 hop via import search |
| **D5** | Diff size cap | **locked** | **128KB** unified diff; truncate largest files last |
| **D6** | Supplemental chunk cap | **locked** | **≤15** diff mode; **≤30** full mode |
| **D7** | Exclude tests from retrieval? | **locked** | **Yes** in `standard` unless PR touches `**/tests/**` — **RAG only**, not diff; not CI test runs |
| **D8** | `base_sha` on revision | **locked** | **Yes** — webhook `base.sha` at create; migration |
| **D9** | GitHub compare API | **locked** | **New** `github_api.compare_commits` |
| **D10** | Paraphrase fingerprint | **locked** | `workspace_id` + `pull_request_id` + `file_path` + `category` + `title` + `start_line_key` (message excluded); see [peer review](./REVIEW_QUALITY_PEER_REVIEW.md) D10-M |
| **D10-M** | Fingerprint migration | **locked** | No backfill; next reconcile may regroup open PRs |
| **D13-F** | Compare fallback visibility | **locked** | `fallback_reason` in manifest **and** publish footer/check warning |
| **D11** | Diff + O same release? | **locked** | **Yes** — same PR (S1) |
| **D12** | PR body in prompt? | **locked** | **Yes** — truncated (4KB) |
| **D13** | Diff index strategy? | **locked** | Compare for list+diff; tarball bytes for changed paths only; no extract-all-filter |
| **C1** | Chunk lineage? | **locked** | Copy-forward unchanged chunks; delta embed; per revision_id |

### Autostart

| Q# | Question | Status | Resolution |
|----|----------|--------|------------|
| **AS1** | Profile on autostart/command? | **locked** | **`standard` → `diff`** until workspace profile setting exists |
| **AS2** | Autostart broken on staging? | **locked** | **Staging e2e gate** — verify `opened`/`synchronize` with toggle on; fix code only if gate fails |

### Track G / I / E / M

| Q# | Status | Resolution |
|----|--------|------------|
| G1–G5, G8 | **locked** | Greptile publish; deterministic confidence; no mermaid |
| **G3** | **locked** | Split: compact check run + full issue comment |
| **G6** | **locked** | P2 inline off by default |
| **G7** | **locked** | Message column off in table |
| **G9** | **locked** | R5 metrics owns `resolution_status`; R3 publish reads it |
| **G10** | **locked** | `in_progress` check at pipeline start (RQ3); finalize at publish (RQ7) — Greptile/Bugbot parity |
| I1–I3, C1 | **locked** | content_hash; compare paths; copy-forward incremental |
| E1–E2 | **locked** | evidence_snippet; grounding judge |
| M1 | **locked** | `resolution_status` on groups at next revision; v1 counts only |
| **M2** | Human dismiss in v1? | **locked** | **No** — `addressed` / `still_open` / `judge_dismissed` only; human dismiss → R7.6 |
| A1 | **locked** | Defer R6+ |

### Structural cross-file context (SC)

Full analysis: [REVIEW_QUALITY_STRUCTURAL_CONTEXT.md](./REVIEW_QUALITY_STRUCTURAL_CONTEXT.md).

| Q# | Question | Status | Resolution |
|----|----------|--------|------------|
| **SC1** | Defer full LSP in v1? | **locked** | **Yes** |
| **SC2** | Defer all structural cross-file context? | **locked** | **No** — RQ-STRUCT-1 v1.1 |
| **SC3** | v1 trace instrumentation? | **locked** | `changed_symbols`, `structural_context_*` in manifest |
| **SC4** | v1.1 default path? | **locked** | Path C — hunk expansion + import +1 + caller grep |
| **SC5** | v2 path (graph vs agent)? | **locked** | Data-driven from v1 dogfood traces |
| **SC6** | “Impact beyond diff” in v1 positioning? | **locked** | **No** until RQ-STRUCT-1 green |
| **SC7** | Full LSP sidecar? | **open** | RQ-STRUCT-2 if Path C insufficient |
| **SC8** | North star architecture? | **locked** | **Graph substrate + agent runtime** — Greptile index + Bugbot investigator; [structural context](./REVIEW_QUALITY_STRUCTURAL_CONTEXT.md) |

### PR review context (RC)

Full strategy: [REVIEW_QUALITY_REVIEW_CONTEXT.md](./REVIEW_QUALITY_REVIEW_CONTEXT.md).

| Q# | Question | Status | Resolution |
|----|----------|--------|------------|
| **RC0** | Wire Greptile + Bugbot to execution + findings? | **locked** | **Yes** — RQ0 `.greptile/files.json` + `.cursor/BUGBOT.md` |
| **RC1** | Path-scoped doc subsets? | **open** | **RQ-RC-1** post-v1 if dogfood noisy |
| **RC2** | Active RQ phase pointer in Bugbot? | **open** | **RQ-RC-1** |
| **RC4** | `.revy/rules` workspace policy? | **open** | Post-G product |
| **G10** | `revy/review` in-progress on PR? | **locked** | RQ3 + RQ7 — [dogfood log](./REVIEW_QUALITY_REVIEW_CONTEXT.md#dogfood-log-pr-50) |

---

## Parking lot

| Item | When |
|------|------|
| Langfuse / OTel overlay | Internal dogfood eval |
| `.revy/rules` (BUGBOT.md parallel) | Post-G workspace policy — [RC4](./REVIEW_QUALITY_REVIEW_CONTEXT.md) |
| **RQ-RC-1** — scoped review context, active slice pointer | Post-`review-quality-v1` — [review context](./REVIEW_QUALITY_REVIEW_CONTEXT.md) |
| Claims verifier (PR body vs diff) | Post-G |
| **RQ-STRUCT-1** — grep/import/hunk bridge (no LSP) | **v1.1** — [structural context](./REVIEW_QUALITY_STRUCTURAL_CONTEXT.md) |
| **RQ-STRUCT-2** — graph vs agent fork | After v1 trace metrics |
| Full LSP call graph / symbol sidecar | RQ-STRUCT-2 — SC7 |
| Shuffled-diff voting | Eval only |
| Reviewer UI pipeline tab | After admin API stable |

---

## Devil's advocate — resolved

| Risk | Mitigation | Q# |
|------|------------|-----|
| R4 typo “depends on R5 reconcile” | Means **review-pipeline R5** reconcile job, not RQ R5 metrics | E-deps |
| Chunk lineage undefined | **C1** copy-forward + delta per revision | C1 |
| R1 too large for one slice | **S1** one PR; execution file sections per track | S1 |
| `base_sha` only from compare | **D8** webhook `base.sha` at revision create | D8 |
| D10 deferred → smoke dupes | **D10** in same PR | D10 |
| `deep`/`critical` → `full` unwired | **AS1** profile → index_mode map | AS1 |
| R3 vs R5 “fixed” overlap | **G9** R5 owns status; R3 reads | G9 |
| R8 prerequisite soft | **AS2** autostart fix + e2e verify in PR | AS2 |
| No retention purge | **O8** Celery purge job | O8 |
| Pipeline API admin-only | **O9** `items_view` read | O9 |
| G3 same body size limits | **G3** split check vs comment | G3 |
| Compare fallback silent | `fallback_reason` in manifest + footer | D13 |
| Diff-only misses cross-file bug | D4=0 v1; `full` mode; compare fallback | D4 |
| Prompt storage cost | O4 retention + O8 purge; chunk refs O6 | O4 |
| Diff cap hides huge-file bug | Truncate manifest lists omitted hunks; warn in summary | D5 |
| Cross-file caller misses | RQ-STRUCT-1 v1.1; v1 manifest instrumentation | SC1–SC4 |

---

## Experiment / verification

| Check | Pass |
|-------|------|
| Smoke #44 replay in **diff** mode | Findings reference changed file; no unrelated test haystack |
| Manifest shows `index_mode=diff`, `changed_files` | Matches GitHub compare |
| Stored raw response | Present on success and parse failure |
| Index `full` on 1-line PR | Warning text in job metadata |
| Second `synchronize` (with I) | Embed count << first run |
| Admin API returns pipeline trace | All step types; `items_view` auth |
| Autostart e2e on staging | `opened`/`synchronize` without `@revy review` |
| D10 fingerprint | No paraphrase duplicate rows on smoke #44 replay |
| Greptile comment (G) | Narrative + confidence on dogfood PR |
| Resolution prose (G9) | Second push cites `resolution_status` |

---

## Phasing (doc slices — one PR ship)

| Slice | Tracks | Implementation section |
|-------|--------|------------------------|
| **R1** | **D + O** | Compare, diff index, context pack, pipeline tables, API, purge |
| **R2** | **I + C1** | Copy-forward, content_hash, delta embed |
| **R3** | **G** | Greptile publish; G3 split bodies |
| **R4** | **E** | Evidence + grounding judge |
| **R5** | **M** | Resolution metrics; feeds G9 |
| **R6+** | **A** | Agents defer |

---

## References

| Path | Role |
|------|------|
| `backend/app/services/github_review.py` | Lenses, prompt build, no diff today |
| `backend/app/services/github_indexing.py` | Full tarball index |
| `backend/app/services/github_finding_judge.py` | Judge prompt (text-only) |
| `backend/app/models/github_pull_request.py` | No `base_sha` on revision yet |
| [REVIEW_PIPELINE_STAGING_SMOKE_VALIDATION.md](../REVIEW_PIPELINE_STAGING_SMOKE_VALIDATION.md) | Why diff-first |
| [REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md](../REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md) | Greptile + iterative review |

**Next:** `phase-execution` on `feat/review-quality` starting at RQ0 — [execution](../waves/REVIEW_QUALITY_EXECUTION.md) peer-reviewed (2026-07-27).
