# Bugbot — review pipeline contract

**Active program:** model-run-capture — durable per-run model identity (embeddings, reviewer, judge, publish).

When reviewing **backend** changes for model run capture, treat these as authoritative:

- [MODEL_RUN_CAPTURE_P0_EXECUTION.md](../docs/models/model-run-capture/waves/MODEL_RUN_CAPTURE_P0_EXECUTION.md) — MRC-P0 LOOP (index manifest + step model)
- [MODEL_RUN_CAPTURE_FINDINGS.md](../docs/models/model-run-capture/MODEL_RUN_CAPTURE_FINDINGS.md) — MRC-Q1–Q10, target catalog
- [MODEL_RUN_CAPTURE_GENERAL_PLAN.md](../docs/models/model-run-capture/MODEL_RUN_CAPTURE_GENERAL_PLAN.md) — MRC-P0–P3 goals

**Agent workflow:**

- [agents/prompts/](../docs/review-pipeline/agents/prompts/) — VERB + OUTPUT_FORMAT
- [CURSOR_AGENT_WORKFLOW.md](../docs/utils/CURSOR_AGENT_WORKFLOW.md) — roles + verbs quick ref
- [agents/prompts/ROLES.md](../docs/review-pipeline/agents/prompts/ROLES.md) — master/reviewer boundaries
