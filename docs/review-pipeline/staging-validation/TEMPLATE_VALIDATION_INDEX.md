# docs/review-pipeline/staging-validation/TEMPLATE_VALIDATION_INDEX.md

# Staging validation index

**Status:** operator index — active dogfood PRs and per-program validation memos.

| Doc | Purpose |
|-----|---------|
| [STAGING_VALIDATION_FINDINGS.md](./STAGING_VALIDATION_FINDINGS.md) | Meta workflow baseline (optional) |

## Active dogfood PRs

| PR | Program | Branch | Status |
|----|---------|--------|--------|
| TBD | *(program)* | `chore/*-staging-dogfood` | — |

## Per-program validation memos

| Program | Memo |
|---------|------|
| *(program)* | [*PROGRAM*_STAGING_VALIDATION.md](../path/to/memo.md) |

## Shared tooling

| Tool | Path |
|------|------|
| *(metrics script)* | `backend/scripts/…` |

**Operator loop:** deploy `main` → record deploy boundary ISO → open chore dogfood PR → run scripts → fill memo via `staging-validation` skill.
