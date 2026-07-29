# Finding resolution dogfood P4 — MR-DG1 Moonshot signature (execution)

Phase **P4** of [FINDING_RESOLUTION_DOGFOOD_GENERAL_PLAN.md](../FINDING_RESOLUTION_DOGFOOD_GENERAL_PLAN.md). Baseline: findings § MR-DG1. **P4 only** — wave B, separate branch.

**Goal:** Moonshot does not flag valid `format_summary_comment(generation_groups=…, pr_active_groups=…)` as unknown kwargs.

## Decisions locked for P4

- **Branch:** `chore/moonshot-formatter-signature` — not mixed with wave A resolution fixes.
- **Prompt only:** add formatter public API snippet to reviewer system/context in `moonshot_review.py` — no signature change in `github_publish_formatter.py`.
- **Test:** assert prompt contains `generation_groups` and `pr_active_groups` parameter names near `format_summary_comment`.
- **Depends on P0:** program docs + findings baseline only — no probe, no P1–P3 deploy.
- **SSOT:** keep `active_program` on wave A during P4; optional Bugbot MR-DG1 bullet.

## Out of scope for P4

- Resolution manifest / G9 / thread collapse
- Judge JSON contract parser changes

---

## P4.0 — Branch + review context

**What:** Open `chore/moonshot-formatter-signature` from `main`; optional Bugbot note for MR-DG1 scope (no SSOT switch required).

**Files:** `.cursor/BUGBOT.md` (add MR-DG1 bullet if not present)

**Deliverable:** Branch created.

---

## P4.1 — Prompt formatter API context

**What:** Inject short “publish formatter API” block into Moonshot reviewer prompt listing `format_summary_comment(*, generation_groups, pr_active_groups)`.

**Files:** `backend/app/integrations/moonshot_review.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_moonshot_review.py -q
```

---

## P4.2 — Regression test for kwargs

**What:** Test fixture diff containing valid `format_summary_comment` call — document expected non-flag behavior (prompt assertion minimum; optional golden if Moonshot mocked).

**Files:** `backend/tests/unit/test_moonshot_review.py`

**Deliverable:** New test passes.

---

## P4.3 — Close MR-DG1 in findings

**What:** Update findings gap registry MR-DG1 → **closed** with PR link; README wave B status.

**Files:** `FINDING_RESOLUTION_DOGFOOD_FINDINGS.md`, `README.md`

**Deliverable:** Registry row updated.

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_moonshot_review.py -q
```

**Next:** none
