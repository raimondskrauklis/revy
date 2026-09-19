---
name: babysit-revy-pr
description: >-
  Poll Revy PR check until idle (120s), fetch revybot comments, fix valid
  findings, local Bugbot until clean, commit and push, loop until solved. Use
  when user says babysit revy, fix revy on pr, revy poll loop, or /babysit-revy-pr.
---

# Babysit Revy PR

Post-push loop for **Revy** on our own PRs (`integrations.revy: true`). Gates on the **Revy** check and `revybot` comments.

**Command:** `.cursor/commands/babysit-revy-pr.md` · **Ship gate:** [ship-changes](../ship-changes/SKILL.md) · **Orchestration:** [ORCHESTRATION.md](../../docs/review-pipeline/agents/ORCHESTRATION.md)

**Not:** merge, CI triage, or push while Revy is running. Greptile is off — do not invoke `babysit-pr`.

---

## When

User says *babysit revy*, *fix revy on pr*, *revy poll loop*, `/babysit-revy-pr`, or gives a PR number/URL with Revy follow-up.

---

## Outer loop (until solved)

Repeat until **no unresolved actionable Revy findings** remain **and** Revy check is idle (`pass` / `fail` / `skipping` / `neutral`):

```text
1. Resolve PR + branch (checkout head if needed)
2. Poll Revy idle (120s interval) — see below
3. Fetch Revy comments — see below
4. Triage → fix valid findings only
5. ruff + targeted pytest if backend touched
6. Local Bugbot (review-bugbot) until clean
7. Commit + push (feature branch only)
8. Go to step 2 (Revy re-runs after push)
```

**Solved:** no new actionable Revy inline findings after the latest idle pass (code fixed for all open threads). GitHub threads may stay `unresolved` until Revy re-reviews or you resolve manually — use thread `body` + `path:line`, not only `isResolved`.

**Stop early (report):** Revy suspended (no check row), user says stop, or only non-actionable INFO with explicit skip rationale.

---

## Step 2 — Poll Revy idle (120s)

**Poll interval:** `120` seconds between status checks.

```bash
PR=$(gh pr view --json number -q .number)
# Repeat until Revy not pending/in_progress/queued (max attempts: user context; default keep looping outer loop)
gh pr checks "$PR" 2>&1 | grep -iE '^Revy[[:space:]]'
```

| Revy status | Action |
|-------------|--------|
| `pending` / `in_progress` / `queued` | Sleep 120s, poll again |
| `pass` / `fail` / `skipping` / `neutral` | **Idle** — fetch comments |
| No `Revy` row | Idle (app suspended) — fetch comments anyway |

Use `sleep 120` (Shell) between polls. Do not push during `pending`/`in_progress`.

---

## Step 3 — Fetch Revy comments

**Prefer GraphQL** (thread resolved/outdated):

```bash
OWNER=$(gh repo view --json owner -q .owner.login)
NAME=$(gh repo view --json name -q .name)
PR=$(gh pr view --json number -q .number)

gh api graphql -f query='
query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      reviewThreads(first: 100) {
        nodes {
          isResolved
          isOutdated
          comments(first: 20) {
            nodes { author { login } body path line originalLine }
          }
        }
      }
    }
  }
}' -f owner="$OWNER" -f name="$NAME" -F number="$PR"
```

**REST fallback** (inline review comments):

```bash
gh api "repos/$OWNER/$NAME/pulls/$PR/comments" \
  --jq '.[] | select(.user.login|test("revy";"i")) | {path, line, body}'
```

**Issue comments** (check summary / narrative):

```bash
gh pr view "$PR" --comments
gh api "repos/$OWNER/$NAME/issues/$PR/comments" \
  --jq '.[] | select(.user.login|test("revy";"i")) | {body}'
```

Filter: `author.login` matches `revy`, `revybot`, `revybot[bot]`; skip `isResolved` / outdated threads unless user asks to reopen.

---

## Step 4–7 — Fix, gate, ship

| Step | Rule |
|------|------|
| Triage | Fix valid bugs; skip false positives (state why). Prefer minimal diff. |
| ruff | `cd backend && pipenv run ruff check --fix . && pipenv run ruff check .` when Python changed |
| Tests | Targeted pytest for touched modules; manifest `test_commands` for broad regressions |
| Bugbot | Invoke **`review-bugbot`** on `uncommitted changes`; fix blockers; re-run until clean |
| Commit | Plain message, e.g. `fix: address Revy findings on PR #<n>` |
| Push | Only on feature branch; **never** while Revy `pending`/`in_progress` |

After push, **always** re-enter poll loop (step 2) before declaring done.

---

## Output

Per iteration, short table:

| Severity | Location | Finding | Action |
|----------|----------|---------|--------|
| … | `path:line` | one line | fixed / skipped / pending Revy |

Final line: PR URL, last commit sha, Revy check status, open thread count.

---

## Do not

- Push while Revy is running.
- Commit on `main` / default prod branch.
- Push with open local Bugbot blockers.
- Empty commit unless re-triggering Revy after idle with no code changes (rare).
