# docs/github-onboarding/GITHUB_ONBOARDING_FINDINGS.md

# GitHub onboarding — findings (Revy)

Baseline for a **Revy web-UI GitHub connect wizard**. **No execution steps.**

**Status:** baseline-ready (2026-09-19). Execution files P0–P4 ready. Next: `phase-execution` from P0.  
**Verified:** this repo + vendor docs (2026-09-19).  
**Dogfood (planned):** new Revy user + install Revy on **`raimondskrauklis/saas-base`**. That repo is the **P4 experiment target**, not the product verify predicate (Q16).

Review pipeline already reviews GitHub PRs. Connecting a workspace still requires a human to type GitHub IDs. Operator setup is markdown. This program ships the missing **in-app onboarding** (pipeline Q10).

---

## Build principles

- **Never mislead.** Wrong GitHub URL (user vs org) or “connected” without a verified installation is a product bug.
- **No fake completion.** Checklist complete only after `github_installations.verified_at` is set (live GitHub list shows ≥1 granted repo). Not after opening a tab, typed ID, spoofed query, or a P1 row with `status=active` and `verified_at` null.
- **GitHub owns consent.** We cannot click `github.com` for the user. Install URL / Setup URL / OAuth are the automations. Everything else is **guided HTML**.
- **Setup/Callback are public API GETs, not the SPA.** No `Depends(get_current_user)` — API auth is `HTTPBearer` (`backend/app/core/auth.py`); GitHub’s browser GET has no `Authorization`. Bind from HMAC install `state`. `ProtectedRoute` saves `location.pathname` only. Do not use `/installations?setup=1` or `/settings/integrations/github/callback`.
- **Do not trust `installation_id` on the Setup URL.** GitHub documents spoofing. Bind via signed `state` started in Revy, then a **user access token** that proves this GitHub user can admin that installation ([About the setup URL](https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/about-the-setup-url)). App JWT `GET /app/installations/{id}` is necessary and not sufficient.
- **Start in Revy, not on github.com.** Installing the App first, then hoping Revy notices, is the orphan deadlock. Sentry/Greptile/Linear all start from the product.
- **One config for paste values.** Webhook URL, permissions, events from [GITHUB_APP_TARGET_CONFIG.md](../utils/GITHUB_APP_TARGET_CONFIG.md) / env — not a second table in the wizard.
- **Secrets stay server-side.** PEM / webhook secret / GitHub App client secret never in the browser.
- **EN+LV, `--app-*`, unit tests only.**
- **Do not re-implement review.** No new pipeline tables. This is connect + verify, then existing R0–R8 run.

---

## Terminology

| Term | Meaning |
|------|---------|
| **GitHub App** | One Revy App (`GITHUB_APP_ID`). Settings `https://github.com/settings/apps/<slug>`. |
| **Installation** | One install on a user/org. URL `https://github.com/settings/installations/<id>`. **Not** the App ID. |
| **Install URL** | `https://github.com/apps/<slug>/installations/new?state=…` — user picks repos. |
| **Setup URL** | Public API GET. GitHub redirects here after install/update with `installation_id` + `setup_action` + install `state`. **Prod:** `https://revy.createit.digital/api/v1/github/setup`. **Local:** `http://localhost:8000/api/v1/github/setup`. |
| **Callback URL** | Public API GET. GitHub user OAuth `code` + OAuth `state` (not the install `state`). **Prod:** `https://revy.createit.digital/api/v1/github/callback`. **Local:** `http://localhost:8000/api/v1/github/callback`. |
| **Install `state`** | HMAC/JWT on the Install URL: workspace_id, user_id, nonce, exp. TTL **1800s**. No consume table. Public hops bind `workspace_id` + `user_id` from this blob — not a live Keycloak/JWT session. |
| **OAuth `state`** | Separate CSRF + `redirect_uri` = Callback URL. Setup hop stashes `installation_id` in a signed cookie (**SameSite=Lax**) or equivalent blob for the Callback hop. Strict would drop the stash on GitHub’s top-level GET. |
| **Orphan webhook** | `installation` / `installation_repositories` for an id **not** in `github_installations` → log + 200, **no row**. **Expected** on first install (GitHub fires before the browser hits Setup). |
| **Dogfood repo** | `raimondskrauklis/saas-base` — P4 experiment only. Product verify is ≥1 granted repo. |

