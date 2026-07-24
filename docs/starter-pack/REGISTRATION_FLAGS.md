# Registration flags (backend ↔ frontend)

Pair backend `REGISTRATION_*` with frontend `VITE_REGISTRATION_*`. **Mismatches cause confusing UX** (gates shown/hidden vs API behaviour).

**Authority:** `internal-docs/starter-pack/docs/backend/USER_REGISTRATION.md` (Mode A / Mode B).

**Related:** [DEV_BOOTSTRAP.md](./DEV_BOOTSTRAP.md) · [KEYCLOAK_DEV_CHECKLIST.md](./KEYCLOAK_DEV_CHECKLIST.md)

---

## Mode A — open SaaS (P1 default)

No admin approval, no profile form. User reaches dashboard after Keycloak login + email verification path.

| Backend (`backend/.env`) | Frontend (`frontend/.env.local`) | Value (Mode A) |
|--------------------------|----------------------------------|----------------|
| `REGISTRATION_REQUIRE_ADMIN_APPROVAL` | `VITE_REGISTRATION_REQUIRE_ADMIN_APPROVAL` | `false` |
| `REGISTRATION_REQUIRE_PROFILE_FORM` | `VITE_REGISTRATION_REQUIRE_PROFILE_FORM` | `false` |

**Backend behaviour:** auto-provision on first JWT; `maybe_auto_provision_user` may activate `pending_profile` users when both flags are false.

**Frontend behaviour:** `ProtectedRoute` does not block on profile/admin gates when both `VITE_*` are `false`.

---

## Mode B — gated registration (P2)

Admin approval and/or profile form required before `active` dashboard access.

| Backend | Frontend | Example (approval only) |
|---------|----------|-------------------------|
| `REGISTRATION_REQUIRE_ADMIN_APPROVAL` | `VITE_REGISTRATION_REQUIRE_ADMIN_APPROVAL` | `true` |
| `REGISTRATION_REQUIRE_PROFILE_FORM` | `VITE_REGISTRATION_REQUIRE_PROFILE_FORM` | `false` |

**Shipped in P2:** `POST /api/v1/users/complete-profile`, `GET /api/v1/admin/users/pending`, approve/reject APIs, `/complete-profile` form, `/admin/users` queue (platform `super_admin` only).

### Mode B verification (local)

1. Set on **both** backend `.env` and `frontend/.env.local`:

   ```text
   REGISTRATION_REQUIRE_ADMIN_APPROVAL=true
   VITE_REGISTRATION_REQUIRE_ADMIN_APPROVAL=true
   REGISTRATION_REQUIRE_PROFILE_FORM=true
   VITE_REGISTRATION_REQUIRE_PROFILE_FORM=true
   ```

2. Restart API + Vite. Register new user in Keycloak → verify email.
3. Complete profile at `/complete-profile` → `GET /api/v1/me` shows `pending_approval`.
4. As bootstrap `super_admin`, open `/admin/users` → approve → user reaches `active` + dashboard.

Optional: set only `REGISTRATION_REQUIRE_PROFILE_FORM=true` (admin approval false) to test profile form → immediate `active` after submit.

---

## Warnings

- Change **both** sides when toggling modes; restart API and Vite dev server after env edits.
- `VITE_*` are baked at **build time** in production CI — set GitHub secrets to match droplet `REGISTRATION_*`.
- Edge case (`pending_profile` + Mode A): when both `REGISTRATION_REQUIRE_*` are `false`, `maybe_auto_provision_user` may activate on the same auth request while `/me` still briefly shows `pending_profile`. Frontend does not gate on `pending_profile` when `VITE_REGISTRATION_REQUIRE_PROFILE_FORM=false`. If auto-provision fails, user could reach the dashboard while `/me` still shows `pending_profile` — see [SCAFFOLD_FINDINGS.md](./SCAFFOLD_FINDINGS.md) § Edge cases.
