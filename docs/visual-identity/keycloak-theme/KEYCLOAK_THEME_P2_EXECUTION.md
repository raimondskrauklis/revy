// docs/visual-identity/keycloak-theme/KEYCLOAK_THEME_P2_EXECUTION.md

# P2 — Transport, apply, realm cutover (execution)

Phase **P2** of [`KEYCLOAK_THEME_GENERAL_PLAN.md`](./KEYCLOAK_THEME_GENERAL_PLAN.md). Baseline: [`KEYCLOAK_THEME_FINDINGS.md`](./KEYCLOAK_THEME_FINDINGS.md) Q1–Q13. **P2 only.**

**Goal:** The theme is on production `revy-kc`, the realm is switched, and users who click "Get Started" land on Revy-branded login in their language.

## Decisions locked for P2
- Q12 `defaultLocale` resolved in P0. Q14 apply decision made (operator script or CI). Placeholder deploy user and docker GID filled from P0 values.
- Parent `keycloak.v2`, always dark, `login` type only, CSS-only, `loginTheme=revy`, i18n `en,lv` on.
- Rollback: `loginTheme` ← P0 recorded value (instant, no restart).

## Out of scope for P2 (later phases)
- Dockerfile bake, compose sync → **P3**
- Changing registration/reset/remember-me **policy** — only style what's enabled
- Client/redirect/secret changes
- Admin console theme

---

## P2.1 — Create volume dir for themes

**What:** SSH to droplet. `install -d -m 0755 -o <deploy-user-from-P0> -g <docker-gid-from-P0> /mnt/revy_volume/keycloak-themes/`. Run once — ensures the sibling directory to `/mnt/revy_volume/keycloak/config/` exists for rsync.

**Files:** None (ops command on droplet)

**Deliverable:** `ls -la /mnt/revy_volume/keycloak-themes/` shows the directory with correct owner and group.

---

## P2.2 — Create apply_theme.sh script

**What:** `infra/keycloak/scripts/apply_theme.sh` — runs on the droplet. Steps: (1) if `/opt/keycloak/themes/revy` exists in container, `docker cp revy-kc:/opt/keycloak/themes/revy /mnt/revy_volume/keycloak-themes/.prev-$(date +%s)/` for backup; (2) `docker cp /mnt/revy_volume/keycloak-themes/revy revy-kc:/opt/keycloak/themes/`; (3) `docker exec revy-kc rm -rf /opt/keycloak/data/tmp/kc-gzip-cache`; (4) `docker restart revy-kc`; (5) wait for `curl -sf http://127.0.0.1:8080/health/ready` (up to 60s); (6) print hint to check Admin theme dropdown. Session impact per P0 (brief blip if Infinispan-only).

**Files:** New — `infra/keycloak/scripts/apply_theme.sh`

**Deliverable:** Script exists and is executable (`chmod +x`). Does not run in this subphase — P2.4 invokes it.

---

## P2.3 — Transport theme to droplet

**What:** `rsync -az --delete infra/keycloak/themes/revy/ infra/keycloak/scripts/ <ssh-target>:/mnt/revy_volume/keycloak-themes/` from local (or CI if Q14 = workflow). Copies both theme files and the `apply_theme.sh` script. SSH target is the operator user on the production droplet.

**Files:** None (network operation)

**Deliverable:** `ssh <host> ls /mnt/revy_volume/keycloak-themes/revy/login/theme.properties` returns the file; `ls /mnt/revy_volume/keycloak-themes/scripts/apply_theme.sh` returns the script.

---

## P2.4 — Apply theme on production

**What:** SSH to droplet. Run `bash /mnt/revy_volume/keycloak-themes/scripts/apply_theme.sh`. Verify container restarts: `docker ps | grep revy-kc` shows Up; `docker logs revy-kc --tail 20` no errors.

**Files:** Theme files now live in `/opt/keycloak/themes/revy/` inside `revy-kc`.

**Deliverable:** `docker exec revy-kc ls /opt/keycloak/themes/revy/login/theme.properties` shows the file; `revy-kc` is healthy on `:8080`; prior copy backed up if existed.

---

## P2.5 — Realm i18n + theme cutover

**What:** Via Keycloak Admin UI (`auth.revy.createit.digital/admin` → realm `revy`): set `internationalizationEnabled=true`, `supportedLocales=en,lv`, `defaultLocale` per Q12. Then set `loginTheme=revy`. Record rollback command in `P0_INSPECT.md` appendix: `loginTheme` ← P0 value.

**Files:** None (Admin UI operation). Document rollback in `P0_INSPECT.md` appendix.

**Deliverable:** `revy` theme selected on realm `revy`; locale switcher appears on login page; `loginTheme` dropdown shows `revy`.

---

## P2.6 — Production visual QA

**What:** Exercise `auth.revy.createit.digital/realms/revy/account` (login page): sign-in, forgot-password → info page, error page (append `?redirect_uri=bad` to login URL). Register only if `registrationAllowed=true` from P0. EN and LV via locale switcher. 375px and desktop. Password visibility toggle. Verify OIDC callback: sign in → redirect to `revy.createit.digital/auth/callback` → SPA loads. Admin console `auth.revy.createit.digital/admin` still stock. **Rollback test (required):** set `loginTheme` ← P0 value via Admin UI, confirm login returns to stock theme, then set `loginTheme=revy` again. This proves rollback is instant and recoverable.

**Files:** None (manual QA). Screenshots to temp location.

**Deliverable:** All login-type pages pass the findings verification list on production; SPA callback works; rollback tested and reverted; rollback value documented; `.prev-<ts>` backup exists.

---

**Phase gate** (manual — production verification):

- `curl -sf https://auth.revy.createit.digital/realms/revy/account` returns login page HTML.
- Visual: canvas `#07140c`, no PF blue, CTA phosphor green, EN+LV switcher present.
- SPA: sign-in → callback → `/reviewer` loads.
- Admin `auth.revy.createit.digital/admin` — stock Keycloak, no green theme.
- Rollback value known: `loginTheme` → P0 value, instant revert possible.

**Human gate:** P2 applies to production — one `docker restart revy-kc` drops SSO sessions (brief blip per P0). Confirm with ops before running, or run off-peak.

**Deploy:** commit + push after production QA passes. PR update: `feat(keycloak-theme): P2 — transport, apply, realm cutover`.

**Next:** [`KEYCLOAK_THEME_P3_EXECUTION.md`](./KEYCLOAK_THEME_P3_EXECUTION.md) — bake + docker-compose sync (optional, deferred).
