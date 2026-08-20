# docs/agents/findings/README.md

# Agent workflow findings

Living baselines for LOOP / review cadence. Not execution files. Add a new `*_FINDINGS.md` here when a workflow decision needs a durable record.

| File | Topic |
|:---|:---|
| [REVY_PUSH_CADENCE_FINDINGS.md](./REVY_PUSH_CADENCE_FINDINGS.md) | Fetch Revy before the next push; closeout WHILE is a second cycle |
| [REVY_PLATFORM_RULES_FINDINGS.md](./REVY_PLATFORM_RULES_FINDINGS.md) | Short rule packs on whole touched files; derive from `scope`, do not dump `.cursorrules` |
| [REVY_PRODUCT_RULE_PACKS_HANDOFF.md](./REVY_PRODUCT_RULE_PACKS_HANDOFF.md) | Attach in the Revy repo: load packs, whole-file prompt, do not auto-ingest `.cursorrules` |
