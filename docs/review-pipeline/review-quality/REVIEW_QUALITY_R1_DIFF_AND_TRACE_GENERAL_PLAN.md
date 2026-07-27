# Review quality R1 — Diff-first review + pipeline trace

General plan from [REVIEW_QUALITY_FINDINGS.md](./REVIEW_QUALITY_FINDINGS.md) tracks **D + O**. **No execution steps.** Implemented in **same PR** as R2–R5 (S1).

**Cross-cutting:** workspace-tenanted pipeline tables; `items_view` `GET …/pipeline` (O9); hand-written Alembic; `backend/tests/unit/`; no Reviewer UI trace tab; `index_mode=full` preserved with warnings; **AS2 staging e2e gate** (RQ8).

**Depends on:** R0–R8 on `main`.

---

## Goal

Default review scope = **PR diff + bounded context** (D13); every run leaves a **replayable trace** (prompt, raw LLM I/O, retrieval manifest). Fixes smoke #44 haystack review and enables tuning without Celery log archaeology.

---

## Scope

**In:**

| Area | Deliverable |
|------|-------------|
| **Compare / revision** | `base_sha` from webhook `pull_request.base.sha` at revision create (D8); `github_api.compare_commits`; changed-file list |
| **Diff index (D13)** | Compare → unified diff in context pack; tarball at `head_sha` → chunk/embed **changed paths only**; manifest in trace |
| **Index mode** | `diff` default; `full` for `deep`/`critical` via profile (AS1) — `index_mode` on job; optional `POST …/index` body field in R1 if needed |
| **Context pack** | PR metadata → changed files → unified diff (D5 128KB cap) → scoped supplemental chunks (D6, D12) |
| **Retrieval** | Lenses scoped to changed-file chunks; D7 test exclusion; manifest with lens, score, `in_diff`, rank |
| **Pipeline trace** | `github_pipeline_*` tables (migration subphase 0); capture index + retrieve + review + judge + publish artifacts (O1–O3, O7) |
| **API** | `GET …/review-runs/{id}/pipeline` — **`items_view`** (O9) |
| **Retention** | 90d default (O4); Celery purge job (O8) |
| **Warnings** | `full` mode + compare `fallback_reason` in manifest **and** publish footer (D13-F) |
| **Structural trace (SC3)** | Manifest: `changed_symbols`, `structural_context_mode`, `caller_files_*` — v1 default `none`; see [structural context](./REVIEW_QUALITY_STRUCTURAL_CONTEXT.md) |
| **Autostart** | **Staging e2e gate** (AS2): toggle on → `opened`/`synchronize` full pipeline; code fix only if gate fails |
| **D10** | Fingerprint per [peer review](./REVIEW_QUALITY_PEER_REVIEW.md) D10 formula + D10-M |

**Out:** Greptile narrative sections beyond minimal footer (R3); copy-forward incremental (R2/C1); `evidence_snippet` (R4); Reviewer UI tab; Langfuse; agents; mermaid.

---

## Deliverables

1. `index_mode=diff` default for autostart / `@revy review` on `standard` (AS1).
2. Reviewer prompt includes **unified diff** before supplemental chunks.
3. Each completed review run has **prompt**, **raw response** (always), **parse_report**, **retrieval manifest** (`index_mode`, `changed_files`, `fallback_reason` if any).
4. Judge step stores per-candidate prompt + raw response when judge runs.
5. `items_view` member can read pipeline for PRs in their workspace.
6. Staging smoke #44 replay: `diff` mode; findings on changed file only; no paraphrase duplicate rows (D10).
7. `full` index works; warning when `deep`/`critical` or explicit full.
8. Autostart e2e green on staging with toggle on.

---

## Depends on

Review pipeline R3–R8; Voyage + reviewer LLM on staging.

---

## Out of scope (R1 slice label only)

- C1 copy-forward embed reuse (R2)
- Greptile formatter LLM (R3)
- Evidence column (R4)
- Workspace settings UI for index mode (API/env v1)

---

## Next

Section in `waves/REVIEW_QUALITY_EXECUTION.md` via **`create-execution-plan`**.
