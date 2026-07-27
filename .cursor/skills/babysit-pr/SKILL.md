---
name: babysit-pr
description: >-
  On demand: fetch unresolved Greptile review comments from a GitHub PR via gh,
  fix valid findings, commit, and push. Use when user says babysit pr, fix
  greptile on pr, or /babysit-pr.
---

# Babysit PR

Thin project wrapper around the Greptile PR review loop. Full command text: `.cursor/commands/babysit-pr.md`.

## When

User says *babysit pr*, *fix greptile*, `/babysit-pr`, or gives a PR number/URL.

## Steps

1. Resolve PR from current branch (`gh pr view`) or user input.
2. Checkout PR head branch if needed.
3. Fetch unresolved review threads / PR comments where `author.login` is `greptile-apps` or `greptile-apps[bot]`.
4. Validate each finding; fix valid ones only.
5. Ruff + targeted tests if backend Python changed.
6. **Local Bugbot** — `review-bugbot` on fix diff; do not push if blockers remain ([agent orchestration](../../docs/review-pipeline/review-quality/REVIEW_QUALITY_AGENT_ORCHESTRATION.md)).
7. Commit + push on feature branch if anything changed.

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
