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

**Requires P2 APIs/UI:** `POST /users/complete-profile`, admin pending list, approve/reject — not available in P1.

---

## Warnings

- Change **both** sides when toggling modes; restart API and Vite dev server after env edits.
- `VITE_*` are baked at **build time** in production CI — set GitHub secrets to match droplet `REGISTRATION_*`.
- Edge case: `/me` may briefly show `pending_profile` while Mode A auto-activates — see [SCAFFOLD_FINDINGS.md](./SCAFFOLD_FINDINGS.md) § Edge cases.
