---
name: ship-changes
description: >-
  Ship finished work: Bugbot on uncommitted changes, feature branch if needed,
  commit, push, open PR. Use when the user says ship, commit and pr, push and
  open pr, or after an agent stopped with uncommitted fixes.
---

# Ship changes

**When:** work is done but not on GitHub — user says *ship*, *commit and pr*, *bugbot commit push*, or agent stopped mid-task.

**Not:** merge, deploy, or `main`/`master` commits.

---

## Steps

1. **Branch** — forbidden on `main` / `master` / default prod branch.
   - On forbidden branch → `git checkout -b feat/<short-topic>` (keep uncommitted work).
   - Else stay on current feature branch.
2. **Checks** — run tests for touched areas; if `backend/` Python changed: `pipenv run ruff check --fix .` then `pipenv run ruff check .` (no `--unsafe-fixes`).
3. **Local Bugbot** — invoke **`review-bugbot`** on `uncommitted changes` (or `branch changes`). Fix blockers; re-run checks. **Do not commit if blockers remain.** See [agent orchestration](../../docs/review-pipeline/review-quality/REVIEW_QUALITY_AGENT_ORCHESTRATION.md).
4. **Commit** — `git add` relevant files; plain `git commit -m "…"` — **no** `--trailer`, **no** `Co-authored-by: Cursor`.
5. **Push** — `git push -u origin HEAD` (first push) or `git push`.
6. **PR** — `gh pr view` or `gh pr list --head <branch> --json url`; if none:

```bash
gh pr create --title "<short title>" --body "$(cat <<'EOF'
## Summary
- …

## Test plan
- [ ] …

EOF
)"
```

Skip step 6 if user said **no pr**. After PR is open, **`babysit-pr`** for Greptile threads — then **local Bugbot again** before any fix push.

**Output:** branch, commit sha, PR URL (or compare URL if `gh pr create` failed).
