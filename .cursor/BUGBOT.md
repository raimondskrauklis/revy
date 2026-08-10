# Bugbot — review pipeline contract

**Active program:** pipeline-observability — durable LLM attempt rows, commit graph, staging metrics.

When reviewing **backend** changes for pipeline observability, treat these as authoritative:

- [PIPELINE_OBSERVABILITY_P1_EXECUTION.md](../docs/review-pipeline/pipeline-observability/waves/PIPELINE_OBSERVABILITY_P1_EXECUTION.md) — P1 LOOP (Moonshot, Anthropic judge, Voyage instrumentation)
- [PIPELINE_OBSERVABILITY_FINDINGS.md](../docs/review-pipeline/pipeline-observability/PIPELINE_OBSERVABILITY_FINDINGS.md) — PO-Q1–Q19, commit graph, metric catalog
- [PIPELINE_OBSERVABILITY_GENERAL_PLAN.md](../docs/review-pipeline/pipeline-observability/PIPELINE_OBSERVABILITY_GENERAL_PLAN.md) — P0–P5 goals
- [PIPELINE_OBSERVABILITY_P0_EXECUTION.md](../docs/review-pipeline/pipeline-observability/waves/PIPELINE_OBSERVABILITY_P0_EXECUTION.md) — P0 shipped reference (schema, recorder, checkpoint)

**Agent workflow:**

- [agents/prompts/](../docs/review-pipeline/agents/prompts/) — VERB + OUTPUT_FORMAT
- [CURSOR_AGENT_WORKFLOW.md](../docs/utils/CURSOR_AGENT_WORKFLOW.md) — roles + verbs quick ref
- [agents/prompts/ROLES.md](../docs/review-pipeline/agents/prompts/ROLES.md) — master/reviewer boundaries
