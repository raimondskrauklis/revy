# Create New Feature Branch and Commit

**Context:** User is on `main` branch and has already run `git stash`

## Your Task

1. Check current branch is `main` (if not, warn and stop)
2. Analyze stashed changes to infer a good branch name
3. Execute this single atomic command:

```bash
git checkout -b features/[branch-name] && git stash pop && git add -A && git commit -m "[message]" && git push -u origin features/[branch-name]
```

Use `required_permissions: ["all", "git_write", "network"]`

## Branch Naming
- Use kebab-case
- Be descriptive (e.g., `bugbot-type-fixes`, `anomaly-scoring-api`, `supplier-query-optimization`)

## Commit Message Format
```
<type>: <short description>

- Detail 1
- Detail 2
- Detail 3
```

Types: `feat`, `fix`, `refactor`, `chore`, `docs`

## Before Executing
Show brief summary:
```
📋 Branch: features/[name]
📝 [type]: [description]
⏱️ Executing...
```

Then execute immediately.

## If Error
Report exactly: `❌ [Command] failed: [error]. Run manually: [command]`
Do NOT retry automatically.
