# docs/agents/findings/REVY_PUSH_CADENCE_FINDINGS.md

# Revy push cadence — findings

**Status:** Baseline for LOOP batch-push (living; extend, do not replace, as PRs teach us more)  
**Date:** 2026-08-14  
**Scope:** When to fetch Revy comments relative to a push on an open PR. Not product internals of the reviewer. Not Bugbot (local, pre-commit).

**Verified against:** GitHub review-thread behaviour (outdated / Files-changed vs Conversation); published review-bot iteration patterns (incremental review on new commits; fetch-then-push loops); current LOOP paste in `.cursor/skills/create-execution-plan/SKILL.md` (`batch` tail) and `docs/knab/cache_warm/execution/KNAB_CACHE_WARM_P3_EXECUTION.md`.

---

## Build principles

- Inline review comments are anchored to a commit/diff. A later push can hide them from the working view without deleting them.
- The executing agent reads the **phase execution file**. Cadence that is not in that file will be skipped.
- Never force-push / rebase while Revy threads exist on the PR.
- End-of-program Revy WHILE is a **new** cycle on the combined tip. It does not replace draining the first-push review.

---

## Terminology

| Term | Meaning |
|:---|:---|
| **first-push** | P1 push that opens the PR. Revy starts. Do not drain comments. |
| **batch push** | Next push after P1. Fetch first, then one push with phase work + fixes. |
| **Outdated** | GitHub marks an inline comment when the hunk moved or a new commit landed. Often gone from Files changed; still in Conversation / API. |
| **Incremental review** | Typical bot behaviour on a later push: comment on the new delta, do not restate old findings. |
| **Sync barrier** | Re-fetch unresolved comments immediately before push so findings that arrived while coding this phase land in **this** push. |

---

## Three options (compared)

| # | Order | What happens | Verdict |
|:---|:---|:---|:---|
| **1** | Fetch Revy (P1 snapshot) → fix what still applies to HEAD → **one push** with phase work | Threads still fetchable (including outdated). Revy’s next run sees the combined tip. One review cycle covers several local phases. | **Adopt** |
| **2** | Push phase work first → then fetch Revy | Files changed is already the new diff. Old threads outdated. Revy busy on the new SHA. Agent can “see clean”. | **Reject** as default |
| **3** | Finish the whole LOOP, then fetch | Same hiding as 2, plus more HEAD drift. Late Revy focuses on the latest push. Human closeout becomes archaeology. | **Reject** as the only Revy moment |

Option 2 looks like fewer turns. Those turns return as lost threads.

---

## What GitHub and review bots do (external)

**Adopt for this LOOP:**

- Append commits; do not rewrite history during review. Force-push/rebase marks inline comments outdated and hides them from the current diff (GitHub contributor guidance; Copilot/agent-skill warnings).
- Fetch **unresolved** threads via Conversation / `gh api …/comments --paginate`, not only the Files changed tab.
- Gather findings → address → push. Re-fetch once immediately before push (sync barrier). Pattern used by published PR-closure agent skills (e.g. Netdata `pr-reviews`: without the barrier, the next round forever “fixes” issues that already landed on the previous HEAD).
- After that push, bots typically **incremental-review the new tip** (CodeRabbit: incremental vs full review). That is a **new** comment set — required WHILE at closeout, not a repeat of step 1.

**Defer:**

- Treating Revy’s incremental vs full-review switch as verified product behaviour until a real PR shows it. Assume incremental until proven otherwise.

**Reject:**

- Force-push to “clean” the PR while Revy threads are open.
- Using GitHub review **state** (`COMMENTED` / `APPROVED`) as “Revy is done”. Unresolved inline threads are the signal.

---

## Two Revy moments (not duplicates)

1. **Batch (mid-LOOP)** — Drain the **first-push** review into the same push as P2…Pk. Fetch outdated/unresolved. Triage against current HEAD (skip obsolete with a one-line note). Sync barrier. One push. Never force-push.
2. **Closeout WHILE** — After that push, poll until idle, fetch, fix, push. Repeat until no actionable threads. Then gap + docs. Then human.

Local phases between P1 and batch do **not** fetch. Revy works in parallel on the open PR.

---

## Edge cases

| Case | Handling |
|:---|:---|
| P1 comment obsolete because later local phases moved the code | Skip with a one-line note; do not “fix” dead hunks. |
| New Revy comments arrive while coding Pk | Sync barrier: re-fetch; fold into the **same** batch push. |
| Files changed looks empty of Revy | Still paginate API / Conversation. Outdated ≠ resolved. |
| Revy still `pending` | Do not push. Poll. Do not ask Continue?. |
| Two-phase program | P0 local, P1 may be both first-push and batch — README `Push` column is the override. |

---

## Decisions registry

| Q | Question | Status | Resolution |
|:---|:---|:---|:---|
| Q1 | Fetch then push with phase work, or push then fetch? | **locked** | Fetch first (option 1). |
| Q2 | Is end-of-LOOP Revy enough by itself? | **locked** | No. Batch drain + closeout WHILE. |
| Q3 | Force-push during review to keep a clean history? | **locked** | No. Append commits. |
| Q4 | Fetch only comments on the latest commit? | **locked** | No. All unresolved, including outdated. |
| Q5 | Second batch mid-program on a long wave? | **open** | README `Push` column may add another `batch` when a PR teaches us we waited too long. |

---

## Devil's advocate

- Fetch-first adds turns before the second push. Cheaper than reconstructing outdated threads at merge.
- Some P1 findings are already fixed by later local commits. That is why triage against HEAD exists — not a reason to skip the fetch.
- A lazy agent that only reads Files changed will still miss outdated threads unless the **execution file** says paginate / include outdated.

---

## Experiment / verification (on the next real PR)

- After P1, Revy posts inline comments. After local P2…, those threads show **Outdated** on Files changed but remain in `gh api` / Conversation. **Pass** if batch fetch still lists them.
- Batch push includes Revy fixes + unpushed phase commits. **Pass** if Revy’s next run comments on the **combined** tip (new SHA), not only restating P1.
- Sync barrier: a comment posted while Pk was in progress appears in the re-fetch and in the same push. **Fail** if it waits until closeout WHILE as if it were new-tip-only.

---

## References

- LOOP paste: `.cursor/skills/create-execution-plan/SKILL.md` (`batch` tail)
- Example file: `docs/knab/cache_warm/execution/KNAB_CACHE_WARM_P3_EXECUTION.md`
- Fetch/push skills: `.cursor/skills/ship-changes/SKILL.md`, `.cursor/skills/babysit-revy-pr/SKILL.md`
- GitHub: review comments become outdated on new commits; Files changed drops them; Conversation keeps them
- Incremental bot review: CodeRabbit docs (incremental vs `@full review`)
- Fetch-before-push + sync barrier: Netdata `.agents/skills/pr-reviews/SKILL.md`
