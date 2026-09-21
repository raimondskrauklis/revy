# docs/visual-identity/keycloak-theme/KEYCLOAK_THEME_GENERAL_PLAN.md

# Keycloak login theme — general plan

**Purpose:** Ship a `revy` Keycloak **login** theme that continues the dark phosphor-green operator console (`--app-*` tokens from `tokens.revy.css`) on `auth.revy.createit.digital`, without recreating the live `revy-kc` container or hitchhiking on app deploys.

**Inputs:** [KEYCLOAK_THEME_FINDINGS.md](KEYCLOAK_THEME_FINDINGS.md) — Q1–Q13 locked.  
**Out of scope:** SPA React, JWT/RBAC, admin/account/email themes, Keycloak version upgrade, bind-mounting into the live container (deferred C6).

---

## Plan-level decisions (locked)

| ID | Resolution |
|:---|:---|
| Q1 | Parent `keycloak.v2` (KC 26.0) |
| Q2 | Always dark; copy resolved hex from `tokens.revy.css` `html.dark` L63–106 |
| Q3 | Theme type `login` only |
| Q4 | First apply: rsync → block storage → `docker cp` into `revy-kc`; no recreate |
| Q5 | Not part of `deploy-production`; gated workflow or operator script |
| Q6 | Realm `revy` → `loginTheme=revy`; rollback = recorded current value |
| Q7 | No copied FTL |
| Q8 | Resolved `--app-*` hex verbatim from `tokens.revy.css` L63–106; `--app-radius-md` (4px) same in both modes — copy value directly |
| Q9 | EN+LV branding overrides; remainder inherit KC bundles |
| Q10 | Block storage `/mnt/revy_volume/keycloak-themes/` as on-box source |
| Q11 | Theme home `infra/keycloak/` |
| Q12 | Realm i18n `en,lv` on |
| Q13 | No runtime bind-mount in v1 |

**Open (must close before the named phase):** Q12 `defaultLocale` `lv`/`en` (before P2 — ask ops). Q14 who runs the apply — operator or CI (before P2; default: operator script, workflow optional).

---

## Cross-cutting (every phase)

i18n **EN+LV** on user-visible Keycloak strings we override; realm i18n is a P2 deliverable, not an assumption. Visual QA is the verification (375px included) plus `infra/keycloak/scripts/check_theme.sh` (B7 — allows hex from verbatim token block + documented layout hex list) — no pytest/Vitest, no API smoke. **No Keycloak secrets in git** (inspect redacts Env values to key names only). **No production restart before the local loop (C0) passes.** Local Bugbot before every push.

**Push strategy:** P0 local → **P1 first push** (opens PR) → P2 local → P3 push. PR title `feat(keycloak-theme): <what shipped>`. No Revy PR loop needed (no backend/frontend changes).

---

## P0 — Inspector (read-only)

**Goal:** Know the running server so parent theme, apply method, and rollback values cannot be wrong.

**Scope:** `docker inspect revy-kc` → redacted artifact (image digest, `Cmd`, `Entrypoint`, `User`, `Mounts`, `RestartPolicy`, `PortBindings`, `NetworkMode`, Env **key names only** — never values). `docker exec revy-kc /opt/keycloak/bin/kc.sh --version`; `docker exec revy-kc ls -la /opt/keycloak/themes /opt/keycloak/data/tmp`. Determine deploy user and docker GID from `deploy.yml` SSH actions or droplet `id`. Record session persistence config (Infinispan vs DB sessions). Realm `revy` via Admin UI: `loginTheme` (**rollback value**), `internationalizationEnabled`, `supportedLocales`, `defaultLocale`, `registrationAllowed`, `resetPasswordAllowed`, `rememberMe`, `loginWithEmailAllowed`; confirm `keycloak.v2` in the theme dropdown. **In:** one redacted inspect artifact in this folder. **Out:** theme CSS, restart, realm change, any file copy into the container.

**Deliverables:** Version + start-mode + writability + realm state + session persistence recorded (redacted); Q12 `defaultLocale` closed; rollback value known; KC version confirmed `26.0`; deploy user and docker GID resolved; `stylesCommon` inheritance behavior tested locally with a minimal child theme. Q14 resolved (ask or default to operator).

**Depends on:** nothing.

---

## P1 — Theme package + local loop

**Goal:** A git directory theme that looks like the dark phosphor-green console, proven on a local Keycloak `26.0` before production is touched.