---

## What exists vs genuinely new

### Verified — Revy product (this tree)

| Layer | What | Evidence |
|-------|------|----------|
| Manual register | Admin types installation id + account fields | `frontend/src/features/installations/pages/InstallationsPage.tsx`; i18n “Dev-only manual registration until the webhook phase ships” (stale copy — webhooks **did** ship) |
| POST create | Workspace admin, plan gate `installations.create`; **no GitHub call**; same-workspace duplicate **409** | `installations.py`; `create_github_installation`; `_installation_conflict` |
| Webhooks | HMAC ingest; unknown `installation` **and** `installation_repositories` orphan (log + 200, no row) | `apply_installation_webhook_event`; `github_repository_orphan_installation` |
| GitHub API | App JWT, installation tokens, **list repos**; **no** `GET /app/installations/{id}` | `github_api.py` `list_installation_repositories`; only `/app/installations/{id}/access_tokens` |
| R1 sync | Explicit enqueue, not automatic on create | `enqueue_installation_repository_sync` |
| Pipeline | Index → review → judge → publish | R0–R8 shipped |
| Checklist | `connect_integration` complete iff `installationCount > 0` | `checklistSteps.ts` — **row existence**, not GitHub verify. Create always sets `status=active`. No `verified_at` on ORM or FE type yet |
| SPA query drop | Unauthenticated visit to `/installations` keeps **pathname only** | `ProtectedRoute.tsx` `state={{ from: location.pathname }}`; `LoginPage` uses `from` as Keycloak `redirectUri` |
| API auth | JWT via `Authorization: Bearer`, not cookies | `HTTPBearer` — `backend/app/core/auth.py` |
| Operator docs | Create App, permissions, ID mix-up trap | [GITHUB_APP_SETUP.md](../utils/GITHUB_APP_SETUP.md) |
| Target App fields | SPA placeholders (must not go live) | Setup `/installations?setup=1`; Callback `/settings/integrations/github/callback` (route **missing**) |
| Pipeline lock | Q10 **reopened** to this folder | [REVIEW_PIPELINE_FINDINGS.md](../review-pipeline/REVIEW_PIPELINE_FINDINGS.md) |
| App OAuth client | **Unused.** `.env.example`: client secrets not used | No `GITHUB_CLIENT_ID` / slug in settings |

### Verified — GitHub origin (2026-09-19)

