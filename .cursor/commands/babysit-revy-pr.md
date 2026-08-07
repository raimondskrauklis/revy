# Babysit Revy PR (poll → fix → Bugbot → push → loop)

**On demand.** User invokes `/babysit-revy-pr` with an optional PR number or URL. Default: current branch’s open PR.

Skill: `.cursor/skills/babysit-revy-pr/SKILL.md`

## Loop (until all Revy findings solved)

1. **Resolve PR** — `gh pr view` on current branch, or parse user’s PR # / URL.
2. **Poll Revy idle** — `gh pr checks <PR> | grep Revy`; while `pending`/`in_progress`/`queued`, **sleep 120s** and poll again.
3. **Fetch Revy comments** — GraphQL `reviewThreads` or REST `pulls/{n}/comments` where `author.login` matches `revy` / `revybot`; include issue comments from `revybot[bot]`.
4. **Triage** — Fix valid findings; skip false positives (say why). Ignore resolved/outdated threads.
5. **Checks** — if `backend/` Python touched: ruff + targeted pytest.
6. **Local Bugbot** — `review-bugbot` on uncommitted changes until clean.
7. **Commit + push** — feature branch only; never push while Revy is running.
8. **Repeat** from step 2 until no actionable open Revy findings and Revy is idle.

## Output

Table: Severity | Location | Finding | Action. Final: PR URL, commit sha, Revy status.

If nothing open after idle: say so — no empty commit unless re-triggering Revy.
