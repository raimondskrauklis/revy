# Local Bugbot — agent docs slice (RC-D16/D17, ROLES, VALIDATE)

**Date:** 2026-07-27 · **Diff:** doc-only (ROLES, babysit, OUTPUT_FORMAT, DOGFOOD RC-D17)  
**Operator:** master spawned Bugbot pass 1 FIND + pass 2 CLOSE on uncommitted changes.

## Pass 1 findings (fixed)

| Sev | Location | Finding | Action |
|-----|----------|---------|--------|
| high | PROMPTS.md babysit | Still said generic Pass 1 FIND | → VALIDATE |
| medium | DOGFOOD archive link | Stale `#greptile-babysit-shallow-fix` anchor | → new heading anchor |
| medium | babysit-pr.md | No fix-between-passes / push guard | → steps 6–8 split |
| medium | OUTPUT_FORMAT | VALIDATE scope note required RQn | → FIND vs VALIDATE sections |
| low | OUTPUT_FORMAT shell | Contradicted PROMPTS brief | → aligned VERB shell |

## Pass 2

| Prior | Status |
|-------|--------|
| Pass 1 items | CLOSED |
| New: babysit omit re-CLOSE loop | fixed in command + skill |

## Deferred

| Sev | Topic | Why deferred |
|-----|-------|--------------|
| — | Full UI thinking trace | Export from Cursor UI to `local_bugbot_from_ui_*.txt` if needed; subagent returns findings table only |

## Note

Subagent does not auto-archive CoT. Distill rows here; link [ui_3](./local_bugbot_from_ui_3.txt) / [ui_4](./local_bugbot_from_ui_4.txt) for RC-D17 flush/rollback evidence.
