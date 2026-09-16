# .revy/rules/frontend.md

# Frontend

React 19, strict TS, TanStack Query for server state (not Zustand). Zustand is UI only.

- Colors: `--tp-*` via `bg-[color:var(--tp-…)]`. `--tp-warning` not `--tp-warn`. No `bg-blue-500`, `#fff`, hex in product UI.
- Borders: `ring-1 ring-[color:var(--tp-ring)]` — not `border` / `border-gray-200`.
- Focus: `focus-visible:ring-2 ring-[color:var(--tp-ring-strong)]`. Touch targets ≥ 44px.
- Inputs: `QuietInput` / `QuietSelect` / `QuietDateInput` / Quiet chips — not native `<input type="date">` or `<select>`. Zebra rows: Quiet chips `placement="dataRow"` where needed.
- Dates: `@/lib/date`. Locales: `getIntlLocale()` — not `'en-GB'` / `'lv-LV'` / bare `toLocaleString()`.
- Errors: `mapApiError` → `showDomainErrorToast`. Toasts: Sonner only.
- i18n: every user-facing string via `t()`; feature namespace, not a growing root `en.json` for new screens.
- Colocate `api.ts` / `hooks.ts` / `types.ts`. Do not copy `features/profiles/` mock data.
