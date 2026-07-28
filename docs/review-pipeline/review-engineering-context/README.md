# Review engineering context — program index

**Status:** **findings only** — [judge-json-contract](../judge-json-contract/README.md) merged (#58); next: `create-general-plan` from findings.

**Problem:** Greptile and Bugbot get execution + findings via RC0 wiring; **revybot** does not — contract drift and false positives on program PRs (PR #58: `format.name`, P3 lock).

| Doc | Purpose |
|-----|---------|
| [REVIEW_ENGINEERING_CONTEXT_FINDINGS.md](./REVIEW_ENGINEERING_CONTEXT_FINDINGS.md) | Baseline — where we are, RCX gaps, locked decisions |

**Authority:** [REVIEW_QUALITY_REVIEW_CONTEXT.md](../review-quality/REVIEW_QUALITY_REVIEW_CONTEXT.md) (RC0–RC6) · [REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md](../REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md)

**Related programs**

| Program | Link |
|---------|------|
| Review quality (RC track) | [review-quality/README.md](../review-quality/README.md) |
| Judge JSON contract (active) | [judge-json-contract/README.md](../judge-json-contract/README.md) |

**Next step:** `create-general-plan` from findings; wire revybot engineering context (RCX program).
