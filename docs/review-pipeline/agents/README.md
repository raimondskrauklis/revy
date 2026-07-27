# How we build Revy (platform map)

**One page.** Process + evidence for program work in Cursor. Product spec lives in [review-quality/findings](../review-quality/REVIEW_QUALITY_FINDINGS.md); code in `backend/`.

**Pace:** distill outcomes; don’t hurry. Dogfood on our own PRs is product research.

---

## Four layers (don’t mix them)

| Layer | What | Where | Agent reads when |
|-------|------|-------|------------------|
| **1. Contract** | Locked Q#, schema, routes, RQ scope | [FINDINGS](../review-quality/REVIEW_QUALITY_FINDINGS.md) + [EXECUTION](../waves/REVIEW_QUALITY_EXECUTION.md) § RQn | Implementing RQn |
| **2. Process** | LOOP, gates, prompts | **This folder** + [skills](../../../.cursor/skills/) | Every push / phase-execution |
| **3. Wiring** | Greptile + Bugbot see the contract | `.greptile/files.json`, `.cursor/BUGBOT.md` | RQ0 + update active phase line |
| **4. Evidence** | What we learned on a real PR | [DOGFOOD_PR50](../review-quality/REVIEW_QUALITY_DOGFOOD_PR50.md), [CODE_REVIEW_LEARNINGS](../REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md) | After push; before next RQ |

**Post-v1 strategy** (read only when relevant): [STRUCTURAL_CONTEXT](../review-quality/REVIEW_QUALITY_STRUCTURAL_CONTEXT.md) (code graph), [REVIEW_CONTEXT](../review-quality/REVIEW_QUALITY_REVIEW_CONTEXT.md) (bot wiring roadmap).

---

## One RQ iteration

```text
Read EXECUTION § RQn only
        ↓
Implement + pytest + ruff
        ↓
LOCAL BUGBOT  ← mandatory (skills enforce)
        ↓
commit → push
        ↓
Greptile + Revy on PR  →  babysit valid threads  →  Bugbot  →  push
        ↓
One dogfood note (DOGFOOD doc row)
        ↓
Human gate if execution says stop (e.g. migration pause)
        ↓
Next RQ
```

**Three reviewers:** Bugbot (pre-push) · Greptile (contract + inline) · Revy (deployed behavior). Disagreement is signal, not noise.

---

## Principles

| | |
|-|-|
| **Distill** | Code without a dogfood note or prompt update = incomplete phase |
| **Pause** | Migration / staging gates are features |
| **Awesome for us** | Greptile-shaped GitHub UX (RQ7) is the bar — see PR #50 visual gap |
| **Thin routers** | [AGENTS.md](../../../AGENTS.md) = pointer; detail stays here |

---

## Files in this folder

| File | Role |
|------|------|
| [ORCHESTRATION.md](./ORCHESTRATION.md) | LOOP detail, anti-patterns, reviewer roles |
| [PROMPTS.md](./PROMPTS.md) | Copy-paste Bugbot / invoke per RQ |

**Skills (gates):** [phase-execution](../../../.cursor/skills/phase-execution/SKILL.md) · [ship-changes](../../../.cursor/skills/ship-changes/SKILL.md) · [babysit-pr](../../../.cursor/skills/babysit-pr/SKILL.md)

---

## What we deliberately don’t do

- Duplicate contract into `agents/` — point at FINDINGS + EXECUTION
- Bloat [AGENTS.md](../../../AGENTS.md) — one row in Read first; expand at **RQ8** doc-sync only
- New index files per PR — extend `DOGFOOD_PR50.md` table or add `DOGFOOD_PR<n>.md` when needed
- Skip Bugbot because Greptile will run later

**Active program:** review-quality · [PR #50](https://github.com/raimondskrauklis/revy/pull/50) · RQ0 done · migration pause.
