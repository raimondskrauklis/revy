// docs/visual-identity/keycloak-theme/KEYCLOAK_THEME_P0_EXECUTION.md

# P0 — Inspector (execution)

Phase **P0** of [`KEYCLOAK_THEME_GENERAL_PLAN.md`](./KEYCLOAK_THEME_GENERAL_PLAN.md). Baseline: [`KEYCLOAK_THEME_FINDINGS.md`](./KEYCLOAK_THEME_FINDINGS.md) Q1–Q13. **P0 only — read-only.**

**Goal:** Know the running server so parent theme, apply method, and rollback values cannot be wrong.

## Decisions locked for P0
- Q1–Q13 already locked in findings. Nothing to re-decide.
- Q12 `defaultLocale` and Q14 who applies are **open** — P0 closes them by inspecting the live realm and asking ops.

## PR review context (required when code + docs ship in one PR)
- **SSOT (Moonshot inject):** `.revy/review-context.json` — set `active_program: "keycloak-theme"`; `programs[]` = one entry: `scope: ["infra/keycloak/**"], doc paths: [KEYCLOAK_THEME_P0_EXECUTION.md, KEYCLOAK_THEME_FINDINGS.md, KEYCLOAK_THEME_GENERAL_PLAN.md]`
- **Bugbot:** `.cursor/BUGBOT.md` — active program `keycloak-theme` + links to same three docs
- **Agent mirror:** copy `.revy/review-context.json` → `.agent/review-context.json`
- **Do not** wire Greptile (`integrations.greptile: false`)

## Out of scope for P0 (later phases)
- Theme CSS, messages, `infra/keycloak/` tree → **P1**
- rsync, `docker cp`, realm cutover, production restart → **P2**
- Dockerfile bake, compose sync → **P3**

---

## P0.1 — Program PR review context (SSOT + Bugbot)

**What:** Switch the review tooling to `keycloak-theme`. Update `.revy/review-context.json` — `active_program: "keycloak-theme"`, `scope: ["infra/keycloak/**"]` (infra dir is created in P1; scope covers it from the start), doc paths to the three plan docs. Update `.cursor/BUGBOT.md` — active program + links to same docs. Mirror to `.agent/review-context.json`.

**Files:** `.revy/review-context.json`, `.cursor/BUGBOT.md`, `.agent/review-context.json`

**Deliverable:** `python -m json.tool .revy/review-context.json > /dev/null` — valid JSON; `active_program` reads `keycloak-theme`; `scope` is `["infra/keycloak/**"]`. `diff .revy/review-context.json .agent/review-context.json` exits 0.

---

## P0.2 — Inspect production Keycloak container

**What:** SSH to droplet. Run `docker inspect revy-kc`, `docker exec revy-kc /opt/keycloak/bin/kc.sh --version`, `docker exec revy-kc ls -la /opt/keycloak/themes /opt/keycloak/data/tmp`. Record in a redacted artifact file: image digest, `Cmd`, `Entrypoint`, `User`, `Mounts`, `RestartPolicy`, `PortBindings`, `NetworkMode`, Env **key names only** (never values). Determine deploy user (`id`) and docker GID from `deploy.yml` SSH actions or droplet `id`.

**Files:** New — `docs/visual-identity/keycloak-theme/P0_INSPECT.md` (redacted, no secrets)

**Deliverable:** `P0_INSPECT.md` exists; contains version, writability, session persistence config, deploy user, docker GID; no Env values present.

---

## P0.3 — Record realm state

**What:** Via Keycloak Admin UI (`auth.revy.createit.digital/admin` → realm `revy`), record: `loginTheme` (current — **rollback value**), `internationalizationEnabled`, `supportedLocales`, `defaultLocale`, `registrationAllowed`, `resetPasswordAllowed`, `rememberMe`, `loginWithEmailAllowed`. Confirm `keycloak.v2` appears in the theme dropdown.

**Files:** Append to `P0_INSPECT.md`

**Deliverable:** Realm state recorded; Q12 `defaultLocale` resolved; rollback value known.

---

## P0.4 — Test stylesCommon inheritance locally

**What:** Create a minimal throwaway directory theme (`parent=keycloak.v2`, `styles=css/test.css`, empty CSS file, `darkMode=false`), mount into a local `start-dev` Keycloak 26.0, and confirm PatternFly `stylesCommon` CSS still loads on the login page. Use a one-liner docker run: `docker run --rm -p 8080:8080 -v $(pwd)/test-theme:/opt/keycloak/themes/test-theme -e KC_BOOTSTRAP_ADMIN_USERNAME=admin -e KC_BOOTSTRAP_ADMIN_PASSWORD=admin quay.io/keycloak/keycloak:26.0 start-dev`. Open browser dev tools on `http://localhost:8080/realms/master/account` — check network tab for PF CSS files loading. If inherit breaks, the P1 `theme.properties` must include `stylesCommon` explicitly. Record result.

**Files:** Scratch — not committed. Result appended to `P0_INSPECT.md`.

**Deliverable:** `stylesCommon` behavior documented (inherits automatically or must be explicit); P1 can proceed without guessing.

---

**Phase gate** (no pytest/Vitest — manual verification):

- `P0_INSPECT.md` exists and contains: KC version, writability, session config, realm state, `stylesCommon` result, deploy user + docker GID.
- No Env values present (grep `passwords`: only key names).
- Q12 `defaultLocale` is not `TBD`.
- Q14 answered (operator script or CI workflow).

**Deploy:** none — read-only. No container changes.

**Next:** [`KEYCLOAK_THEME_P1_EXECUTION.md`](./KEYCLOAK_THEME_P1_EXECUTION.md) — theme package + local loop.
