---
name: ship-changes
description: >-
  Ship finished work: Bugbot on uncommitted changes, feature branch if needed,
  commit, push, open PR. Use when the user says ship, commit and pr, push and
  open pr, or after an agent stopped with uncommitted fixes.
---

# Ship changes

**When:** work is done but not on GitHub — user says *ship*, *commit and pr*, *bugbot commit push*, or agent stopped mid-task.

**Config:** read `.agent/manifest.json` for `test_commands`, `integrations`, and active program `scope` (from `.revy/review-context.json` SSOT, mirrored in `.agent/review-context.json`).

**Not:** merge, deploy, or default-branch commits. **Not:** auto Greptile babysit.

---

## Steps

1. **Branch** — forbidden on `main` / `master` / default prod branch.
   - On forbidden branch → `git checkout -b feat/<short-topic>` (keep uncommitted work).
   - Else stay on current feature branch.
2. **Checks** — run lint/tests for touched areas per manifest `test_commands` and program `scope` (`backend/**`, `frontend/**`, or both).
   - Backend default: `pipenv run ruff check --fix .` then `pipenv run ruff check .` (no `--unsafe-fixes`).
3. **Local Bugbot** — invoke **`review-bugbot`** on `uncommitted changes` (or `branch changes`). Fix blockers; re-run checks. **Do not commit if blockers remain.** See [agents/ORCHESTRATION.md](../../docs/review-pipeline/agents/ORCHESTRATION.md).
4. **Commit** — `git add` relevant files; plain `git commit -m "…"` — **no** `--trailer`, **no** `Co-authored-by: Cursor`.
5. **Revy idle gate** — when `integrations.revy: true`, **never push while Revy is running.** See [Revy gate](#revy-gate-before-push).
6. **Push** — `git push -u origin HEAD` (first push) or `git push`.
7. **PR** — `gh pr view` or `gh pr list --head <branch> --json url`; if none:

```bash
gh pr create --title "<title per PR title pattern>" --body "$(cat <<'EOF'
## Summary
- …

## Test plan
- [ ] …

EOF
)"
```

Update existing PR title when scope grows: `gh pr edit <N> --title "…"`.

Skip step 7 if user said **no pr**.

**Greptile:** do **not** invoke `babysit-pr` unless user explicitly asks **and** `integrations.greptile: true`.

**Output:** branch, commit sha, PR URL (or compare URL if `gh pr create` failed).

---

## Revy gate (before push)

When `integrations.revy: true` in `.agent/manifest.json`:

```bash
gh pr checks <PR_NUMBER> 2>&1 | grep -iE 'revy|Revy'
# No PR yet (first push): skip gate — Revy runs after PR exists
```

| Revy check status | Action |
|-------------------|--------|
| `pending` / `in_progress` / `queued` | **Do not push.** Poll until settled. |
| `pass` / `fail` / `skipping` / `neutral` / no Revy row | Safe to push (if other gates green). |

After a push, Revy often returns to `pending` — **wait again** before the next push.

To re-trigger review after Revy is idle: empty commit (`git commit --allow-empty -m "chore: re-trigger Revy"`) then push once.

Fetch findings after Revy completes:

```bash
gh api repos/<owner>/<repo>/pulls/<PR>/comments --jq '.[] | select(.user.login|test("revy";"i"))'
gh pr view <PR> --comments
```

Fix actionable items; re-run local Bugbot; commit; **wait for Revy idle** before pushing fixes.

**Note:** If Revy GitHub App is suspended on this repo (no check row), gate is a no-op — still run local Bugbot.

---

## PR title pattern

Phase labels (`R0`–`R8`, `P0`–`P6`) are **LOOP commit labels**, not PR titles. PR titles describe **what shipped** for reviewers and release notes.

**Template:**

```text
<type>(<program-slug>): <primary outcome in plain English>
```

| Part | Rule | Example |
|------|------|---------|
| `type` | `feat`, `fix`, `docs`, `chore` | `feat` |
| `program-slug` | `active_program` from `.revy/review-context.json` | `revy-review-dogfood`, `review-quality` |
| outcome | Domains touched + user-visible result | `revision ingest idempotency and HEAD suppression` |

**Good:**

- `feat(revy-review-dogfood): R0–R3 ingest, publish hygiene, resolution stamp`
- `fix(review-quality): judge evidence extraction on large hunks (Revy)`

**Avoid:** `R3 Wave B` (phase-only, no outcome).

**Batched multi-phase PR:**

```text
feat(revy-review-dogfood): ingest, thread resolve taxonomy, staging validation
```

Set title on first `gh pr create`; refresh after major phase batches with `gh pr edit`.