**Scope:** Create `infra/keycloak/` tree: `themes/revy/login/` (`theme.properties` — `parent=keycloak.v2`, `styles=css/revy-login.css`, `darkMode=false`; no `stylesCommon` unless P0 test proves inherit is broken; `resources/css/revy-login.css` owning the **full** layout with the verbatim token block from `tokens.revy.css` `html.dark` L63–106; hex in KC class overrides must come from the token block or a documented layout hex list; comment notes `--app-radius-md` is 4px in both light and dark; `messages/messages_en.properties` + `messages_lv.properties`), `docker-compose.yml` (`quay.io/keycloak/keycloak:26.0`, `start-dev`, `./themes:/opt/keycloak/themes`, theme caches off), `.env.example`, `scripts/check_theme.sh` (B7 — allows hex from token block + documented layout hex list). Local realm `revy` with `loginTheme=revy`; visual QA of login / forgot / error / info in EN+LV at 375px and desktop. Register QA only if P0 shows `registrationAllowed=true`; otherwise it's a known no-op. **Out:** Dockerfile bake, deploy workflow, FTL clones, `scripts=` JS (only if C0 proves `darkMode=false` insufficient — then record why), admin/email themes.

**Deliverables:** Theme files in repo; `check_theme.sh` green; local screenshots pass the findings verification list (canvas `#07140c`, no PF geometry, no blue stripe, CTA `#a8dc84` on `#07140c`); **first push**.

**Depends on:** P0 (parent + tag confirmed).

---

## P2 — Transport, apply, realm cutover

**Goal:** The theme is on production `revy-kc`, the realm is switched, and users who click "Get Started" land on Revy-branded login in their language.

**Scope:** Create `/mnt/revy_volume/keycloak-themes/` once (owner and GID from P0: `install -d -m 0755 -o <deploy-user-from-P0> -g <docker-gid-from-P0>`). Transport: `rsync -az --delete infra/keycloak/themes/revy/ <host>:/mnt/revy_volume/keycloak-themes/revy/`. Apply script (runs on the box): C1b backup of current container copy if exists → C1c `docker cp` → C2 gzip-cache delete → **one** `docker restart revy-kc` (session impact per P0; brief blip accepted if Infinispan-only) → wait for `:8080` → print theme dropdown check hint. Realm `revy`: `internationalizationEnabled=true`, `supportedLocales=[en,lv]`, `defaultLocale` per Q12, then `loginTheme=revy`. Exercise production login-type pages: login, forgot → info, error (bad `redirect_uri`); register if `registrationAllowed` per P0 (otherwise no-op); EN+LV via switcher; 375px; password toggle; OIDC callback to the SPA; admin console still stock. **Rollback:** `loginTheme` ← P0 value (instant). **Out:** client/redirect/secret changes; registration/reset **policy** changes.

**Deliverables:** Theme present in `revy-kc:/opt/keycloak/themes/revy`; Keycloak back on `:8080` after one restart; `revy` visible in Admin theme dropdown; `.prev-<ts>` backup exists if prior copy did; production login-type pages pass the findings verification list; rollback value and command documented in this folder; push (if CI workflow was created in P1).

**Depends on:** P1; Q12 `defaultLocale` answered; Q14 apply decision.

---

## P3 — Bake + docker-compose sync (optional, deferred)

**Goal:** The same theme is repeatable without tribal `docker cp`, and the deploy compose can bake it in.

**Scope:** `infra/keycloak/Dockerfile` — **separate file** from `deploy/keycloak/config/Dockerfile`. `FROM revy-keycloak:26.0` (the built image containing vymalo webhook JARs + `start --optimized` — not stock `quay.io/keycloak/keycloak:26.0`), `COPY themes/revy /opt/keycloak/themes/revy`. No `kc.sh build` — base image already ran it. **Prerequisite:** the `deploy/keycloak/config/Dockerfile` must be built first (`docker compose build` in `deploy/keycloak/config/`) to produce the `revy-keycloak:26.0` base image. Update `deploy/keycloak/config/docker-compose.yml` → bind-mount `/mnt/revy_volume/keycloak-themes:/opt/keycloak/themes:ro` (absolute path; themes dir is a separate volume sibling to `keycloak/config/`, not a subdirectory). Document the ops-owned recreate option (C6). **Out:** executing a recreate on production; Keycloak upgrade.

**Deliverables:** Baked image builds locally and serves the theme under `start --optimized`; compose updated for the next deploy cycle; final push.

**Depends on:** P2 (proven in production).

---

## Next

**`create-execution-plan`** from this folder. Open items: Q12 `defaultLocale` (ask ops before P2), Q14 who applies (default operator; workflow optional).
