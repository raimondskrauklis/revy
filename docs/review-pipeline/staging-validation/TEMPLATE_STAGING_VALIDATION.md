# docs/review-pipeline/staging-validation/TEMPLATE_STAGING_VALIDATION.md

# {{PROGRAM_TITLE}} — staging validation

**Program:** [README.md](./README.md) · **Baseline:** [{{FINDINGS_DOC}}](./{{FINDINGS_DOC}})

**Status:** *pending* — stub created {{DATE}}; fill on operator demand.

---

## Deploy boundaries

| Boundary | `--since` ISO | Used for |
|----------|---------------|----------|
| *(baseline)* | `{{DEPLOY_BASELINE_ISO}}` | initial metrics window |
| *(post-deploy)* | TBD | fill after next `main` deploy |

**Rule:** Use deploy job completion time, not merge time. See [staging-validation README](./README.md).

---

## Dogfood PR

| PR | Branch | Status |
|----|--------|--------|
| TBD | `chore/{{PROGRAM_SLUG}}-staging-dogfood` | not opened |

---

## Dogfood pushes

| Push | Intent | Status |
|------|--------|--------|
| 1 | Introduce probe / minimal `backend/**` touch | pending |
| 2 | Exercise primary pass criteria | pending |
| 3 | Cleanup / regrowth (if applicable) | pending |

---

## Pass criteria — push 2

| Check | Pass | Evidence |
|-------|------|----------|
| *(define from findings)* | pending | — |

---

## Pass criteria — push 3

| Check | Pass | Evidence |
|-------|------|----------|
| *(define from findings)* | pending | — |

---

## Results (operator)

| Push | `head_sha` | Notes |
|------|------------|-------|
| 1 | — | pending |

---

## Sign-off

| Check | Status | Evidence |
|-------|--------|----------|
| Staging PASS | pending | — |

**Next:** run metrics script with deploy `--since`; open dogfood PR; update rows on user demand via `staging-validation` skill.
