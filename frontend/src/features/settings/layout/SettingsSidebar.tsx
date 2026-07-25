// frontend/src/features/settings/layout/SettingsSidebar.tsx
import { NavLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

const PERSONAL_LINKS = [
  { to: '/settings/profile', label: 'settings.nav.profile' },
  { to: '/settings/security', label: 'settings.nav.security' },
  { to: '/settings/appearance', label: 'settings.nav.appearance' },
] as const;

const WORKSPACE_LINKS = [
  { to: '/settings/workspace', label: 'settings.nav.workspace' },
  { to: '/settings/team', label: 'settings.nav.team' },
  { to: '/settings/integrations', label: 'settings.nav.integrations' },
] as const;

function linkClassName({ isActive }: { isActive: boolean }): string {
  return [
    'block rounded-lg px-3 py-2 text-sm',
    'focus-visible:ring-2 ring-[color:var(--app-ring-strong)]',
    isActive
      ? 'bg-[color:var(--app-chip-active)] text-[color:var(--app-text-strong)]'
      : 'text-[color:var(--app-text-muted)] hover:bg-[color:var(--app-chip)]',
  ].join(' ');
}

export function SettingsSidebar() {
  const { t } = useTranslation();

  return (
    <nav
      className="w-full shrink-0 md:w-52"
      aria-label={t('settings.sidebar.label')}
    >
      <div className="space-y-6">
        <div>
          <h2 className="px-3 text-xs font-semibold uppercase tracking-wide text-[color:var(--app-text-muted)]">
            {t('settings.group.personal')}
          </h2>
          <ul className="mt-2 space-y-1">
            {PERSONAL_LINKS.map((item) => (
              <li key={item.to}>
                <NavLink to={item.to} className={linkClassName}>
                  {t(item.label)}
                </NavLink>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <h2 className="px-3 text-xs font-semibold uppercase tracking-wide text-[color:var(--app-text-muted)]">
            {t('settings.group.workspace')}
          </h2>
          <ul className="mt-2 space-y-1">
            {WORKSPACE_LINKS.map((item) => (
              <li key={item.to}>
                <NavLink to={item.to} className={linkClassName}>
                  {t(item.label)}
                </NavLink>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </nav>
  );
}
