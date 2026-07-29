# Finding resolution — post-PSA dogfood

**Status:** **findings baseline** — gaps discovered during [PSA #63 dogfood](../publish-summary-alignment/PUBLISH_SUMMARY_ALIGNMENT_STAGING_VALIDATION.md); address in next validation PR(s).

**Thesis:** PSA #62 validated two-block publish shape; PR #63 exposed **resolution lifecycle** failures (G9 prose, stale groups, thread collapse) that need isolated dogfood with **one push per agent cycle**.

| Doc | Purpose |
|-----|---------|
| [FINDING_RESOLUTION_DOGFOOD_FINDINGS.md](./FINDING_RESOLUTION_DOGFOOD_FINDINGS.md) | Baseline — FR-DG* gaps, evidence, target PRs |
| *(later)* `FINDING_RESOLUTION_DOGFOOD_STAGING_VALIDATION.md` | Operator memo after deploy |
| *(later)* `waves/` execution | LOOP when general plan is written |

## Planned PRs

| PR branch | Gaps | Notes |
|-----------|------|-------|
| `chore/finding-resolution-staging-dogfood` | FR-DG1, FR-DG2 | Primary — backend resolution + publish |
| `chore/moonshot-formatter-signature` | MR-DG1 | Separate small PR — prompt/context only |

## Operator rules (from PSA #63)

1. **One push per agent cycle** — no back-to-back commits while Revy is running (rev 5 `skipped_not_head` broke resolution pairing).
2. **Deploy boundary** — `--since` = droplet deploy job completion, not merge time.
3. **Dogfood PR** — `chore/<program>-staging-dogfood`; minimal `backend/**` touch for autostart.

**Parent program:** [finding-resolution](../finding-resolution/README.md) (shipped P0–P5 on #57).

**Excluded from this track:** RCX retrieve changes, judge-json contract code — separate programs.
