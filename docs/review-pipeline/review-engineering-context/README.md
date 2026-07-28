# Review engineering context — program index

**Status:** General plan ready — `create-execution-plan` next.

**Problem:** Revy Moonshot (`prepare_review_context`) has no engineering-context layer — only diff + RAG. Greptile has partial wiring via `.greptile/files.json` but loads every shipped program. **P0 = Revy inject**; Greptile parallel; Bugbot maintained in daily workflow but not P0 build.

| Doc | Purpose |
|-----|---------|
| [REVIEW_ENGINEERING_CONTEXT_FINDINGS.md](./REVIEW_ENGINEERING_CONTEXT_FINDINGS.md) | Baseline — platform view, RCX-D8 Moonshot inject, manifest, deliverables |
| [REVIEW_ENGINEERING_CONTEXT_GENERAL_PLAN.md](./REVIEW_ENGINEERING_CONTEXT_GENERAL_PLAN.md) | Phases P0–P5 — manifest, inject, metrics migration `0029`, validation |

**Authority:** [REVIEW_QUALITY_REVIEW_CONTEXT.md](../review-quality/REVIEW_QUALITY_REVIEW_CONTEXT.md) (RC0–RC6) · [REVIEW_PIPELINE_PRODUCT_PATTERNS.md](../REVIEW_PIPELINE_PRODUCT_PATTERNS.md)

**Related programs**

| Program | Link |
|---------|------|
| Review quality (RC track) | [review-quality/README.md](../review-quality/README.md) |
| Structural context (sibling) | [REVIEW_QUALITY_STRUCTURAL_CONTEXT.md](../review-quality/REVIEW_QUALITY_STRUCTURAL_CONTEXT.md) |
| Judge JSON contract (shipped) | [judge-json-contract/README.md](../judge-json-contract/README.md) |

**Next step:** `create-execution-plan` → P0 execution file (migration `0029`, caps, manifest schema).
