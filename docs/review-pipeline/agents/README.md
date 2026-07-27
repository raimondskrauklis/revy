# Agent orchestration (living docs)

**Purpose:** Capture how **humans + parent agents** run Revy program work in Cursor — LOOP discipline, local Bugbot, Greptile babysit, prompts. **Update as we go** (each RQ phase, each dogfood PR).

**Not:** product Revy review pipeline code (that is `backend/` + review-quality findings).

**Skills (source of truth for gates):** [phase-execution](../../../.cursor/skills/phase-execution/SKILL.md) · [ship-changes](../../../.cursor/skills/ship-changes/SKILL.md) · [babysit-pr](../../../.cursor/skills/babysit-pr/SKILL.md) · [review-bugbot](../../../.cursor/skills-cursor/review-bugbot/SKILL.md)

---

## Docs in this folder

| File | Status | When to update |
|------|--------|----------------|
| [ORCHESTRATION.md](./ORCHESTRATION.md) | **active** | New LOOP patterns, gate changes, parent discipline |
| [PROMPTS.md](./PROMPTS.md) | **active** | Per-phase Bugbot / invoke templates (RQ0+ ) |
| *(future)* `SUBAGENTS.md` | planned | When to Task vs Bugbot vs explore |
| *(future)* `DOGFOOD_INDEX.md` | planned | Links per PR case study |

---

## Related (outside this folder)

| Doc | Role |
|-----|------|
| [review-quality/REVIEW_QUALITY_DOGFOOD_PR50.md](../review-quality/REVIEW_QUALITY_DOGFOOD_PR50.md) | PR #50 — Greptile vs Revy visual, triage tables |
| [review-quality/REVIEW_QUALITY_REVIEW_CONTEXT.md](../review-quality/REVIEW_QUALITY_REVIEW_CONTEXT.md) | `.greptile/` + `BUGBOT.md` wiring (RC) |
| [REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md](../REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md) | GitHub publish UX target (Greptile bar) |

---

## How to extend

1. **New program PR dogfood** — add `../review-quality/REVIEW_QUALITY_DOGFOOD_PR<n>.md` or row in future `DOGFOOD_INDEX.md`.
2. **New RQ phase shipped** — add prompt block in [PROMPTS.md](./PROMPTS.md); optional dogfood row.
3. **New hard gate** — update skill **and** [ORCHESTRATION.md](./ORCHESTRATION.md) in same commit.

**First program using this folder:** review-quality `feat/review-quality` · [PR #50](https://github.com/raimondskrauklis/revy/pull/50).
