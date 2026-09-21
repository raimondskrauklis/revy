# docs/visual-identity/keycloak-theme/KEYCLOAK_THEME_FINDINGS.md

# Keycloak login theme — findings

**Status:** Baseline for planning (decisions locked). Not yet peer-reviewed.  
**Last verified:** 2026-09-21 (repo HEAD + `deploy/keycloak/config/` + `KEYCLOAK_DEV_CHECKLIST.md` + upstream KC 26.0).  
**Parent:** `VISUAL_IDENTITY_FINDINGS.md` · `VISUAL_IDENTITY_GENERAL_PLAN.md`  
**Research adapted from:** `kp-platform/docs/infrastructure/keycloak_theme/` — same KC 26 base, not executed.

---

## Build principles

- **Identity stays Keycloak; authorization stays PostgreSQL.** This program changes pixels on Keycloak login-type pages only. No JWT, realm clients, roles.
- **Match the Revy operator console — not PatternFly.** SPA forced dark (`html.dark`). Login continues phosphor-green (`--app-*` from `tokens.revy.css`), not PF blue geometry.
- **Do not edit bundled Keycloak themes.** Child theme in git, parent `keycloak.v2`.
- **Do not recreate the live container** until `docker inspect` is recorded.
- **Do not restart Keycloak on every app deploy.** Gated, explicit theme apply.
- **CSS over FreeMarker.** No copied `login.ftl` / `template.ftl`.
- **Tokens, not a second palette.** Resolved hex from `tokens.revy.css` `html.dark` block (L63–106). No `--rv-*` names in theme CSS.
- **No Alembic.** Theme + realm `loginTheme`. KC owns its own DB.
- **Never commit Keycloak secrets.** Inspect strips values.
- **Git is SSOT; block storage is on-box copy.** `git → rsync → /mnt/revy_volume/keycloak-themes/ → docker cp → container`.
- **Iterate locally, restart production once.** Local `start-dev` with caches off.

---

## Terminology

| Term | Meaning |
|:---|:---|
| **Login-type pages** | Theme type `login`: sign-in, register, reset, update, error, info, OTP. One theme covers all. |
| **`keycloak.v2`** | PatternFly 5 login (KC 23+). Present in KC 26.0. Parent to extend. |
| **Directory theme** | Folder under `/opt/keycloak/themes/<name>/`. No JAR, no `kc.sh build`. |
| **Theme gzip cache** | `/opt/keycloak/data/tmp/kc-gzip-cache` — stale after `docker cp`. |

---

## What exists vs genuinely new

### Verified — Revy Keycloak infra

| Piece | Evidence |
|:---|:---|
| Auth host | `https://auth.revy.createit.digital` — `.env.example:19` |
| Container name | `revy-kc` — `docker-compose.yml:15` |
| Image | `revy-keycloak:26.0`, base `quay.io/keycloak/keycloak:26.0` |
| Start command | `start --optimized` — `docker-compose.yml:17` |
| Volume | `/mnt/revy_volume/` |
| Network | `revy-net` external |
| Webhook | vymalo 0.10.0-rc.1 → `revy-api:8000` |
| Realm | `revy`, client `revy-web` — `KEYCLOAK_DEV_CHECKLIST.md` |
| `infra/keycloak/` | **Does not exist** — this program creates it |

### Verified — Revy dark tokens (verbatim copy source)

| Token | Dark hex | `tokens.revy.css` |
|:---|:---|:---|
| Canvas | `#07140c` | L64 |
| Surface | `#0d1c14` | L66 |
| Ring | `#1e3a28` | L67 |
| Ring strong | `#2f5840` | L68 |
| Input border | `#4a7a5c` | L69 |
| Text strong | `#d5ead0` | L70 |
| Text (body) | `#c5e0b8` | L71 |
| Text muted | `#86a882` | L72 |
| Text subtle | `#5e7c5c` | L73 |
| Chip | `#132418` | L74 |
| Primary / CTA bg | `#a8dc84` | L76,79 |
| CTA fg | `#07140c` | L80 |
| Info | `#a8d4e8` | L77 |
| Warning | `#d4a84b` | L78 |
| Danger | `#e06b6b` | L79 |
| Success | `#a8dc84` | L79 |

### Verified — SPA auth flow

