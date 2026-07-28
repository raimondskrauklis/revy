# Review engineering context — program index

**Status:** **findings expanded** (2026-07-29) — discuss → `create-general-plan`.

**Problem:** Engineering context (locked decisions, execution contract, operator smoke) is wired for Greptile + local Bugbot only. **Hosted `revybot[bot]`** and the **Revy product pipeline** (Moonshot/judge) lack the same intent layer → false positives and generic API advice (PR #58).

| Doc | Purpose |
|-----|---------|
| [REVIEW_ENGINEERING_CONTEXT_FINDINGS.md](./REVIEW_ENGINEERING_CONTEXT_FINDINGS.md) | Baseline — reviewer channels, context layers, industry patterns, RCX gaps |

**Authority:** [REVIEW_QUALITY_REVIEW_CONTEXT.md](../review-quality/REVIEW_QUALITY_REVIEW_CONTEXT.md) (RC0–RC6) · [REVIEW_PIPELINE_PRODUCT_PATTERNS.md](../REVIEW_PIPELINE_PRODUCT_PATTERNS.md)

**Related programs**

| Program | Link |
|---------|------|
| Review quality (RC track) | [review-quality/README.md](../review-quality/README.md) |
| Structural context (sibling) | [REVIEW_QUALITY_STRUCTURAL_CONTEXT.md](../review-quality/REVIEW_QUALITY_STRUCTURAL_CONTEXT.md) |
| Judge JSON contract (shipped) | [judge-json-contract/README.md](../judge-json-contract/README.md) |

**Next step:** Discuss findings → `create-general-plan` → dogfood manifest (RCX-G1) before RC4 product DB.
