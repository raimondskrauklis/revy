# docs/github-onboarding/GITHUB_ONBOARDING_P0_EXECUTION.md

# P0 — Foundations (execution)

Phase **P0** of [`GITHUB_ONBOARDING_GENERAL_PLAN.md`](./GITHUB_ONBOARDING_GENERAL_PLAN.md). Baseline: [`GITHUB_ONBOARDING_FINDINGS.md`](./GITHUB_ONBOARDING_FINDINGS.md) Q8, Q12–Q14, Q20. **P0 only.**

**Goal:** Env can name the live App and mint install HMAC `state`; target config paste values match Q8 + Q12 (not SPA placeholders).

## Decisions locked for P0

- Q8 — OAuth-on-install **unchecked**; Setup URL + Redirect on update **on**.
- Q12 — Setup `…/api/v1/github/setup`, Callback `…/api/v1/github/callback` (prod host `https://revy.createit.digital`, local `http://localhost:8000`).
- Q13–Q14 — install HMAC payload `{workspace_id, user_id, nonce, exp}`; TTL **1800s**; no consume table.
- Q20 — HMAC secret is server-side; no JWT on hops (hops are P1).
- HMAC-SHA256 key = `GITHUB_CLIENT_SECRET` (same secret used later for OAuth token exchange). Empty secret → mint/verify fail closed (`ServiceUnavailableError`). Rotating the client secret invalidates in-flight install `state` (TTL 1800s).
- `GITHUB_OAUTH_PUBLIC_BASE` is the API origin GitHub redirects the **browser** to (no trailing slash). Prod `https://revy.createit.digital`; local `http://localhost:8000`. Setup/Callback URLs = `{base}/api/v1/github/setup` and `{base}/api/v1/github/callback`. **Do not** substitute `APP_PUBLIC_URL` (that is the SPA: local `http://localhost:5173`).
- Live GitHub App dashboard paste stays **P4**.

## PR review context (required when code + docs ship in one PR)

- **SSOT (Moonshot inject):** `.revy/review-context.json` — `active_program: "github-onboarding"`; `programs[]` = **one entry only**; `scope`: `["backend/**", "frontend/**"]`; three doc paths below.
- **Bugbot:** `.cursor/BUGBOT.md` — active program github-onboarding + same three docs.
- **Agent mirror:** copy SSOT to `.agent/review-context.json`.
- **Do not** wire Greptile as a reviewer. Leftover `.greptile/files.json` may be regenerated from SSOT so CI unit tests do not drift — it is not babysat.

**Doc paths (SSOT `paths[]` only):**

- `docs/github-onboarding/GITHUB_ONBOARDING_P0_EXECUTION.md`
- `docs/github-onboarding/GITHUB_ONBOARDING_FINDINGS.md`
- `docs/github-onboarding/GITHUB_ONBOARDING_GENERAL_PLAN.md`

## Out of scope for P0 (later phases)

- Public GET Setup/Callback, persist, cookies → **P1**
- Start-connect JWT API, wizard UI → **P2**
- Live repo verify / set `verified_at` → **P3**
- Live App form paste, dogfood, Q10 shipped → **P4**

---

## P0.0 — Program PR review context (SSOT + Bugbot)

**What:** Switch SSOT to `github-onboarding`; one program entry; update Bugbot; copy the same JSON to `.agent/review-context.json` (workflow mirror).

**Files:** `.revy/review-context.json`, `.agent/review-context.json`, `.cursor/BUGBOT.md`

**Deliverable:**

```bash
python -m json.tool ../.revy/review-context.json > /dev/null
pipenv run pytest tests/unit/test_engineering_context_manifest.py -q
```

---

## P0.1 — Settings + env examples

**What:** Add `github_app_slug`, `github_client_id`, `github_client_secret`, `github_oauth_public_base` on `Settings`. Properties `github_setup_url` / `github_callback_url` concatenate Q12 paths. Remove `.env.example` line that client secrets are unused. Same keys on `deploy/env-examples/backend.env.production.example`.

**Files:** `backend/app/core/config.py`, `backend/.env.example`, `deploy/env-examples/backend.env.production.example`

**Deliverable:** settings expose slug + OAuth client + public base; example env documents prod vs local Q12 hosts; comments say hops use `GITHUB_OAUTH_PUBLIC_BASE`, not `APP_PUBLIC_URL`.

```bash
cd backend && pipenv run ruff check app/core/config.py
```

---

## P0.2 — Install HMAC `state` mint/verify

**What:** New helper `mint_install_state` / `verify_install_state` (url-safe HMAC, TTL 1800s, payload workspace_id + user_id + nonce + exp). Reject missing/expired/tampered. No DB row. Unit tests only.

**Files:** `backend/app/services/github_install_state.py` (new), `backend/tests/unit/test_github_install_state.py` (new)

**Deliverable:** valid mint round-trips; expired and flipped workspace_id fail.

```bash
cd backend && pipenv run pytest tests/unit/test_github_install_state.py -q
```

---

## P0.3 — Target config Q8 + Q12

**What:** Replace SPA Callback `/settings/integrations/github/callback` and Setup `/installations?setup=1` with Q12 API URLs. Uncheck “Request user authorization (OAuth) during installation”. Redirect on update on. Note live dashboard paste is P4.

**Files:** `docs/utils/GITHUB_APP_TARGET_CONFIG.md`

**Deliverable:** that file no longer lists mutually exclusive GitHub checkboxes or SPA hops.

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_github_install_state.py tests/unit/test_engineering_context_manifest.py -q
pipenv run ruff check app/core/config.py app/services/github_install_state.py
```

**Deploy:** env shape only; do not paste Setup/Callback on the live App until P4.

**Next:** [`GITHUB_ONBOARDING_P1_EXECUTION.md`](./GITHUB_ONBOARDING_P1_EXECUTION.md)
