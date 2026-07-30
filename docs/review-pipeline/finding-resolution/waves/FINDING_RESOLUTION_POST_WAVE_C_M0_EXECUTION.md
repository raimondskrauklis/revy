# docs/review-pipeline/finding-resolution/waves/FINDING_RESOLUTION_POST_WAVE_C_M0_EXECUTION.md

# M0 — MR-DG1 Moonshot formatter API (execution)

Phase **M0** of [FINDING_RESOLUTION_POST_WAVE_C_GENERAL_PLAN.md](../FINDING_RESOLUTION_POST_WAVE_C_GENERAL_PLAN.md). Baseline: [backlog findings](../FINDING_RESOLUTION_POST_WAVE_C_BACKLOG_FINDINGS.md) § MR-DG1. **M0 only.** Supersedes [dogfood P4](../../finding-resolution-dogfood/waves/FINDING_RESOLUTION_DOGFOOD_P4_EXECUTION.md) for LOOP.

**Goal:** Moonshot does not flag valid `format_summary_comment(generation_groups=…, pr_active_groups=…)` as unknown kwargs.

## Decisions locked for M0

- **Branch:** `chore/moonshot-formatter-signature` — not mixed with wave D.
- **Prompt only:** formatter public API snippet in `moonshot_review.py` — no `github_publish_formatter.py` signature change.
- **Test:** prompt contains `format_summary_comment`, `generation_groups`, `pr_active_groups`.
- **SSOT:** no program switch — keep `finding-resolution-dogfood` active during M0.

## Out of scope for M0

- Pass 3 / FR-CS4 → **D0**
- Resolution manifest / G9 / thread collapse
- Judge JSON contract

---

## M0.0 — Branch

**What:** Open `chore/moonshot-formatter-signature` from `main`; optional Bugbot MR-DG1 bullet in `.cursor/BUGBOT.md`.

**Files:** `.cursor/BUGBOT.md` (optional one-line scope note)

**Deliverable:** Branch exists.

---

## M0.1 — Formatter API prompt + regression tests

**What:** Add publish-formatter API block to Moonshot reviewer system/context (`format_summary_comment(*, generation_groups, pr_active_groups)`). Add `test_moonshot_review.py` assertions that prompt includes those names.

**Files:** `backend/app/integrations/moonshot_review.py`, `backend/tests/unit/test_moonshot_review.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_moonshot_review.py -q
```

---

## M0.2 — Close MR-DG1 (findings row)

**What:** Update `FINDING_RESOLUTION_DOGFOOD_FINDINGS.md` MR-DG1 → **closed** with PR link; dogfood README sign-off row.

**Files:** `docs/review-pipeline/finding-resolution-dogfood/FINDING_RESOLUTION_DOGFOOD_FINDINGS.md`, `docs/review-pipeline/finding-resolution-dogfood/README.md`

**Deliverable:** Registry row shows closed PASS.

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_moonshot_review.py -q
```

**Human gate (non-gate):** Optional staging push with valid formatter test in diff — Moonshot does not flag kwargs.

**Next:** [`FINDING_RESOLUTION_POST_WAVE_C_D0_EXECUTION.md`](./FINDING_RESOLUTION_POST_WAVE_C_D0_EXECUTION.md) — after M0 merge.
