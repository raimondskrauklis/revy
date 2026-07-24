# Babysit PR (Greptile → fix → push)

**On demand.** User invokes `/babysit-pr` with an optional PR number or URL. Default: current branch’s open PR.

## Loop (one pass unless user asks to repeat)

1. **Resolve PR** — `gh pr view` on current branch, or parse user’s PR # / URL.
2. **Checkout** — `git fetch origin` then checkout PR head branch if not already on it.
3. **Fetch open Greptile threads** — GitHub GraphQL `reviewThreads` (or REST `pulls/{n}/comments`) where `author.login` is `greptile-apps` or `greptile-apps[bot]` and `isResolved == false`. Read severity, path, line, description.
4. **Triage** — Fix only valid findings; skip false positives (say why). Ignore resolved/outdated threads.
5. **Checks** — if `backend/` Python touched: `pipenv run ruff check --fix .` then `pipenv run ruff check .` from `backend/`. Run targeted tests when obvious.
6. **Commit + push** — only if fixes were made; branch must not be `main` / default prod branch.

```bash
git add <relevant files> && git commit -m "$(cat <<'EOF'
fix: address Greptile findings on PR #<n>

- <finding 1>
- <finding 2>
EOF
)" && git push
```

## Output

Short table: Severity | Location | Finding | Action (fixed / skipped / already resolved).

If nothing open: say so — no empty commit.

## Do not

- Change CI workflows to greenwash failures.
- Merge conflicts / full CI babysit loop unless user asks.
- Commit on `main`.
