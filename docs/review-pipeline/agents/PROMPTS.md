# Agent prompts (copy-paste)

**Index:** [agents/README.md](./README.md) · **LOOP rules:** [ORCHESTRATION.md](./ORCHESTRATION.md)

Add a section per program phase as we ship it. Keep **Custom Instructions** pointed at the active execution § and locked Q#.

---

## Review quality — RQ0 (schema)

### Local Bugbot (pre-push)

```text
Full Repository Path: /absolute/path/to/revy
Diff: uncommitted changes
Custom Instructions: Review against docs/review-pipeline/waves/REVIEW_QUALITY_EXECUTION.md
§ RQ0 and REVIEW_QUALITY_FINDINGS.md locked Q#. Migration 0026 only — hand-written Alembic.
FK ondelete SET NULL on optional pipeline FKs; created_at index for O8. Fix blockers only.
```

### phase-execution invoke

```text
@docs/review-pipeline/waves/REVIEW_QUALITY_EXECUTION.md /phase-execution
```

Stop after RQ0 migration pause until staging `alembic upgrade head`.

### babysit-pr

```text
/babysit-pr 50
```

Skip Revy findings for RQ1 scope; fix Greptile P1/P2 in migration/ORM. **Local Bugbot before push.**

---

## Review quality — RQ1 (diff + compare)

*(Add when RQ1 starts — AS1 index_mode at job create, compare_commits, D13.)*

```text
Full Repository Path: …
Diff: branch changes
Custom Instructions: REVIEW_QUALITY_EXECUTION.md § RQ1. AS1: index_mode at job create not column default.
D13 hybrid index; re-call compare in review worker.
```

---

## Review quality — RQ7 (Greptile publish)

*(Add when RQ7 starts — G3 split, G5 formatter, G10 check finalize.)*

```text
Custom Instructions: § RQ7. G3 compact check vs full issue comment. G10 update_check_run not one-shot create.
```

---

## Generic parent agent reminders

Paste into long sessions when context drifts:

```text
- Local Bugbot before every push (not optional).
- Read only current RQ execution section.
- Migration pause: stop LOOP after RQ0 until human confirms staging migration.
- Minimal doc commit per phase; update BUGBOT.md active phase line.
```
