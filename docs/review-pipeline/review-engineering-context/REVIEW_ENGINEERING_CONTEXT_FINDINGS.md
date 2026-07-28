# Review engineering context — findings

**Date:** 2026-07-29  
**Purpose:** Baseline for wiring **intent** (locked decisions, execution contract) into **all** PR reviewers — especially **revybot** — not only Greptile and Cursor Bugbot. **No execution steps.**

**Status:** Findings only — after judge-json-contract. See [README.md](./README.md).

**Evidence:** PR [#58](https://github.com/raimondskrauklis/revy/pull/58) dogfood; [REVIEW_QUALITY_REVIEW_CONTEXT.md](../review-quality/REVIEW_QUALITY_REVIEW_CONTEXT.md); live RTU structured-output smoke (2026-07-29).

---

## Summary

**Context is king.** Greptile cites program docs because `.greptile/files.json` injects execution + findings on every review. Cursor Bugbot gets the same via `.cursor/BUGBOT.md`. **revybot** (GitHub “Revy” check) reviews diff + repo only — no engineering context — so it gives **generic API advice** that contradicts locked program decisions.

Example on PR #58:

| Reviewer | Structured-output comment | Ground truth |
|----------|---------------------------|--------------|
| **Greptile** | Add `format.name` to `judge_structured_output_config` | Wrong for RTU — workspace rejects structured outputs; `name` is **extra input** |
| **revybot** | `output_config` envelope may be wrong (`output` vs `output_config`) | Wrong — gateway accepts `output_config`; failure is feature unsupported |
| **Operator smoke** | — | `structured_outputs not supported in your workspace`; plain JSON works |

Greptile had **partial** context (program docs, not live smoke). revybot had **no** program context. Both missed the P3 lock in findings until operator ran smoke.

---

## Where we are

### Context wiring today

| Reviewer | Mechanism | Gets execution + findings? | Gets live operator smoke? |
|----------|-----------|----------------------------|---------------------------|
| **Greptile** | `.greptile/files.json` + `scope` | Yes (when wired per program) | Only if findings doc updated |
| **Cursor Bugbot** | `.cursor/BUGBOT.md` links | Yes (when wired per program) | Same |
| **revybot** | None | **No** | **No** |
| **Revy product** (Moonshot pipeline) | `prepare_review_context` | Code/PR only | N/A |

RC0 shipped Greptile + Bugbot for dogfood ([REVIEW_QUALITY_REVIEW_CONTEXT.md](../review-quality/REVIEW_QUALITY_REVIEW_CONTEXT.md)). RC4 (`.revy/rules` in DB) and RC5 (pipeline inject locked Q#) are **open** — product path, not repo file clone.

### Dogfood signal (PR #58)

| Signal | Result |
|--------|--------|
| Greptile confidence | 4/5 — cites missing `format.name` from program shape, not RTU workspace |
| revybot | Useful hygiene (smoke script `--prompt-file`, `compare-direct` exit) + false-positive API warnings |
| Operator RTU smoke | Locks P3: parse helper + snippet-first; structured output off on gateway |
| Resolution | Disposition comments need **locked decision + live evidence** — neither bot had both |

### Two context layers (unchanged)

| Layer | Question | v1 dogfood | Target |
|-------|----------|------------|--------|
| **Engineering context** (this program) | What should this PR implement? | Greptile + Bugbot only | revybot + customer Revy |
| **Structural context** | Who calls X? Impact beyond diff? | SC3 manifest; RQ-STRUCT-1 | Graph + agent (SC8) |

Both matter. This program is **engineering context** only.

---

## Problem statement

1. **Intent drift** — revybot flags code that matches a **locked** program decision because it never sees findings/execution.
2. **Duplicate maintenance risk** — copying `.greptile/files.json` to a second hand-edited file will drift.
3. **Incomplete Greptile context** — `files.json` does not auto-include operator smoke results; findings must be updated manually (P0 matrix on #58).
4. **Customer gap** — customer repos will not have `.greptile/`; product must own policy (RC4), not vendor config.

---

## Locked decisions (discussion 2026-07-29)

| ID | Decision |
|----|----------|
| **RCX-D1** | **Single source of truth** — one doc set per active program (execution + findings + general plan); all reviewers consume the **same** paths, not forked copies. |
| **RCX-D2** | **Do not duplicate Greptile JSON by hand** — revybot integration reads the same paths as `.greptile/files.json` (or a shared manifest generated from it). |
| **RCX-D3** | **Operator evidence is first-class** — smoke matrices, live API errors, and P3 locks belong in findings; reviewers should prefer findings over generic API lore. |
| **RCX-D4** | **Dogfood first** — wire revybot on this repo before RC4 DB productization. |
| **RCX-D5** | **Out of scope v1** — replacing Greptile; full structural graph (SC8); auto-sync from every LOOP commit without human findings touch. |

---

## What we need to achieve

### Success criteria (dogfood)

1. revybot inline/check review cites **locked IDs** (e.g. JC-D*, P3 lock) when flagging contract issues — same bar as Greptile RC-D3 on PR #50.
2. revybot does **not** recommend changes that contradict findings (e.g. `format.name` on RTU gateway).
3. One update to findings smoke matrix is visible to **Greptile + Bugbot + revybot** without editing three configs.
4. False-positive rate on program PRs drops vs PR #58 baseline (operator-tracked).

### Deliverables (for future general plan)

| # | Deliverable | Notes |
|---|-------------|--------|
| **RCX-G1** | Shared context manifest | Parse `.greptile/files.json` or thin wrapper; revybot prompt injection |
| **RCX-G2** | revybot dogfood wiring | Hosted check reads manifest + diff scope |
| **RCX-G3** | Active program pointer | Which slice is “active” (RC2) — avoid stale multi-program noise |
| **RCX-G4** | Findings smoke section contract | Standard table for operator RTU/direct results |
| **RCX-G5** | Disposition helpers | Babysit: link finding ID + smoke evidence in thread replies |
| **RCX-G6** | RC4 spike | `workspace_review_policy` shape — EN+LV; post-dogfood |

### Explicitly out of scope (v1)

- Vendor Greptile config in **customer** repos (product owns via DB)
- Embedding / vector index of docs
- Auto-closing bot threads without human disposition

---

## Gap registry

| ID | Gap | Evidence |
|----|-----|----------|
| **RCX-1** | revybot has no engineering context | PR #58 `format.name` / `output_config` false positives |
| **RCX-2** | Greptile lacks live smoke unless findings updated | P0 matrix filled after operator run, not before |
| **RCX-3** | Three manual wires per program (Greptile, Bugbot, revybot TBD) | phase-execution RC0 only covers two |
| **RCX-4** | `BUGBOT.md` lists many shipped programs — context noise | RC2 active pointer not automated |
| **RCX-5** | Customer repos need DB policy, not `.greptile/` | [PRODUCT_PATTERNS](../REVIEW_PIPELINE_PRODUCT_PATTERNS.md) |

---

## Reproduce (PR #58)

```bash
# Plain judge — pass
cd backend && pipenv run sh -c 'python -m scripts.test_anthropic_judge_gateway'

# Structured — fail (workspace)
cd backend && pipenv run sh -c 'python -m scripts.test_anthropic_judge_gateway --structured'
```

See [JUDGE_JSON_CONTRACT_FINDINGS.md](../judge-json-contract/JUDGE_JSON_CONTRACT_FINDINGS.md) § P0 smoke results.

---

## Next steps

1. Finish **judge-json-contract** (P3–P5) on current branch — do not block on this program.
2. `create-general-plan` from this findings doc when revybot wiring becomes priority.
3. Spike **RCX-G1** — revybot reads `.greptile/files.json` paths for active `backend/**` PRs.
