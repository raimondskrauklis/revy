// docs/visual-identity/keycloak-theme/KEYCLOAK_THEME_P1_EXECUTION.md

# P1 — Theme package + local loop (execution)

Phase **P1** of [`KEYCLOAK_THEME_GENERAL_PLAN.md`](./KEYCLOAK_THEME_GENERAL_PLAN.md). Baseline: [`KEYCLOAK_THEME_FINDINGS.md`](./KEYCLOAK_THEME_FINDINGS.md) Q1–Q13. **P1 only.**

**Goal:** A git directory theme that looks like the dark phosphor-green console, proven on a local Keycloak `26.0` before production is touched.

## Decisions locked for P1
- Parent `keycloak.v2`, always dark, `login` type only, CSS-only (no FTL), `darkMode=false`, tokens from `tokens.revy.css` `html.dark` L63–106, EN+LV messages, `styles=` only (no `stylesCommon` unless P0 proved inherit broken)

## Out of scope for P1 (later phases)
- rsync, `docker cp` into production, realm cutover → **P2**
- Dockerfile bake, compose sync → **P3**
- `scripts=` JS file (only create if `darkMode=false` alone insufficient — record reason)
- Admin console, account console, email themes

---

## P1.1 — Create theme.properties

**What:** `infra/keycloak/themes/revy/login/theme.properties` — `parent=keycloak.v2`, `styles=css/revy-login.css`, `darkMode=false`. Do **not** set `stylesCommon` unless P0.4 proved auto-inherit is broken.

**Files:** New — `infra/keycloak/themes/revy/login/theme.properties`

**Deliverable:** File exists with exactly three non-comment lines. `parent`, `styles`, `darkMode` match P0 + findings decisions.

---

## P1.2 — Create revy-login.css with verbatim token block

**What:** `infra/keycloak/themes/revy/login/resources/css/revy-login.css` — header comment naming source lines (`tokens.revy.css html.dark L63–106`). Verbatim copy of all resolved `--app-*` hex values as CSS custom properties under `:root {}`. Note `--app-radius-md` is 4px in both light and dark. Then write the full login layout CSS: kill PF blue stripe (`#kc-header-wrapper`, `.pf-v5-c-login__main-header` — remove `--keycloak-card-top-color`, zero the 4px top border), set canvas `#07140c`, surface `#0d1c14`, ring `#1e3a28`, inputs `#4a7a5c` with focus `#2f5840` and min-height 44px, CTA `bg: #a8dc84` / `fg: #07140c`, link `#a8dc84`, danger `#e06b6b`, info `#a8d4e8`, text body `#c5e0b8` on canvas. `color-scheme: dark` on `html`/`:root`. Cover login-type pages: login, register, forgot-password, error, info. OTP, update-password, and other KC login-type pages inherit the same CSS by default — no special selectors needed. Any hex in KC class overrides (e.g. `#kc-page-title`, `#kc-form-login`, `.pf-v5-c-form-control`) must come from the token block or a documented layout hex list in a CSS comment. No `#hex` outside those two lists.

**Files:** New — `infra/keycloak/themes/revy/login/resources/css/revy-login.css`

**Deliverable:** CSS file compiles without syntax errors; token block hex matches `tokens.revy.css` `html.dark` L63–106 exactly; `check_theme.sh` passes hex audit (token block + layout list only). WCAG 2.2 AA / APCA Lc ≥ 75 contrast verified visually in P1.6.

---

## P1.3 — Create EN+LV message overrides

**What:** `infra/keycloak/themes/revy/login/messages/messages_en.properties` and `messages_lv.properties` — override branding keys only (realm display name, locale labels, footer). Remainder inherits from Keycloak bundles. EN and LV keys must match (LV keys ⊆ EN keys — `check_theme.sh` enforces).

**Files:** New — `infra/keycloak/themes/revy/login/messages/messages_en.properties`, `messages_lv.properties`

**Deliverable:** Both files exist; LV keys ⊆ EN keys; realm display name = `revy` in both locales.

---

## P1.4 — Create local docker-compose + .env.example

**What:** `infra/keycloak/docker-compose.yml` — `image: quay.io/keycloak/keycloak:26.0`, `command: start-dev`, `volumes: ./themes:/opt/keycloak/themes`, `environment: KC_BOOTSTRAP_ADMIN_USERNAME=admin`, `KC_BOOTSTRAP_ADMIN_PASSWORD=admin`, theme cache flags off (`--spi-theme-static-max-age=-1 --spi-theme-cache-themes=false --spi-theme-cache-templates=false`), `ports: 8080:8080`. `.env.example` with placeholder admin password.

**Files:** New — `infra/keycloak/docker-compose.yml`, `infra/keycloak/.env.example`

**Deliverable:** `docker compose -f infra/keycloak/docker-compose.yml up -d` starts KC; `curl -sf http://127.0.0.1:8080/health/ready` passes.

---

## P1.5 — Create check_theme.sh

**What:** `infra/keycloak/scripts/check_theme.sh` — bash script. Checks: (1) every file in `styles=` resolves under `themes/revy/login/resources/`; (2) `messages_lv` keys ⊆ `messages_en` keys; (3) all `#hex` values in `revy-login.css` come from either the verbatim token block or a documented layout hex list (no unlisted hex). Exit 0 on pass, non-zero with details on fail.

**Files:** New — `infra/keycloak/scripts/check_theme.sh`

**Deliverable:** `bash infra/keycloak/scripts/check_theme.sh` exits 0 on the shipped tree.

---

## P1.6 — Local visual QA

**What:** Start local compose. Create throwaway realm `revy` via Admin (`http://localhost:8080/admin`) with `loginTheme=revy`. Screenshot login, forgot-password, error page (bad `redirect_uri`), and info page (after reset-password submit) in EN and LV at 375px and desktop. Register QA only if P0 `registrationAllowed=true`. Verify: canvas `#07140c`, no PF blue geometry, no `--keycloak-bg` SVG, CTA `#a8dc84` on `#07140c`, inputs ≥ 44px, focus ring visible, password toggle not blue, locale switcher works. SPA callback simulation not needed (local only).

**Files:** Screenshots to a temp location (not committed) or described in `P0_INSPECT.md` appendix.

**Deliverable:** Visual pass: every login-type page matches the findings verification list (A1–A7).

---

**Phase gate** (no pytest/Vitest — manual + script):

```bash
bash infra/keycloak/scripts/check_theme.sh
# visual QA screenshots pass the findings verification list
```

**Deploy:** commit + **first push**. PR title `feat(keycloak-theme): theme package and local loop`. Commit message: `feat(keycloak-theme): P1 — theme package, local loop, check_theme.sh`.

**Next:** [`KEYCLOAK_THEME_P2_EXECUTION.md`](./KEYCLOAK_THEME_P2_EXECUTION.md) — transport, apply, realm cutover.
