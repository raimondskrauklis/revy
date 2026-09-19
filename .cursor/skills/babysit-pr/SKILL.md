---
name: babysit-pr
description: >-
  On demand: fetch unresolved Greptile review comments from a GitHub PR via gh,
  fix valid findings, commit, and push. Use when user says babysit pr, fix
  greptile on pr, or /babysit-pr.
---

# Babysit PR

**This repo does not use Greptile.** `integrations.greptile` is false. **Stop** — do not fetch Greptile threads or run this loop. Use [`babysit-revy-pr`](../babysit-revy-pr/SKILL.md) for Revy comments.

Thin project wrapper around the Greptile PR review loop (unused here). Full command text: `.cursor/commands/babysit-pr.md`.

## When

User says *babysit pr*, *fix greptile*, `/babysit-pr`, or gives a PR number/URL.

## Steps

1. Resolve PR from current branch (`gh pr view`) or user input.
2. Checkout PR head branch if needed.
3. Fetch unresolved review threads / PR comments where `author.login` is `greptile-apps` or `greptile-apps[bot]`.
4. Validate each finding; fix valid ones only.
5. Ruff + targeted tests if backend Python changed.
6. **Bugbot pass 1 (VALIDATE)** — brief per [ROLES.md](../../docs/review-pipeline/agents/prompts/ROLES.md) + [OUTPUT_FORMAT VALIDATE](../../docs/review-pipeline/agents/prompts/OUTPUT_FORMAT.md). Do not push if blockers remain.
7. Fix blockers → **Bugbot pass 2 (CLOSE)**; re-CLOSE until clean before push.
8. Commit + push on feature branch if anything changed.

## Fetch (reference)

**GraphQL** — all thread comments (not only first):

```bash
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
}' -f owner=OWNER -f name=REPO -F number=N
```

**REST fallback:**

```bash
gh api repos/OWNER/REPO/pulls/N/comments
```

Filter: `author.login` in `greptile-apps`, `greptile-apps[bot]`; `isResolved == false` (GraphQL).

## Not in scope (unless asked)

Merge conflicts, human review comments, CI triage loops. Built-in global `babysit` skill covers the wider merge-ready loop.
