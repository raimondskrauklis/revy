# Review engineering context — program index

**Status:** Peer-reviewed general plan — `create-execution-plan` next.

**Problem:** Revy Moonshot has no engineering-context layer. Greptile loads 15 programs from `files.json`. **RCX P2** = Moonshot inject; **P3** = Greptile generated from SSOT; Bugbot manual.

| Doc | Purpose |
|-----|---------|
| [REVIEW_ENGINEERING_CONTEXT_FINDINGS.md](./REVIEW_ENGINEERING_CONTEXT_FINDINGS.md) | Baseline — RCX-D1–D12, validation metrics, peer-review aligned deliverables |
| [REVIEW_ENGINEERING_CONTEXT_GENERAL_PLAN.md](./REVIEW_ENGINEERING_CONTEXT_GENERAL_PLAN.md) | **Execution authority** — P0–P5 |

**Phase map (authority = general plan)**

| Phase | Focus |
|-------|--------|
| P0 | SSOT schema, migration `0029`, caps default 512 KB, manifest key contract |
| P1 | Extractor + `fetch_repository_file_at_sha` |
| P2 | Moonshot inject + populate metrics |
| P3 | Greptile `files.json` generation + active program trim |
| P4 | Judge lock reuse |
| P5 | Staging validation (requires dogfood PR) |

**Supersedes:** [RQ-RC-1](../review-quality/REVIEW_QUALITY_REVIEW_CONTEXT.md) dogfood items (RC1, RC2, RC5 inject) — folded into RCX.

**Related:** [review-quality/README.md](../review-quality/README.md) · [judge-json-contract](../judge-json-contract/README.md)

**Next step:** `create-execution-plan` → P0 execution file.
