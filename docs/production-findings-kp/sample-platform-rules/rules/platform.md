# .revy/rules/platform.md

# Platform (shared)

Check the **whole file** for each path in the diff (unchanged lines count). Comment on violations. Soft line-count / taste is out of scope.

- Production behaviour: no swallowed errors, no fake success, no invented data.
- Domain exceptions / `mapApiError` — not bare `HTTPException` or `window.alert`.
- No secrets, credentials, or `.env` values in diffs.
- New user-facing copy is i18n (`t()`), not hardcoded English/Latvian in UI code.
