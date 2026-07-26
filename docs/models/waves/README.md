# Model policy — execution index

Linear **phase-execution** order. General plan: [`../MODEL_POLICY_GENERAL_PLAN.md`](../MODEL_POLICY_GENERAL_PLAN.md).

**Authority:** [`../MODEL_POLICY_FINDINGS.md`](../MODEL_POLICY_FINDINGS.md), [`../../utils/GITHUB_APP_TARGET_CONFIG.md`](../../utils/GITHUB_APP_TARGET_CONFIG.md), [`../../saas-base/SETTINGS_IA.md`](../../saas-base/SETTINGS_IA.md), `internal-docs/product/revy/docs/architecture.md` §11.3, §13–14.

| Phase | File | Status |
|-------|------|--------|
| M0 — Model role foundations | [MODEL_POLICY_M0_EXECUTION.md](./MODEL_POLICY_M0_EXECUTION.md) | done (`22c35ab`) |
| M1 — AWS Bedrock LLM provider | [MODEL_POLICY_M1_EXECUTION.md](./MODEL_POLICY_M1_EXECUTION.md) | done (`91fe16a`) |
| M2 — Workspace model policy (API) | [MODEL_POLICY_M2_EXECUTION.md](./MODEL_POLICY_M2_EXECUTION.md) | done (`4fededb`) |
| M3 — Review settings UI | [MODEL_POLICY_M3_EXECUTION.md](./MODEL_POLICY_M3_EXECUTION.md) | done (pending commit) |

**LOOP order:** M0 → M1 → M2 → M3 (strict — each phase depends on prior).

**Pre-flight:** General plan locked decisions MP-D1–MP-D15; findings baseline 2026-07-26; execution peer-reviewed 2026-07-26.
