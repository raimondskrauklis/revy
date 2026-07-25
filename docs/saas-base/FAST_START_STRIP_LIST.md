# Fast-start strip list

When cloning Revy starter-pack + SaaS base into a **new B2B product**, remove or replace these items. Keep W0–W8 shell; drop Revy domain slice.

---

## Product folders (delete or replace)

| Path | Action |
|------|--------|
| `frontend/src/features/installations/` | Remove — Revy GitHub installs |
| `frontend/src/features/reviewer/` | Remove — review pipeline UI |
| `backend/app/api/v1/installations/` | Remove |
| `backend/app/services/installations/` | Remove |
| `backend/app/models/installation*.py` | Remove + migration to drop tables |
| `docs/starter-pack/REVY_PRODUCT_SLICE.md` | Replace with product slice doc |
| `frontend/src/styles/tokens.revy.css` | Rename/rebrand (`tokens.<product>.css`) |

---

## Env keys (remove if unused)

| Key | Reason |
|-----|--------|
| `GITHUB_*` | Revy GitHub App |
| Product-specific S3/bucket keys | Not in base SaaS |

Keep: `KEYCLOAK_*`, `DATABASE_URL`, `STRIPE_*` (if billing), `EXPORT_*`, `BOOTSTRAP_SUPER_ADMIN_EMAIL` (one-time).

---

## Nav & extensions

| Item | Action |
|------|--------|
| `/installations` route + header link | Remove |
| `registerRevyExtensions()` in bootstrap | Remove; register product extensions |
| Settings → Integrations Revy card | Replace with product integration card or empty shell |
| Dashboard widgets tied to installations | Remove from registry |

---

## Docs

| Doc | Action |
|-----|--------|
| `AGENTS.md` product row | Update product name + slice link |
| `docs/saas-base/` | Keep as program reference or archive after fork |
| `internal-docs/product/revy/` | Replace with `internal-docs/product/<name>/` |

---

## Settings IA

Per [SETTINGS_IA.md](./SETTINGS_IA.md): sidebar lists **only shipped routes**. After strip, ensure integrations card deep-links to your product connect flow (or hide integrations group until W2 product card exists).
