# Post review-quality — findings (baseline)

**Purpose:** Capture **actual** signals from PR [#51](https://github.com/raimondskrauklis/revy/pull/51) dogfood (RQ9 + agent-doc experiment) and list **target improvements** — failing, deferred, and future. No execution steps yet.

**Date:** 2026-07-27 · **Head:** `8cd8e03` (+ babysit fixes pending)

**Related:** [review-quality FINDINGS](../review-quality/REVIEW_QUALITY_FINDINGS.md) · [DOGFOOD § PR #51](../review-quality/REVIEW_QUALITY_DOGFOOD_PR50.md#dogfood-pr-51--docsagent-work-rq9) · [REVIEW_CONTEXT RC-D19/20](../review-quality/REVIEW_QUALITY_REVIEW_CONTEXT.md)

---

## Executive summary

| Surface | Verdict |
|---------|---------|
| **Greptile** | Strong — cited RQ9 mechanism, confidence 4/5, 2 actionable P2 threads |
| **Local Bugbot** | Valuable reasoning; weak handoff (RC-D19) |
| **Revy bot (`revy/review`)** | Weak — JSON blob, no Greptile-shaped narrative (PQ-UX) |
| **CI** | Validate green; deploy **skipped on PR** (expected) |
| **Merge readiness** | Code sound after P2 fixes; human gate AS2 still open |

---

## Greptile PR #51 (actual)

### Summary comment (top-level)

- **Understood RQ9:** neutral finalize for draft/closed at review time; shared `_finalize_pipeline_github_check`; split DB context; unit tests cited.
- **Confidence:** 4/5 — safe to merge; notes `conclusion: str` typing gap and closed-PR test asymmetry.
- **Cited execution § RQ9?** **Yes** — mechanism matches execution doc (not diff-only).
- **Cited wired docs (ROLES, workflow)?** **No** in summary — code-path review; RC0 execution implicit via diff + `files.json`.
- **Mermaid flowchart:** present (skip in distill).

### Inline threads (2 open P2 — babysit)

| # | Sev | File | Finding | Action |
|---|-----|------|---------|--------|
| G51-1 | P2 | `github_pipeline_trace.py:731` | `conclusion: str` untyped — use `Literal["failure", "neutral"]` | **Fix** — valid |
| G51-2 | P2 | `test_review_pipeline.py:292` | Closed-PR test missing `pipeline_check_summary` assertion | **Fix** — valid |

### Greptile vs local Bugbot (PR #51)

| | Greptile | Local Bugbot (ui_7) |
|--|----------|---------------------|
| **When** | Post-push | Pre-push |
| **Draft smoke doc trap** | Not raised (code-focused) | **Medium** — staging gate wording |
| **Backend logic** | Clean 4/5 | No logic bugs |
| **Test gaps** | P2 closed-PR assertion | P2 trace test scope |
| **Output shape** | Summary + inline P2 | 4 findings; no Deferred table (RC-D19) |

---

## Revy bot (`revy/review`) — PQ-UX gap

**Observed on PR #51:** check **completed** in ~6m (neutral/success path on old deploy). Issue comment is a **JSON payload** with:

- Single **info** row: untyped `conclusion` (same theme as Greptile G51-1)
- Confidence 5/5
- No narrative, no “files needing attention” prose, no confidence explanation

**Gap vs Greptile target (G-UX):**

| Greptile | Revy today | Target |
|----------|------------|--------|
| Long summary comment + confidence | JSON `review_comment` blob | RQ7 formatter on customer PRs |
| P-badge inline threads | Weak / absent on this PR | RQ7 inline + badges |
| 👀 ack on open | N/A | **G-UX+** optional |

**Not a blocker for merging #51** — staging runs pre-RQ9 deploy; comment shape is pre-formatter or fallback path.

---

## CI / deploy signals

| Check | PR #51 | Note |
|-------|--------|------|
| Lint, Type Check, Build, Test | ✅ | `SKIP_CI_TESTS=true` still — tests may be shallow in CI |
| Greptile Review | ✅ | 4m |
| `revy/review` | ✅ neutral ~6m | Old deploy behavior |
| Deploy to Droplet | **Skipped** | **Expected** — `if: github.ref == refs/heads/main && push` only |

**PQ-CI-1:** Deploy skip on PR is correct; document in recovery checklist so operators don’t chase “skipped” as failure.

---

## Agent orchestration (RC layer)

| ID | Signal | Result | Target |
|----|--------|--------|--------|
| **RC-D19** | Bugbot ui_7 — no Deferred/Scope in output | Platform XML over table | OUTPUT_FORMAT always-require; master reads thinking |
| **RC-D20** | Greptile 👀 on PR open | Queued ack only | Log first comment — done § PR #51 |
| **RC-D21** | Greptile summary cites RQ9 mechanism without PR body | **RC0 works** — `files.json` + diff > PR prose | Keep RC2-lite PR template optional |
| **RC-D22** | Revy bot JSON vs Greptile narrative | Product gap | **PQ-UX** / G-UX track |

---

## Human gate (still open — PQ-OPS)

| Gate | Status |
|------|--------|
| `alembic upgrade head` through `0026` on staging | ☐ |
| Celery beat + workers restarted | ☐ |
| AS2 autostart e2e (diff index, pipeline GET) | ☐ |
| G10 draft-after-index → `neutral` smoke | ☐ |
| Tag `review-quality-v1` | ☐ |

RQ9 merge **before** tag is consistent with execution doc.

---

## Deferred / future (not PR #51 blockers)

| ID | Item | Track | Why deferred |
|----|------|-------|--------------|
| **PQ-D1** | SC3 `changed_symbols` population | PQ-STRUCT | v1 stub only |
| **PQ-D2** | Unique `pipeline_runs.index_job_id` | v1.1 | No hot-path proof yet |
| **PQ-D3** | Pending review → orphan `in_progress` check | Hardening | Pre-existing; not RQ9 regression |
| **PQ-D4** | `SKIP_CI_TESTS=false` in Actions | PQ-CI | Secrets readiness |
| **PQ-D5** | G-UX+ ack (👀, “read summary”) | PQ-UX | Post-v1 interaction design |
| **PQ-D6** | RQ-RC-1 path-scoped `files.json` | PQ-RC | After tag if noise grows |
| **PQ-D7** | RQ-STRUCT-1 cross-file graph | PQ-STRUCT | Post-v1 north star |
| **PQ-D8** | Human dismiss UI (R7.6) | Product | Out of review-quality scope |

---

## Target improvements (next wave candidates)

Prioritized from dogfood — **not yet a general plan**:

| Priority | ID | Improvement | Source |
|----------|-----|-------------|--------|
| **P0** | PQ-OPS-1 | Complete human gate AS2 + tag | Recovery Track F |
| **P1** | PQ-UX-1 | Revy GitHub comment → Greptile-shaped narrative (not JSON blob) | PR #51 revybot |
| **P1** | PQ-UX-2 | G-UX+ lightweight ack on webhook/`@revy` | Greptile 👀 affordance |
| **P2** | PQ-RC-1 | RC1 scoped doc sets + RC2 active slice pointer | REVIEW_CONTEXT ladder |
| **P2** | PQ-HARDEN-1 | Pending-review orphan G10 finalize | Dogfood parking |
| **P3** | PQ-STRUCT-1 | SC3 manifest population | STRUCTURAL_CONTEXT |
| **P3** | PQ-CI-1 | Enable full CI tests on PR | `SKIP_CI_TESTS` |

---

## Q-registry (PQ)

| Q# | Question | Status | Resolution |
|----|----------|--------|------------|
| **PQ1** | Merge #51 before human gate? | **open** | Yes if P2 babysit clean — gate is staging ops |
| **PQ2** | Is deploy “skipped” on PR a bug? | **locked** | **No** — main push only |
| **PQ3** | Is Revy JSON comment acceptable v1? | **open** | **No** for product bar — **PQ-UX-1** |
| **PQ4** | Next program folder name? | **locked** | `post-review-quality/` (this doc) |

---

## Next steps

1. Babysit #51 — close G51-1, G51-2; VALIDATE → CLOSE Bugbot; push.
2. Fill Greptile threads resolved on GitHub after push.
3. `create-general-plan` from this findings doc when ready for next wave.
4. Human gate AS2 on staging after merge.
