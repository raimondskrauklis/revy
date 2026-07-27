# Per-phase Custom Instructions (distilled)

**Index:** [prompts/README.md](./README.md) · **Output shape:** [OUTPUT_FORMAT.md](./OUTPUT_FORMAT.md)

Copy the active **§ RQn** block into Bugbot Custom Instructions. `.cursor/BUGBOT.md` points at contract docs + [CURSOR_AGENT_WORKFLOW.md](../../../utils/CURSOR_AGENT_WORKFLOW.md).

---

## RQ0 — Schema

```text
§ RQ0 + FINDINGS locked Q#. Migration 0026 only — hand-written Alembic.
FK ondelete SET NULL on optional pipeline FKs; ix_github_pipeline_runs_created_at for O8.
AS1: index_mode default full on ORM; pipeline jobs set diff at create.
```

---

## RQ1 — Diff + compare

```text
§ RQ1. AS1: index_mode at job create, not inferred in run_index_job.
D13 hybrid index; compare in review worker; get_latest_completed_index_job.
Chunk delete only after embed success; empty raw_chunks stale path cleanup.
```

---

## RQ2 — Diff-first review

```text
§ RQ2. Diff-first prompt order; D7 test exclusion; D10 fingerprint; D13-F fallback_reason in manifest.
Scoped retrieval to changed paths; parse_report on review run.
```

---

## RQ3 — Pipeline trace

```text
§ RQ3. O2/O3 artifacts; retrieve step before review; GET pipeline items_view.
G10: in_progress at start, finalize on all failure paths (index/review/reconcile/publish).
O8 purge beat; stash github_check_run_id before index completes.
```

---

## RQ4 — Incremental index

```text
§ RQ4. content_hash on insert; index_incremental=false skips copy-forward (deep/critical full).
Parent revision = prior row same PR; first push no-op copy-forward.
Copy-forward on deletion-only sync (empty paths_to_index); wipe revision before incremental rebuild.
Manifest: reused_count, new_count, embed_batches. Rollback chunk work on embed failure.
ReviewAfterIndexOutcome: fail check on ServiceUnavailableError only, not draft/closed/pending.
```

---

## RQ5 — Evidence + judge *(shipped)*

```text
§ RQ5. evidence_snippet at parse from diff hunk or top retrieval chunk.
_build_judge_prompt grounding (E2); judge dismissed → resolved group state.
Pipeline judge step manifest includes per-candidate prompt/raw/outcome.
```

---

## RQ6 — Resolution metrics *(shipped)*

```text
§ RQ6. resolution_status on synchronize: judge_dismissed | addressed | still_open.
Hook in apply_pull_request_webhook_event before pipeline enqueue; compare line-region heuristic.
```

---

## RQ7 — Greptile publish *(shipped)*

```text
§ RQ7. G3 split check vs issue comment; G2 confidence comment-only; G9 resolution prose;
summary_json on publish job; D13-F footer; Moonshot formatter with table fallback.
```

---

## RQ8 — Doc-sync + tag *(shipped — human gate AS2)*

```text
§ RQ8. Merged to main (PR #50). Human gate: staging 0026 + AS2 → tag review-quality-v1.
```

---

## RQ9 — Post-merge hardening *(active)*

```text
§ RQ9. G10 neutral finalize for draft/closed PR (no orphan in_progress).
Split get_db_context in index_tasks — test TX boundary. Greptile scope: CURSOR_AGENT_WORKFLOW + ROLES.
```

---

## Generic tail (any phase)

```text
Read .cursor/BUGBOT.md + docs/utils/CURSOR_AGENT_WORKFLOW.md. Backend scope only unless diff touches frontend.
Fix blockers in implementer session; do not commit from Bugbot subagent.
```
