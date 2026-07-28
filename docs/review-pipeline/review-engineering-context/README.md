# Review engineering context — program index

**Status:** Platform scope locked — ready for `create-general-plan`.

**Problem:** Revy Moonshot (`prepare_review_context`) has no engineering-context layer — only diff + RAG. Greptile has partial wiring via `.greptile/files.json` but loads every shipped program. **P0 = Revy inject**; Greptile parallel; Bugbot maintained in daily workflow but not P0 build.

| Doc | Purpose |
|-----|---------|
| [REVIEW_ENGINEERING_CONTEXT_FINDINGS.md](./REVIEW_ENGINEERING_CONTEXT_FINDINGS.md) | Baseline — platform view, RCX-D8 Moonshot inject, manifest, deliverables |

**Authority:** [REVIEW_QUALITY_REVIEW_CONTEXT.md](../review-quality/REVIEW_QUALITY_REVIEW_CONTEXT.md) (RC0–RC6) · [REVIEW_PIPELINE_PRODUCT_PATTERNS.md](../REVIEW_PIPELINE_PRODUCT_PATTERNS.md)

**Related programs**

| Program | Link |
|---------|------|
| Review quality (RC track) | [review-quality/README.md](../review-quality/README.md) |
| Structural context (sibling) | [REVIEW_QUALITY_STRUCTURAL_CONTEXT.md](../review-quality/REVIEW_QUALITY_STRUCTURAL_CONTEXT.md) |
| Judge JSON contract (shipped) | [judge-json-contract/README.md](../judge-json-contract/README.md) |

**Next step:** `create-general-plan` → RCX P0: manifest + `prepare_review_context` inject + Greptile sync.
