// frontend/src/features/settings/layout/SettingsSidebar.tsx
import { NavLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/contexts/AuthContext';
import { hasPermission } from '@/lib/permissions';
import type { Permission } from '@/lib/permissionTypes';

const PERSONAL_LINKS = [
  { to: '/settings/profile', label: 'settings.nav.profile' },
  { to: '/settings/security', label: 'settings.nav.security' },
  { to: '/settings/appearance', label: 'settings.nav.appearance' },
] as const;

const WORKSPACE_LINKS: ReadonlyArray<{
  to: string;
  label: string;
  permission?: Permission;
}> = [
  { to: '/settings/workspace', label: 'settings.nav.workspace', permission: 'admin:users' },
  { to: '/settings/team', label: 'settings.nav.team' },
  { to: '/settings/integrations', label: 'settings.nav.integrations' },
  { to: '/settings/billing', label: 'settings.nav.billing', permission: 'admin:users' },
  { to: '/settings/danger', label: 'settings.nav.danger' },
];

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
  const { user } = useAuth();

  const workspaceLinks = WORKSPACE_LINKS.filter(
    (item) =>
      !item.permission
      || hasPermission(
        user?.role ?? undefined,
        item.permission,
        user?.platform_role ?? undefined,
      ),
  );

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
            {workspaceLinks.map((item) => (
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
