# docs/review-pipeline/finding-resolution/waves/FINDING_RESOLUTION_POST_WAVE_C_D2_EXECUTION.md

# D2 — FR-CS8 observability (execution, optional)

Phase **D2** of [FINDING_RESOLUTION_POST_WAVE_C_GENERAL_PLAN.md](../FINDING_RESOLUTION_POST_WAVE_C_GENERAL_PLAN.md). Baseline: [backlog findings](../FINDING_RESOLUTION_POST_WAVE_C_BACKLOG_FINDINGS.md) § FR-CS8. **D2 only.**

**Goal:** Observable signal when sync clears `resolution_status` from `addressed` on `active` groups (supersede risk) — without durable DB column.

## Decisions locked for D2

- **Optional phase:** default **skip** unless operator explicitly schedules or production shows re-orphan after `skipped_not_head`.
- **Observability only:** structured log and/or reconcile manifest counter — no schema migration.
- **Out:** `path_removed_at_revision_id` column; skip-reset persistence logic.

## Out of scope for D2

- Pass 3 / FR-CS4 product changes → **D0**
- Hygiene / Track A

---

## D2.0 — Human gate (start decision)

**What:** Operator confirms re-orphan observed or explicitly requests D2. If skip → mark D2 **skipped** in execution index; proceed to **D3**.

**Deliverable:** Execution table row `D2 | optional | skipped` or `in progress`.

---

## D2.1 — Stamp-clear observability

**What:** In `apply_resolution_status_for_synchronize`, when resetting `resolution_status` to `None`, log (or increment manifest field) for groups that were `addressed` and remain `active`.

**Files:** `backend/app/services/github_resolution_metrics.py`, optional `reconcile_tasks.py` manifest passthrough

**Deliverable:** New test (e.g. `test_apply_resolution_status_clears_addressed_stamp_logged`) passes; phase gate still runs full `test_github_resolution_metrics.py`.

---

## D2.2 — Findings status update

**What:** Backlog findings FR-CS8 → **monitor + observability shipped** (not closed PASS).

**Files:** `FINDING_RESOLUTION_POST_WAVE_C_BACKLOG_FINDINGS.md`

**Deliverable:** Gap row updated.

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_github_resolution_metrics.py -q
```

**Next:** [`FINDING_RESOLUTION_POST_WAVE_C_D3_EXECUTION.md`](./FINDING_RESOLUTION_POST_WAVE_C_D3_EXECUTION.md)
