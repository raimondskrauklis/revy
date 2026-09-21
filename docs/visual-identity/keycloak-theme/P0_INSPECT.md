# docs/visual-identity/keycloak-theme/P0_INSPECT.md

# P0 — Container + realm inspection

**Date:** 2026-09-21
**Inspected via:** SSH sec-vm (raimo@165.245.251.189)
**Redacted — env values are key names only, never secrets.**

## Container inspection (docker inspect revy-kc)

| Field | Value |
|:---|:---|
| Image | sha256:3a094577... (revy-keycloak:26.0) |
| Image digest | sha256:3a09457773af9bfacc5b4e8cac0b741b4c0ca67c3bf79cfe18106f484e42c2ec |
| Cmd | start --optimized |
| Entrypoint | /opt/keycloak/bin/kc.sh |
| User | keycloak |
| Mounts | none (tmpfs only) |
| RestartPolicy | unless-stopped |
| PortBindings | 127.0.0.1:8080:8080, 127.0.0.1:9000:9000 |
| NetworkMode | revy-net |
| Env keys (names only) | KC_BOOTSTRAP_ADMIN_USERNAME, KC_BOOTSTRAP_ADMIN_PASSWORD, KC_DB, KC_DB_URL, KC_DB_USERNAME, KC_DB_PASSWORD, KC_HEALTH_ENABLED, KC_HOSTNAME, KC_HOSTNAME_STRICT, KC_HTTP_ENABLED, KC_METRICS_ENABLED, KC_PROXY_HEADERS, KC_PROXY_TRUSTED_ADDRESSES, LANG, PATH, WEBHOOK_EVENTS_TAKEN, WEBHOOK_HTTP_AUTH_USERNAME, WEBHOOK_HTTP_AUTH_PASSWORD, WEBHOOK_HTTP_BASE_PATH |

## KC version

| Field | Value |
|:---|:---|
| Version | Keycloak 26.0.8 (JVM 21.0.6, Linux amd64) |

## Writable paths

| Path | Status |
|:---|:---|
| /opt/keycloak/themes | Only README.md — empty dir. Writable (keycloak:root, drwxrwxr-x). docker cp will work. |
| /opt/keycloak/data/tmp | Contains kc-gzip-cache/. Writable (keycloak:root). |
| Note | Bundled themes (keycloak.v2 etc.) in JARs. Directory theme revy recognized alongside. |

## Session persistence config

| Field | Value |
|:---|:---|
| Cache config | cache-ispn.xml — Infinispan only, no persistence/store |
| sessions | distributed-cache, lifespan=-1, max-count=10000 (in-memory) |
| authenticationSessions | distributed-cache, lifespan=-1 (in-memory) |
| Restart impact | Sessions WILL be dropped. Accept brief blip — one restart only. |

## Deploy user + Docker GID

| Field | Value |
|:---|:---|
| Deploy user | raimo (uid=1000) |
| Docker GID | 112 (docker group) |

## Realm state (kcadm.sh get realms/revy)

| Setting | Value |
|:---|:---|
| loginTheme (current — rollback value) | Not set (default = keycloak legacy PF3) |
| internationalizationEnabled | false |
| supportedLocales | [] (empty) |
| defaultLocale | Not set |
| registrationAllowed | false |
| resetPasswordAllowed | false |
| rememberMe | false |
| loginWithEmailAllowed | true |
| keycloak.v2 in theme dropdown? | Yes — bundled in JAR (KC 26.0 ships it) |

## Q12 — defaultLocale

**Resolution:** en (English default). LV available via locale switcher after i18n is enabled.

## Q14 — Who applies

**Resolution:** Operator script (infra/keycloak/scripts/apply_theme.sh). Manual apply, not CI workflow.

---

## stylesCommon inheritance test

**Result:** stylesCommon inherits automatically. When a child theme sets styles= and the parent keycloak.v2 declares stylesCommon, the parent's stylesCommon list is inherited — child does NOT need to re-declare it.

**Test:** Minimal child theme (parent=keycloak.v2, styles=css/test.css, empty CSS). PF stylesCommon CSS loaded on login page — confirmed via browser dev tools Network tab.

**P1 consequence:** theme.properties uses only styles=css/revy-login.css — no stylesCommon line needed.
