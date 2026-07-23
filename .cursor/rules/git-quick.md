# Git Workflow Commands

## Overview

Three commands for git operations. Agent generates commit messages based on context.

**Shell reality:** Each command takes ~70-80s due to Cursor overhead. Chaining saves multiple invocations.

---

## Command 1: "commit new"

**When:** Starting new feature from main branch (user has run `git stash` manually)

**Agent does:**
1. Infer branch name from stashed changes context
2. Execute single git operation:

```bash
git checkout -b features/[branch-name] && git stash pop && git add -A && git commit -m "[message]" && git push -u origin features/[branch-name]
```

**Permissions:** `["all", "git_write", "network"]`

**Branch naming:** kebab-case, descriptive (e.g., `bugbot-type-fixes`, `anomaly-scoring-api`)

---

## Command 2: "commit" or "commit and push"

**When:** On feature branch, regular commits

**Agent does:**
1. Generate commit message from recent changes
2. Execute:

```bash
git add -A && git commit -m "[message]" && git push
```

**Safety:** If on `main`, stop and tell user: "You're on main. Use 'commit new' first."

---

## Command 3: "solve and commit" or "fix and commit"

**When:** User pastes BugBot errors, linting errors, or any issues to fix

**Agent does:**
1. **Fix the issues** in code first
2. Generate commit message describing fixes
3. Execute:

```bash
git add -A && git commit -m "[message]" && git push
```

This is the BugBot loop command - fix what's broken, commit, push, repeat.

---

## Commit Message Format

```
<type>: <short description>

- Detail 1 (file:line if relevant)
- Detail 2
- Detail 3
```

**Types:**
- `fix` - bug fixes, BugBot issues, errors
- `feat` - new features
- `refactor` - code restructuring
- `chore` - maintenance, deps
- `docs` - documentation

### BugBot Fix Example:
```
fix: address BugBot type safety issues

- Add null checks in supplier query (services/supplier.py:45)
- Correct return type in scoring function (services/anomaly.py:78)
- Remove unused imports in procurement routes
```

### Feature Example:
```
feat: implement supplier anomaly scoring

- Add scoring algorithm in backend/app/services/anomaly.py
- Create POST /api/anomaly/score endpoint
- Add AnomalyScoreCard frontend component
```

---

## Before Executing

Show brief summary:

```
📋 Branch: features/bugbot-type-fixes
📝 fix: address BugBot type safety issues
   - Fix 1
   - Fix 2
⏱️ Executing...
```

Then execute immediately (no wait for approval unless user says "wait").

---

## Error Handling

If git fails:
```
❌ Push failed: [error message]
Run manually: [exact command]
```

Do NOT retry. Do NOT workaround. Tell user what to run.

---

## Context: KP Platform

- **Backend:** FastAPI, SQLAlchemy async, Alembic, Pydantic
- **Frontend:** React 19, TypeScript strict, Vite
- **Services:** `backend/app/services/`
- **Routes:** `backend/app/routes/`
- **Components:** `frontend/src/components/`

Use for accurate, specific commit messages.

---

## User's Manual Tasks (Agent Does NOT Do)

- `git stash` before "commit new"
- Delete branch after PR merge
- `git checkout main && git pull --rebase`
- Resolve merge conflicts

---

## Summary

| Command | Creates Branch | Fixes Code | Commits |
|---------|----------------|------------|---------|
| commit new | ✅ | ❌ | ✅ |
| commit | ❌ | ❌ | ✅ |
| solve and commit | ❌ | ✅ | ✅ |