- `/login` → `keycloak.login({ redirectUri: .../auth/callback })`
- `/auth/callback` → `bg-[color:var(--app-canvas)]` → `/reviewer` on success (AuthCallbackPage.tsx)
- Post-logout redirect → `/` (keycloak.ts:50)

### Assumptions (must verify before implementation)

| Claim | Status |
|:---|:---|
| `keycloak.v2` available in live image | **Assumed** — KC 26.0 ships it. `docker exec` to confirm. |
| `/opt/keycloak/themes` writable | **Assumed** — standard image. |
| Realm `loginTheme` current value | **Unverified** — likely `keycloak` (legacy PF3). Record before cutover — this is the rollback value. |
| Realm i18n flags (`internationalizationEnabled`, `supportedLocales`, `defaultLocale`) | **Unverified** — `en,lv` must be enabled for C3b. |
| Realm page flags (`registrationAllowed`, `resetPasswordAllowed`, etc.) | **Unverified** — determine which login-type pages to QA. |
| gzip cache path `/opt/keycloak/data/tmp/kc-gzip-cache` | **Assumed** — standard Quarkus layout. |
| Session persistence | **Unverified** — `start --optimized` uses Infinispan cache; does `docker restart` drop SSO sessions? Record config in P0 to inform whether P2 restart needs a maintenance window. |

### Genuinely new (this program)

- `infra/keycloak/` tree: directory theme `revy` (login type), local compose, fail-closed `check_theme.sh`.
- Dark phosphor-green CSS owning the **full** login layout (parent v2 `styles.css` is dropped by `styles=`). Kills geometry, blue stripe, uppercase header.
- EN+LV message overrides + realm i18n `en,lv` enabled.
- Transport + apply without `docker rm`: `rsync → block storage → docker cp → gzip delete → one restart`. Backup first.
- One-time realm `loginTheme=revy` with recorded rollback value.
- Later: `Dockerfile` bake `FROM revy-keycloak:26.0` + `COPY themes/revy`; ops-owned recreate with bind mount.

### Reuse traps (from KP research, verified for KC 26)

