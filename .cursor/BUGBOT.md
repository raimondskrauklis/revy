# Bugbot — review pipeline contract

**Active program:** keycloak-theme — Revy Keycloak login theme: dark phosphor-green child theme on `keycloak.v2`, directory theme (no JAR), `docker cp` apply, realm `loginTheme=revy`.

When reviewing **infra** changes for this program, treat these as authoritative:

- [KEYCLOAK_THEME_P0_EXECUTION.md](../docs/visual-identity/keycloak-theme/KEYCLOAK_THEME_P0_EXECUTION.md) — P0 inspector (read-only, review context)
- [KEYCLOAK_THEME_FINDINGS.md](../docs/visual-identity/keycloak-theme/KEYCLOAK_THEME_FINDINGS.md) — KC 26, keycloak.v2, dark tokens, decisions Q1–Q14
- [KEYCLOAK_THEME_GENERAL_PLAN.md](../docs/visual-identity/keycloak-theme/KEYCLOAK_THEME_GENERAL_PLAN.md) — P0–P3 goals and deliverables

**Agent workflow:**

- [agents/prompts/](../docs/review-pipeline/agents/prompts/) — VERB + OUTPUT_FORMAT
- [CURSOR_AGENT_WORKFLOW.md](../docs/utils/CURSOR_AGENT_WORKFLOW.md) — roles + verbs quick ref
- [agents/prompts/ROLES.md](../docs/review-pipeline/agents/prompts/ROLES.md) — master/reviewer boundaries