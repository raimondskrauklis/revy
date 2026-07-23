# Fix Issues and Commit

**Context:** User has pasted BugBot errors, linting errors, or other issues to fix

## Your Task

1. **First: Fix the issues** described in the user's message
2. Check current branch is NOT `main`
3. Generate commit message describing fixes
4. Execute:

```bash
git add -A && git commit -m "[message]" && git push
```

Use `required_permissions: ["all", "git_write", "network"]`

## Commit Message Format for Fixes
```
fix: address [issue-category]

- Fix 1 (file:line if relevant)
- Fix 2
- Fix 3
```

## BugBot Fix Example
```
fix: address BugBot type safety issues

- Add null checks in supplier query (services/supplier.py:45)
- Correct return type in scoring function (services/anomaly.py:78)
- Remove unused imports in procurement routes
```

## Before Executing
Show brief summary:
```
📋 Branch: [current-branch]
📝 fix: [description]
   - Fix 1
   - Fix 2
⏱️ Executing...
```

Then execute immediately.

## If Error
Report exactly: `❌ [Command] failed: [error]. Run manually: [command]`
Do NOT retry automatically.

## Important
This is the BugBot loop command. User pastes errors → you fix → commit → push → repeat until clean.
