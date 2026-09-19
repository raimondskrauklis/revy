# How we build Revy (platform map)

**One page.** Process + evidence for program work in Cursor. Product spec lives in [review-quality/findings](../review-quality/REVIEW_QUALITY_FINDINGS.md); code in `backend/`.

**Pace:** distill outcomes; don’t hurry. Dogfood on our own PRs is product research.

---

## Four layers (don’t mix them)

| Layer | What | Where | Agent reads when |
|-------|------|-------|------------------|
| **1. Contract** | Locked Q#, schema, routes, RQ scope | [FINDINGS](../review-quality/REVIEW_QUALITY_FINDINGS.md) + [EXECUTION](../waves/REVIEW_QUALITY_EXECUTION.md) § RQn | Implementing RQn |
| **2. Process** | LOOP, gates, prompts | **This folder** + [prompts/](./prompts/) + [skills](../../../.cursor/skills/) | Every push / phase-execution |
| **3. Wiring** | Bugbot + Moonshot see the contract | `.cursor/BUGBOT.md`, `.revy/review-context.json`, [CURSOR_AGENT_WORKFLOW.md](../../utils/CURSOR_AGENT_WORKFLOW.md) | first LOOP commit |
| **4. Evidence** | What we learned on a real PR | [DOGFOOD_PR50](../review-quality/REVIEW_QUALITY_DOGFOOD_PR50.md), [CODE_REVIEW_LEARNINGS](../REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md), [`chain_of_thoughts/`](./chain_of_thoughts/) (raw exports) | After push; before next RQ |

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
Revy on PR  →  babysit-revy-pr + local Bugbot  →  push
        ↓
Human gate if execution says stop (e.g. migration pause)
        ↓
Next RQ
```

**Post-push:** Revy on the PR. Greptile is off — do not babysit it.

---

## Principles

| | |
|-|-|
| **Distill** | Bugbot + Revy runs → findings; **skim Bugbot transcripts** after each spin; durable rows in learnings — raw exports in `chain_of_thoughts/` when worth keeping ([RC-D23 distill](./chain_of_thoughts/cursor_bugbot_judge_p56_evidence_close.md)) |
| **Iterate** | Fix → re-Bugbot → push; multi-pass is normal (RC-D8), not one-shot |
| **Pause** | Migration / staging gates are features |
| **Awesome for us** | Revy GitHub UX is the bar |
| **Thin routers** | [AGENTS.md](../../../AGENTS.md) = pointer; detail stays here |

---

## Files in this folder

| File | Role |
|------|------|
| [ORCHESTRATION.md](./ORCHESTRATION.md) | LOOP detail, gates, anti-patterns |
| [prompts/ROLES.md](./prompts/ROLES.md) | Human / master / reviewer — who talks, who gates |
| [prompts/](./prompts/) | Distilled implement vs review, output format, per-RQ blocks |
| [PROMPTS.md](./PROMPTS.md) | Copy-paste Bugbot shells (points at `prompts/`) |
| [chain_of_thoughts/](./chain_of_thoughts/) | Committed Bugbot gate + Cursor chat exports (evidence archive; add selectively) · [judge P56 CLOSE distill](./chain_of_thoughts/cursor_bugbot_judge_p56_evidence_close.md) |

**Skills (gates):** [phase-execution](../../../.cursor/skills/phase-execution/SKILL.md) · [ship-changes](../../../.cursor/skills/ship-changes/SKILL.md) · [babysit-revy-pr](../../../.cursor/skills/babysit-revy-pr/SKILL.md)

---

## What we deliberately don’t do

- Duplicate contract into `agents/` — point at FINDINGS + EXECUTION
- Bloat [AGENTS.md](../../../AGENTS.md) — one row in Read first; expand at **RQ8** doc-sync only
- New index files per PR — extend `DOGFOOD_PR50.md` table or add `DOGFOOD_PR<n>.md` when needed
- Skip Bugbot because Revy will run later

**Active program:** review-quality **merged** — [PR #50](https://github.com/raimondskrauklis/revy/pull/50) · **Next:** human gate AS2 + `0026` on staging → tag `review-quality-v1` · **Quick ref:** [CURSOR_AGENT_WORKFLOW.md](../../utils/CURSOR_AGENT_WORKFLOW.md)
