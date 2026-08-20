# .revy/rules/README.md

# Revy platform rule packs

Short, checkable principles for PR review. Not `.cursorrules` (that file is agent chat + LOOP). Revy reviews **whole files the diff touches**; these packs are what it checks against.

| Id | File | When |
|:---|:---|:---|
| `platform` | [platform.md](./platform.md) | Any program whose `scope` includes `backend/**` or `frontend/**` |
| `backend` | [backend.md](./backend.md) | `scope` includes `backend/**` |
| `frontend` | [frontend.md](./frontend.md) | `scope` includes `frontend/**` |

**Include:** P0.0 writes `programs[].rule_packs` from `scope`. Do not ask in chat. Docs/corpus-only scope → `[]`.

**Catalog:** `.revy/review-context.json` → `rule_packs_catalog`. Consumer findings: [REVY_PLATFORM_RULES_FINDINGS.md](../../docs/agents/findings/REVY_PLATFORM_RULES_FINDINGS.md). Product handoff: [REVY_PRODUCT_RULE_PACKS_HANDOFF.md](../../docs/agents/findings/REVY_PRODUCT_RULE_PACKS_HANDOFF.md).