- **`styles=` replaces parent list.** Only our file + inherited `stylesCommon`. Never list parent `css/styles.css` — that file is v1, causes 404 on child URL ([keycloak#41846](https://github.com/keycloak/keycloak/issues/41846)). **Note:** when child sets `styles=` and the parent `keycloak.v2` declares `stylesCommon`, the parent's `stylesCommon` list is inherited automatically — child does not need to re-declare it. Verify during local loop.
- **`keycloak.v2` still uses `login-pf` class.** Blue stripe is `--keycloak-card-top-color` / `pf-v5-c-login__main-header`. Child CSS must kill it.
- **`darkMode=false` in child** removes parent OS-preference toggler. Force-dark via CSS `color-scheme: dark`. No JS needed.
- **`docker cp` does not create parent dirs.** `/opt/keycloak/themes/` must exist (does in official image). `docker cp` writes `root:root` at destination; UID 1000 needs only read.
- **Mounts cannot be added to running container.** Bind-mount requires recreate — deferred to ops (C6).
- **Never put themes in `/mnt/revy_volume/keycloak/config/`** (holds `.env` with DB secrets). Create sibling `/mnt/revy_volume/keycloak-themes/`.
- **Do not theme Admin Console.** Operators need stock KC admin.
- **No TenderPRO leftover** in this repo (KP had `keycloak-setup/` to delete — not relevant to Revy).

---

## Catalog

### Track A — Visual language

**Rationale:** User-visible break is dark SPA → stock Keycloak. Tokens exist in `tokens.revy.css`; Keycloak can't import that file — hex must be copied verbatim.

| # | Capability | Method |
|:--|:---|:---|
| A1 | Dark canvas | `#07140c`; no background image |
| A2 | Title hierarchy | `#kc-header-wrapper` lowercase, no tracking; `#kc-page-title` section heading |
| A3 | Card / form | `#0d1c14` + `#1e3a28` ring; border-radius 4px (`--app-radius-md` — same value in light and dark); no 4px blue top border |
| A4 | Inputs | Quiet-input analogue: `#4a7a5c` border, focus `#2f5840`, min 44px |
| A5 | Primary button | CTA `bg: #a8dc84` / `fg: #07140c`, not PF blue; hover opacity |
| A6 | Links / errors | Link `#a8dc84` (primary), danger `#e06b6b` |
| A7 | Cover all login-type pages | CSS only — register, forgot, error, info inherit |

### Track B — Theme SPI

| # | Capability | Method |
|:--|:---|:---|
| B1 | Child theme `revy` | `parent=keycloak.v2`; `styles=css/revy-login.css`; `darkMode=false` |
| B2 | Inherit PF + class map | Do **not** set `stylesCommon` / `kc*Class` unless testing shows inherit is broken. When child sets `styles=css/revy-login.css`, parent's `stylesCommon` list is **inherited automatically** — child does not need to re-list it. Verify during P0/P1 local loop. |
| B3 | Messages | Override branding keys EN+LV; remainder inherit KC bundles. Requires realm i18n `en,lv` (C3b) |
| B4 | Force dark | `darkMode=false` + CSS `color-scheme: dark`. `scripts=` only if local testing proves PF variables still fight the tokens |
| B5 | No FTL clones | CSS-only. Optional KC 26 `footer.ftl` only if CSS is insufficient |
| B6 | Token block | Verbatim copy of resolved hex from `tokens.revy.css` `html.dark` (L63–106) with header comment naming source lines. `--app-radius-md` is 4px in both light and dark — copy the value directly. |
| B7 | Fail-closed check | `scripts/check_theme.sh`: every file in `styles=` resolves; `messages_lv` keys ⊆ `messages_en`; all `#hex` values come from either the verbatim token block or a documented list of accepted KC layout overrides (canvas, surface, card classes, input overrides). No unlisted hex. Runs locally and in CI. |

### Track C — Ship / ops

| # | Capability | Method |
|:--|:---|:---|
| C0 | Local loop | `infra/keycloak/docker-compose.yml` — `quay.io/keycloak/keycloak:26.0`, `start-dev`, `./themes:/opt/keycloak/themes`, caches off; throwaway realm `revy` |
| C1a | Transport | `rsync -az --delete infra/keycloak/themes/revy/ <host>:/mnt/revy_volume/keycloak-themes/revy/` |
| C1b | Backup | `docker cp` container copy → `.prev-<ts>/` if a prior copy exists |
| C1c | Apply | `docker cp /mnt/revy_volume/keycloak-themes/revy revy-kc:/opt/keycloak/themes/` |
| C2 | Cache | `docker exec revy-kc rm -rf /opt/keycloak/data/tmp/kc-gzip-cache` → `docker restart revy-kc` **once** |
| C3a | Realm theme | `loginTheme=revy` on realm `revy` via Admin; rollback = recorded current value |
| C3b | Realm i18n | `internationalizationEnabled=true`, `supportedLocales=[en,lv]`, `defaultLocale` TBD |
| C4 | Repeat apply | `.github/workflows/keycloak-theme.yml` (`workflow_dispatch`) or operator script — **never** `deploy-production` |
| C5 | Bake (later) | `infra/keycloak/Dockerfile` **separate from** `deploy/keycloak/config/Dockerfile`. `FROM revy-keycloak:26.0` (the built image with vymalo webhook JARs + `start --optimized`), `COPY themes/revy /opt/keycloak/themes/revy`. No `kc.sh build` — the base image already ran it. |
| C6 | DO recreate (ops, later) | `-v /mnt/revy_volume/keycloak-themes:/opt/keycloak/themes:ro` — absolute mount of the keycloak-themes dir as read-only |

---

## Advice / options

**Recommended:** directory child of `keycloak.v2`, CSS-only dark phosphor-green, `docker cp` onto `revy-kc`, one `loginTheme=revy`. Smallest change matching the Revy console + KC 26 guidance.

**Rejected — legacy parent `keycloak`.** PF3 geometry + blue stripe forever.

**Rejected — Admin "theme colors" picker.** PatternFly variables only; can't match console layout.

**Rejected — new image on first ship.** Unknown `docker run` args → identity outage. `docker cp` first.

**Rejected — mount `/mnt/revy_volume/keycloak/config/`.** Holds secrets.

**Adopted — block storage as on-box source (Q10).** `/mnt/revy_volume/keycloak-themes/` is rsync target + `docker cp` source. Survives rebuild. Becomes bind-mount at ops recreate (C6).

**Deferred — email, account, welcome themes, favicon.**

---

## External research / patterns

| Pattern | Verdict |
|:---|:---|
| Official: extend bundled theme; never edit JAR themes | **Adopt** |
| Disable caches for local iteration: `--spi-theme-static-max-age=-1 --spi-theme-cache-themes=false --spi-theme-cache-templates=false` | **Adopt for local only** |
| `styles=` last file wins; parent CSS not auto-appended | **Adopt** — our file only + `stylesCommon` |
| Do not copy FTL unless structure must change | **Adopt** |
| KC 26 `footer.ftl` hook | **Defer** |
| Force-dark via `darkMode=false` | **Adopt** — removes parent `matchMedia` toggler |
| Vendor path rename in KC 26 (`vendor/patternfly-v5`) | **Adopt** — inherit parent `stylesCommon` |

---

## Data scope & exclusions

**In:** HTML/CSS/messages for Keycloak **login** theme type on realm `revy`.

**Out:**
- `revy` schema, users, RBAC, JWT
- SPA landing / login React components (visual identity P1/P2 owns those)
- Admin console, account console, email templates
- Keycloak HA / hostname / proxy / upgrade
- Changing registration / reset / remember-me **policy** (realm flags — only style what's enabled)
- `revy-kc` Dockerfile rebuild (current image already has webhook + `start --optimized`)

---

## Edge cases

- **404 CSS → unstyled login.** Fail closed: `check_theme.sh` + visual QA + local loop before production.
- **`keycloak.v2` missing.** KC 26.0 ships it. Verify with `docker exec`.
- **Restart drops sessions.** One restart, not a loop. SSO may survive in DB; brief blip accepted.
- **Read-only container root.** `docker cp` fails → bake an image instead.
- **gzip + browser cache.** Delete gzip dir + restart → hard refresh. No query string we control.
- **Light-mode users.** Accepted: SPA is forced dark (VI-Q2). Login continues that.
- **i18n never renders LV** unless realm i18n is on. C3b is a hard deliverable.
- **Realm rollback.** `loginTheme` is instant (no restart). Record current value.
- **Register styling** — must inherit same card, not leftover PF3.
- **Password visibility toggle** — PF control must not reintroduce blue.
- **SPA callback** must still work after theme cutover. No client/redirect change.
- **Admin console** must remain stock Keycloak.

---

## Decisions registry

| Q# | Question | Status | Resolution |
|:---|:---|:---|:---|
| Q1 | Parent theme | **Locked** | `keycloak.v2` (KC 26.0) |
| Q2 | Light/dark | **Locked** | Always dark phosphor-green. Match SPA forced dark (VI-Q2). |
| Q3 | Theme types | **Locked** | `login` only |
| Q4 | First ship vehicle | **Locked** | `docker cp` into `revy-kc`; no recreate |
| Q5 | App `deploy.yml` | **Locked** | Never restart KC on main pushes. Gated apply. |
| Q6 | Realm switch | **Locked** | `loginTheme=revy` once via Admin |
| Q7 | FTL | **Locked** | No copied templates |
| Q8 | Token source | **Locked** | Resolved hex from `tokens.revy.css` `html.dark` L63–106. `--app-radius-md` (4px) same in both modes — copy value directly. |
| Q9 | i18n | **Locked** | EN+LV branding overrides |
| Q10 | On-box source | **Locked** | `/mnt/revy_volume/keycloak-themes/revy/` |
| Q11 | Theme home | **Locked** | `infra/keycloak/` |
| Q12 | Realm i18n flags | **Locked / one open** | `en,lv` on; `defaultLocale` TBD (ask ops) |
| Q13 | Runtime bind-mount | **Locked no (v1)** | Defer to ops recreate |
| Q14 | Who applies | **Open** | Operator script or CI `workflow_dispatch`. Default: operator. |

---

## Parking lot

- `docker inspect revy-kc` (Env key names only, redacted) — prerequisite before any file copy.
- Confirm `keycloak.v2` in Admin theme dropdown.
- **Test `stylesCommon` inheritance** in local loop: does the child theme load PF styles automatically when only `styles=` is set? If not, add `stylesCommon` to child's `theme.properties`.
- Record current realm `loginTheme` — **rollback value.**
- Record realm i18n flags + page flags (`registrationAllowed`, `resetPasswordAllowed`, `rememberMe`, `loginWithEmailAllowed`).
- Record session persistence config (Infinispan / DB sessions) to inform P2 restart impact.
- Create `/mnt/revy_volume/keycloak-themes/` once (`install -d -m 0755 -o <deploy-user> -g docker`). Deploy user and docker GID resolved during P0 from `deploy.yml` SSH actions or droplet user listing.
- Check `/mnt/revy_volume/keycloak/config/.env` permissions (KP had `644` world-readable secrets — flag for ops).
- Optional `infra/keycloak/Dockerfile` bake for on-prem.
- Favicon on Keycloak vs SPA — not this program.

---

## Devil's advocate

- **404 CSS → outage.** Mitigation: local loop + `check_theme.sh` + visual QA before production.
- **`docker rm` without inspect** loses hostname, DB, proxy, webhook. Mitigation: `docker cp` only, no recreate.
- **Theme never selected** — files in container do nothing until realm `loginTheme=revy`. Q6 hard deliverable.
- **Always-dark annoys light users** — accepted; SPA is forced dark.
- **Restart during sessions** — one gated apply. SSO may survive.
- **Secrets in inspect** — redact values.
- **Iterating on production** — C0 local loop mandatory before touching production.
- **Phosphor-green Keycloak ≠ PatternFly blue** — by design. Users should not recognize the hop as a different product.

---

## Experiment / verification

**Pass:**
- Login, register (if enabled), forgot-password, error page: dark `#07140c` canvas, no PF geometry, no blue stripe, CTA `#a8dc84` on `#07140c`.
- `#kc-header-wrapper` reads as `revy` (lowercase, matching console), not tracked uppercase.
- Inputs/button ≥ 44px; focus ring `#2f5840`; password toggle not PF blue.
- EN and LV via locale switcher (realm i18n on).
- `info` page after reset-password submit; `error` page via bad `redirect_uri`.
- SPA callback still works: `auth.revy.createit.digital` → `revy.createit.digital/auth/callback` → `/reviewer`.
- Admin console `auth.revy.createit.digital/admin` still stock Keycloak.
- `check_theme.sh` exits 0.

**Fail:**
- Unstyled / 404 CSS.
- PF geometry or blue button still visible.
- Keycloak down after apply.
- App deploy pipeline restarts KC on unrelated merges.

---

## References

### Code

- `deploy/keycloak/config/docker-compose.yml` — `revy-kc`, `revy-keycloak:26.0`, `start --optimized`
- `deploy/keycloak/config/Dockerfile` — `FROM quay.io/keycloak/keycloak:26.0`, vymalo webhook
- `deploy/keycloak/config/.env.example` — `KC_HOSTNAME`, webhook config
- `docs/starter-pack/KEYCLOAK_DEV_CHECKLIST.md` — realm `revy`, client `revy-web`, JWT audience
- `frontend/src/lib/keycloak.ts` — SPA config, logout, account console
- `frontend/src/features/auth/pages/AuthCallbackPage.tsx` — post-login redirect
- `frontend/src/styles/tokens.revy.css` — `html.dark` `--rv-*` scale (L63–106), contrast record (L4–13)
- `frontend/src/styles/tokens.css` — `--app-*` base (overridden)
- `.github/workflows/deploy.yml` — does not restart KC
- `docs/visual-identity/VISUAL_IDENTITY_FINDINGS.md` — operator console identity
- `docs/visual-identity/VISUAL_IDENTITY_GENERAL_PLAN.md` — P0–P4 phases

### Upstream

- [Keycloak themes](https://www.keycloak.org/ui-customization/themes)
- [RH BK 26.2 Themes](https://docs.redhat.com/documentation/red_hat_build_of_keycloak/26.2/html/server_developer_guide/themes)
- [keycloak.v2 login at 26.0](https://github.com/keycloak/keycloak/tree/26.0/themes/src/main/resources/theme/keycloak.v2/login) — `theme.properties`, `template.ftl`, `styles.css` (134 lines)
- [`docker cp` reference](https://docs.docker.com/reference/cli/docker/container/cp/)
- [Issue #41846 — parent CSS 404](https://github.com/keycloak/keycloak/issues/41846)

### Adapted from

- `kp-platform/docs/infrastructure/keycloak_theme/KEYCLOAK_THEME_FINDINGS.md` — KP research (KC 26, `keycloak.v2`, directory theme, `docker cp`). Not executed. Tokens and infra names adapted for Revy.
