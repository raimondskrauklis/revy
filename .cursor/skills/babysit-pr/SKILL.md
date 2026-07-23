---
name: babysit-pr
description: >-
  On demand: fetch unresolved Bugbot comments from a GitHub PR via gh, fix valid
  findings, commit, and push. Use when user says babysit pr, fix bugbot on pr,
  or /babysit-pr.
---

# Babysit PR

Thin project wrapper around the Bugbot fix loop. Full command text: `.cursor/commands/babysit-pr.md`.

## When

User says *babysit pr*, *fix bugbot*, `/babysit-pr`, or gives a PR number/URL.

## Steps

1. Resolve PR from current branch (`gh pr view`) or user input.
2. Checkout PR head branch if needed.
3. GraphQL: unresolved `reviewThreads` where first comment `author.login == "cursor"`.
4. Validate each finding; fix valid ones only.
5. Ruff if backend Python changed.
6. Commit + push on feature branch if anything changed.

## Fetch (reference)

```bash
gh api graphql -f query='
{
  repository(owner: "OWNER", name: "REPO") {
    pullRequest(number: N) {
      reviewThreads(first: 100) {
        nodes {
          isResolved
          isOutdated
          path
          line
          comments(first: 1) {
            nodes { author { login } body }
          }
        }
      }
    }
  }
}'
```

Filter: `author.login == "cursor"`, `isResolved == false`.

## Not in scope (unless asked)

Merge conflicts, human review comments, CI triage loops. Built-in global `babysit` skill covers the wider merge-ready loop.
