# Commit and Push Changes

**Context:** User is on a feature branch, wants to commit current changes

## Your Task

1. Check current branch is NOT `main` (if on main, warn: "Use /commit-new to create feature branch first")
2. Analyze changes to generate commit message
3. Execute:

```bash
git add -A && git commit -m "[message]" && git push
```

Use `required_permissions: ["all", "git_write", "network"]`

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
📋 Branch: [current-branch]
📝 [type]: [description]
⏱️ Executing...
```

Then execute immediately.

## If Error
Report exactly: `❌ [Command] failed: [error]. Run manually: [command]`
Do NOT retry automatically.