[Manifest flow](https://docs.github.com/en/apps/sharing-github-apps/registering-a-github-app-from-a-manifest): POST `manifest` to `…/settings/apps/new` → `code` → `POST /app-manifests/{code}/conversions` within one hour. Used when **creating** an App, not when **installing** an existing Revy App.

[Install from a third party](https://docs.github.com/en/apps/using-github-apps/installing-a-github-app-from-a-third-party): product sends the user to `/apps/{slug}/installations/new`. Optional `state` is returned to Setup URL.

**GitHub conflict (target config):** “Request user authorization (OAuth) during installation” **disables Setup URL**; users go to Callback URL instead. Target config currently wants **both** that checkbox (prod) **and** Setup URL + Redirect on update. Those cannot be live together. **Locked Q8:** keep Setup URL + Redirect on update; start user OAuth **from the Setup handler** (Sentry). Uncheck GitHub’s OAuth-on-install.

### Genuinely new

- Authenticated **start-connect** API (JWT + `admin:users` + `installations.create`) mints install `state` and returns the Install URL. HMAC secret stays server-side.
- Public backend **GET Setup** then **GET Callback** (302), not SPA routes. **No JWT** on those hops. Bind `workspace_id` + `user_id` from install HMAC; GitHub user-token proves installer. SameSite=Lax stash cookie.
- Two `state` values: install HMAC (workspace, user, nonce, TTL 1800s) vs OAuth CSRF; Setup stashes `installation_id` for Callback.
- **Install Revy** button → start-connect → GitHub Install URL (env slug).
- Two-hop persist: Setup captures GitHub query → OAuth → Callback proves installer (`GET /user/installations`) → App JWT `GET /app/installations/{id}` (new helper) → bind row. Discard the user token. Plan gate on persist uses HMAC `workspace_id` (load workspace; no Bearer).
- Same workspace + same GitHub id → **idempotent** bind (Redirect-on-update). Other workspace → existing unique conflict.
- `verified_at` (nullable, handwritten Alembic) on `github_installations` **and** list API/FE type. Checklist uses it, not row count, in the **same** phase as the column (Q21). Existing `status=active` rows backfilled once.
- After persist: enqueue existing `sync_installation_repositories`. First orphan webhooks stay expected; do not create rows from webhooks.
- Instruction cards + Configure deep-link when the **granted-repo list is empty** (not “missing saas-base”).
- Plan gate `installations.create` on **start-connect** and persist.

### Reuse caveats / traps

| Trap | Detail |
|------|--------|
| **App ID vs installation ID** | [GITHUB_APP_SETUP.md](../utils/GITHUB_APP_SETUP.md) — mixing them is the default failure. Wizard must never use one label for both. |
| **Register-first deadlock** | Webhook will **not** create the installation. Today you must POST the form **before** GitHub events mean anything. |
| **Spoofed Setup URL** | Query `installation_id` is attacker-controlled. Persist only after signed `state` + user-token association check. |
| **SPA Setup/Callback** | Pathname-only login drop. **Reject** current target-config SPA URLs. |
| **JWT on Setup/Callback** | `HTTPBearer` — GitHub GET has no `Authorization`. Requiring Keycloak/JWT re-breaks the hop (Q20). |
| **SameSite=Strict stash** | Drops `installation_id` cookie on GitHub’s top-level GET. Use **Lax**. |
| **Naive create on update** | Same-workspace `create_github_installation` **409s**. Redirect-on-update must upsert/re-verify. |
| **P1 row = checklist today** | `status=active` + `installationCount > 0` completes Connect GitHub without verify. Column + checklist + backfill land together (Q19, Q21). |
| **Expected first orphans** | GitHub sends `installation` + `installation_repositories` **before** Setup. Not a product bug. Enqueue R1 after persist. |
| **OAuth-on-install vs Setup URL** | GitHub mutually exclusive. We need Setup URL for Redirect on update. |
| **Stale i18n** | Form still says “until the webhook phase ships”. |
| **Q10 stale defer** | Obsolete; this program is the reopen. |
| **saas-base is not the app** | Dogfood **repo** only. Product verify is ≥1 granted repo (Q16). |
| **No slug in env** | Need `GITHUB_APP_SLUG` matching the live App. |

---

## Catalog — wizard tracks

### Track 1 — New Revy user (ours)

Keycloak register → Mode A/B → workspace. **Exists.** Wizard after `me.status === active`. POST install today requires `admin:users`.

### Track 2 — Install existing Revy App on the user’s repos — **recommended**

Revy already has **one** GitHub App (env PEM + webhook secret). Tenant should not create a second App.

1. In Revy: Connect GitHub via **start-connect** API (JWT + plan gate; mints install `state`).
2. GitHub Install URL → pick repos (**Only select repositories**; dogfood will pick saas-base).
3. Browser hits **public Setup GET** (`installation_id`, `setup_action`, install `state`). No JWT. Stash id (SameSite=Lax); start OAuth.
4. Browser hits **public Callback GET** (`code`, OAuth `state`). HMAC bind + user-token association + App JWT metadata → idempotent bind. Enqueue R1 sync. `verified_at` still null.
5. Live `list_installation_repositories`: ≥1 granted repo → set `verified_at`. Empty list → Configure on GitHub, checklist stays incomplete. Existing R0–R8 handles PRs on granted repos.

What stays **guided HTML:** repo picker, org owner / SSO, GitHub **Configure** if the allow-list is empty.

### Track 3 — Guided settings (GitHub HTML we cannot skip)

| GitHub page | URL pattern | When |
|-------------|-------------|------|
| Install App | `/apps/{slug}/installations/new?state=…` | Happy path |
| Installation | `/settings/installations/{id}` | Support / add repos (Vercel “Configure GitHub App”) |
| App settings | `/settings/apps/{slug}` | **Us** (platform App), not the tenant |
| Repo settings | `/{owner}/{repo}/settings` | Orientation; dogfood saas-base |
| Actions secrets | `/{owner}/{repo}/settings/secrets/actions` | **Out** (Q2) |

### Track 4 — Manifest (create an App) — **not the tenant path**

Revy **operators** already created the App via runbooks. Manifest is for “register this preconfigured App as a new GitHub App”. **Defer** for tenants. Optional later for self-hosted Revy.

---

## Advice / options

| Option | Verdict |
|--------|---------|
| **A — Install URL + public API Setup/Callback + user OAuth from Setup hop + verify** | **Adopt.** Fulfills Q10. Unblocks saas-base dogfood without typed IDs. Matches Sentry + GitHub’s spoof warning. Not the SPA placeholders. |
| **B — Deep-links only** | **Partial.** Keep for SSO / org-owner / Configure. Not enough — deadlock + fake checklist remain. |
| **C — Manifest per workspace** | **Reject** for hosted Revy. We already own the App. |
| **D — Automate github.com in a browser** | **Reject.** |
| **E — Keep manual form as happy path** | **Reject.** Keep as **admin/dev fallback** (Q6). |
| **F — GitHub “Request OAuth during installation”** | **Reject.** Disables Setup URL; we need Redirect on update. |
| **G — Login-with-GitHub as Revy identity** | **Reject.** Keycloak stays (Q9). GitHub OAuth is **installer proof**, not login. |
| **H — Marketplace listing** | **Defer.** Setup URL is a prerequisite; listing is not this program. |
| **I — Greptile per-repo Enable UI** | **Defer (Q11).** Revy already reviews every granted repo when workspace autostart is on. v1 = GitHub allow-list + copy “Only select repositories”. |
| **J — Greptile CLI / member “bridge app”** | **Reject** for this program. |

---

## External research / patterns

Verified 2026-09-19 against public docs (not our accounts). **Direct functional rival for this wizard: Greptile.** Closest **Setup URL / spoof** analogue remains **Sentry**.

### Direct rival — Greptile

Public docs: [quickstart](https://www.greptile.com/docs/quickstart), [GitHub integration](https://www.greptile.com/docs/integrations/github-gitlab-integration), [CLI onboard](https://www.greptile.com/docs/code-review/cli-onboarding), [orgs & teams](https://www.greptile.com/docs/code-review/team-setup-basics), [org not listed](https://www.greptile.com/docs/troubleshooting/common-issues), self-host env in [manual setup](https://www.greptile.com/docs/docker-compose/manual-setup). App slug: [`greptile-apps`](https://github.com/apps/greptile-apps). **Not verified:** a live Greptile account (no screenshots from our login).

They split **account** from **App install**, then split **GitHub access** from **review-enabled**:

| Layer | Greptile | Revy today | This program |
|-------|----------|------------|--------------|
| 0. Product login | Email / Google / GitHub / GitLab. CLI `greptile login` creates the account. | Keycloak | Unchanged (Q9). |
| 1. Start in product | **Admins only:** Code Providers → Connect GitHub Cloud / Add Provider. Members never see Code Providers. | Typed ID form (`admin:users`) | Adopt admin start (Q4). |
| 2. GitHub App install | Redirect to **one** platform App (`greptile-apps`). Pick account/org; All vs Only select repos; Install / Update / Configure. | Operator runbook | Adopt Install URL from Revy. |
| 3. Return + **Link** | GitHub “automatically returns you”; user **selects the org and clicks Link**. CLI: if exactly one unclaimed org, auto-link. Org missing = App not installed **or** SSO identity mismatch. | Webhook orphan unless row exists | Adopt explicit bind (our Setup persist). Same global uniqueness: “Every organization is already linked to another workspace” = our `github_installation_id` conflict. |
| 4. **Enable repos** | Second picker: Enable / Enable All. **Onboarding cannot finish with zero repos.** Auto-enable new repos is a later admin toggle. | R1 syncs all granted repos; R8 autostart is **workspace-wide** | **Do not copy Enable UI (Q11).** Instruct “Only select repositories”. Product checklist = `verified_at` after ≥1 granted repo (Q16). |
| 5. First PR | ~3 min review; `@greptileai` on older PRs | R0–R8 + `@revy review` | Dogfood PR on saas-base. |

**Greptile copy we should steal:**

- **Authorize ≠ install.** CLI: “authorizing Greptile is not enough. You must finish the install and grant repository access.” Two GitHub screens (user OAuth + App install). Matches Q8 (OAuth from Setup) without using GitHub as IdP.
- **Configure existing install** at `github.com/apps/greptile-apps` (add/remove repo access); dashboard only toggles review. Same split as Vercel Configure.
- **SSO mismatch:** disconnect in product → uninstall App → sign in with company SSO → reinstall → Link. Our `state` TTL must survive SSO; full reinstall is the recovery playbook, not a silent retry.
- **Empty repo list while syncing** — wait / retry, do not mark connected.
- Conflict copy: invite to the other workspace, or install on an org you own — better than a raw `ConflictError`.

**Greptile we must not copy:**

- GitHub as signup/IdP (Q9). They allow it; we do not.
- Invited-member path: link **personal** GitHub profile + install a **bridge app** for “Fix with your Agent”. Different App, not org connect. **Out.**
- `greptile onboard` CLI / agent playbook (10 min poll, print URL for SSH). **Defer.**
- GitLab paste-token + manual webhook. That is what we are **leaving**. Their GitHub path never asks the user to type an installation id.
- Self-host GHES App + `GITHUB_CLIENT_ID` / `CLIENT_SECRET` on the operator box — we already need those env vars for hosted OAuth (P0); GHES itself **defer**.

### Other products (shorter)

| Product | What they do | Adopt / defer / reject for Revy |
|---------|--------------|----------------------------------|
| **Sentry** | Start in Sentry, not github.com. Setup URL; then OAuth. Manual-install-first 500s / orphans. | **Adopt** product-first + Setup URL + OAuth from that handler. |
| **Linear** | Admin Enable. Org install needs GitHub org owner. Then map repos. | **Adopt** admin-only start + org-owner copy. GHES **defer**. |
| **Vercel** | Import → App if needed → repo list. Missing repo → Configure GitHub App deep-link. | **Adopt** Configure deep-link. |
| **CodeRabbit** | Login-with-GitHub **and** Install & Authorize. Preserve wizard ~30 min. | **Adopt** preserve `state`. **Reject** GitHub as Revy IdP. |
| **Marketplace** | Setup URL required; OAuth from Setup; `state` on install URL. | **Defer** listing. **Adopt** `state` + Setup URL. |

**Shared pattern:** one **platform** GitHub App; tenant **installs** it; product UI starts the flow; GitHub HTML is only consent + repo picker.

---

## Data scope & exclusions

**In:**

- Revy UI + API for connect / OAuth-from-setup / verify.
- Public Setup + Callback GETs (Q12, Q20) — no Revy JWT. Target config paste values updated in P0 (OAuth-on-install **unchecked**). Live GitHub App dashboard paste in **P4**.
- Env: `GITHUB_APP_SLUG`, `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET` (server). `.env.example` + `deploy/env-examples/backend.env.production.example`.
- `verified_at` on `github_installations` (handwritten Alembic) + list API/FE + checklist switch + grandfather backfill (Q21). Not a new pipeline table.
- EN+LV wizard.
- Dogfood (P4): new user enables Revy on `raimondskrauklis/saas-base`.

**Out:**

- Implementing this in the saas-base **codebase**.
- Review pipeline features (already shipped).
- Keycloak realm automation; GitHub as login.
- Filling saas-base **Actions secrets** / droplet deploy (Q2).
- Creating a new GitHub App per customer.
- GitHub Marketplace listing; GHES; Manifest-for-tenants.
- Greptile-style per-repo Enable / Auto-enable UI; member bridge app; CLI onboard.

---

## Edge cases

1. **Expected first orphans** — GitHub sends `installation` + `installation_repositories` before Setup. Log + 200. After persist, enqueue R1 `sync_installation_repositories`. Do not create rows from webhooks.
2. **Spoofed `installation_id`** — ignore without matching signed `state` + user-token association.
3. User vs org install URLs; org may require org owner (Linear).
4. SSO interstitial — install `state` TTL **1800s** (Q14).
5. Add/remove repos later — Redirect on update hits Setup again; **idempotent** same workspace+id (Q15); re-run verify.
6. `suspended` / `removed` — webhook already updates status **if** the row exists.
7. Plan gate `installations.create` — gate **start-connect** and persist; `plan_upgrade_required` copy, not GitHub failure (Q18).
8. Mode B user never reaches wizard (`ProtectedRoute` already).
9. One `github_installation_id` globally unique — other workspace `ConflictError` (copy: invite vs org you own).
10. **Empty granted-repo list** — live `list_installation_repositories` empty → Configure, not checklist complete. Do not use local `github_repositories` (orphaned until R1).
11. User hits Setup URL without starting in Revy — no install `state` → guided “start Connect GitHub in Revy”, do not persist.
12. **OAuth without App install** — do not persist; copy: authorize ≠ install.
13. **Org already linked** — unique constraint; Greptile-style copy.
14. Persist happens **on Callback after GitHub created the install** — `github_installation_id` is unknown before that. Not “before redirect”.
15. **No Revy JWT on GitHub return** — Setup/Callback must succeed without `Authorization` (Q20).
16. **Existing installs after checklist switch** — grandfather `verified_at` for current `status=active` rows in the same migration (Q21).

---

## Decisions registry

| Q# | Question | Status | Resolution |
|----|----------|--------|------------|
| Q1 | Program home | **locked** | **Revy.** saas-base is dogfood **repo**, not the app we change. |
| Q2 | Dogfood = install Revy on saas-base vs also guided deploy/Actions secrets? | **locked** | **Install + review only.** No Actions/secrets/deploy onboard. Matches every vendor we checked. |
| Q3 | Platform App (Track 2) vs Manifest per tenant? | **locked** | Track 2 — Revy already has the App. |
| Q4 | Who may start connect — workspace admin only? | **locked** | **Workspace admin** (`admin:users`), same as today’s POST. Linear/CodeRabbit are admin/owner to enable. GitHub may still let a repo admin click Install; Revy will not bind the workspace unless an admin completes Setup. |
| Q5 | Checklist complete = GitHub-verified? | **locked** | Yes — `verified_at` set after live list shows **≥1 granted repo**. Not row count. Q6 fallback uses the same rule. |
| Q6 | Keep manual ID form? | **locked** | **Admin/dev fallback only.** Not the happy path. Still must pass Q5 before checklist. |
| Q7 | Reopen pipeline Q10 here vs fold into review-pipeline docs? | **locked** | Parallel folder `docs/github-onboarding/`; Q10 is the ancestor lock. |
| Q8 | GitHub “Request OAuth during installation” vs Setup URL? | **locked** | **Setup URL + Redirect on update.** Start user OAuth **from the Setup hop**. Uncheck OAuth-on-install. |
| Q9 | GitHub as Revy login (CodeRabbit-style)? | **locked** | **No.** Keycloak stays. GitHub OAuth is installer proof only. Greptile allows GitHub signup; we do not copy that. |
| Q11 | Greptile third layer — per-repo Enable vs GitHub allow-list? | **locked** | **Allow-list is enable for v1.** Workspace `review_autostart_enabled` already reviews every granted repo. Wizard copy: pick **Only select repositories**. Per-repo Enable / Auto-enable dashboard **defer**. |
| Q12 | Setup + Callback URLs | **locked** | Public API GETs, not SPA. Prod `https://revy.createit.digital/api/v1/github/setup` and `…/github/callback`. Local `http://localhost:8000/api/v1/github/setup` and `…/callback`. After persist, 302 to SPA `/installations`. |
| Q13 | Two `state` values | **locked** | Install HMAC (workspace, user, nonce, exp) on Install URL. OAuth CSRF + `redirect_uri`=Callback. Setup stashes `installation_id` in a **SameSite=Lax** signed cookie (or equivalent blob). |
| Q14 | Install `state` TTL / nonce consume | **locked** | **1800s.** HMAC/JWT, **no** consume table. Replay in-window is bound to HMAC `user_id` + `workspace_id` (not a live Keycloak session). Same-workspace persist is idempotent. |
| Q15 | Persist on Redirect-on-update | **locked** | Same workspace + same GitHub id → idempotent bind, then re-verify. Other workspace → unique conflict. Do not call naive `create_github_installation`. |
| Q16 | Product verify target | **locked** | **≥1 granted repo** via live `list_installation_repositories`. `saas-base` is **P4 dogfood only**, not the product predicate. Empty list → Configure `/settings/installations/{id}`. |
| Q17 | First-install webhooks | **locked** | Orphans are **expected**. Enqueue existing `sync_installation_repositories` after persist. Do not create rows from webhooks. |
| Q18 | Plan gate | **locked** | `installations.create` on **start-connect** (JWT) and persist (workspace loaded from HMAC `workspace_id`). Wizard maps `plan_upgrade_required`. |
| Q19 | P1 row vs checklist | **locked** | `verified_at` nullable. New inserts leave it **null** until P3 live verify. Checklist `connect_integration` iff ≥1 row with `verified_at` set. Status enum stays GitHub `active`/`suspended`/`removed`. |
| Q20 | Auth on Setup/Callback | **locked** | Public hops. **No** `Depends(get_current_user)`. Bind from HMAC + GitHub user token. Start-connect is the JWT/admin/plan-gate surface. |
| Q21 | Checklist + backfill with column | **locked** | P1 ships `verified_at` column, list API/FE field, checklist switch, and one-time backfill `verified_at = created_at` for existing `status=active` rows (grandfather current connects). Do not land the column while checklist still uses row count. |

---

## Parking lot

- Fix stale “until webhook phase” i18n in the same UI change.
- Point live GitHub App **Setup URL** + **Callback URL** at the Q12 paths in **P4** (P0 ships docs + env shape only).
- Self-hosted Manifest path (not v1).
- Marketplace listing (not v1).
- Greptile Enable / Auto-enable new repos UI (Q11).
- Member personal GitHub profile + bridge app.

**Phase-0 (code + docs, not live App click):** Env `GITHUB_APP_SLUG` / `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET`; target config Q8 + Q12 URLs; signed install `state`. Live dashboard paste waits for P4 so dogfood hits the real hops.

---

## Devil's advocate

- **“Webhooks already exist.”** They do not **create** the workspace link. Orphan policy is why onboarding still feels like a runbook.
- **“Put the wizard in saas-base.”** Wrong app. saas-base has no review client; Revy is what must be installed on that GitHub repo.
- **“App JWT GET is enough verify.”** GitHub’s own warning: `installation_id` is spoofable. Another tenant’s unbound install could be stolen without user-token association.
- **“Put Setup on `/installations?setup=1`.”** Pathname-only Keycloak return drops GitHub query params. Public API hops (Q12).
- **“Require Keycloak JWT on Setup GET.”** Auth is `HTTPBearer`. GitHub’s redirect has no `Authorization`. HMAC bind (Q20).
- **Manifest for every customer.** Duplicates App ownership; we already have PEM in env.
- **“Copy Greptile Enable.”** Would be a new per-repo product flag. R8 already autostarts every repo on the installation. Wrong scope for connect.

---

## Experiment / verification

New Keycloak user on **Revy** (`revy.createit.digital` / local), GitHub account that can install on `raimondskrauklis/saas-base`:

| Gate | Pass | Fail |
|------|------|------|
| User never types installation id | Yes | Manual form is the only path |
| Flow starts in Revy, not github.com | Yes | Manual-install-first; orphan webhook |
| Install URL opens repo picker including saas-base | Yes | App ID used as install URL |
| Callback persists only after HMAC state + user-token check (no Revy JWT on the hop) | Yes | Persist on raw query `installation_id` or `Depends(get_current_user)` 401 |
| `GET /app/installations/{id}` 200 and **≥1 granted repo** | Yes | 404 / empty allow-list marked complete |
| Checklist complete **after** `verified_at` | Yes | Complete on typed junk, P1 row, or install redirect alone |
| Open a PR on saas-base → Revy check runs | Yes | Connected in UI, pipeline silent |
| EN+LV on every step | Yes | Raw GitHub chrome as copy |
| Redirect-on-update (add repo) does not 409 | Yes | Naive create_github_installation |

---

## References

- `backend/app/api/v1/workspaces/installations.py`
- `backend/app/services/github_installations.py` (`create_github_installation`, `apply_installation_webhook_event`)
- `backend/app/integrations/github_api.py`
- `backend/app/core/auth.py` (`HTTPBearer`)
- `frontend/src/features/installations/`
- `frontend/src/components/auth/ProtectedRoute.tsx` (`from: location.pathname`)
- `frontend/src/features/dashboard/checklistSteps.ts`
- [REVIEW_PIPELINE_FINDINGS.md](../review-pipeline/REVIEW_PIPELINE_FINDINGS.md) Q10, orphan trap
- [GITHUB_APP_SETUP.md](../utils/GITHUB_APP_SETUP.md)
- [GITHUB_APP_TARGET_CONFIG.md](../utils/GITHUB_APP_TARGET_CONFIG.md) (SPA placeholders — do not paste live)
- [pass-01](./reviews/architecture-peer-review/pass-01-2026-09-19.md)
- [pass-02](./reviews/architecture-peer-review/pass-02-2026-09-19-delta.md)
- [About the setup URL](https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/about-the-setup-url) (spoof warning)
- [Sharing a GitHub App](https://docs.github.com/en/apps/sharing-github-apps/sharing-your-github-app) (`state` on install URL)
- Sentry: [docs.sentry.io GitHub](https://docs.sentry.io/integrations/source-code-mgmt/github/) · [develop.sentry.dev](https://develop.sentry.dev/integrations/github/)
- Linear: [linear.app/docs/github](https://linear.app/docs/github)
- Vercel: [vercel.com/docs/git/vercel-for-github](https://vercel.com/docs/git/vercel-for-github)
- Greptile (rival): [quickstart](https://www.greptile.com/docs/quickstart) · [GitHub/GitLab integration](https://www.greptile.com/docs/integrations/github-gitlab-integration) · [CLI onboard](https://www.greptile.com/docs/code-review/cli-onboarding) · [orgs & teams](https://www.greptile.com/docs/code-review/team-setup-basics) · [org not listed](https://www.greptile.com/docs/troubleshooting/common-issues) · [self-host GitHub env](https://www.greptile.com/docs/docker-compose/manual-setup)
- CodeRabbit: [docs.coderabbit.ai GitHub](https://docs.coderabbit.ai/platforms/github-com)
