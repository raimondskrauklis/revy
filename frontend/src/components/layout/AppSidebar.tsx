// frontend/src/components/layout/AppSidebar.tsx
import { useState } from 'react';
import { Link, NavLink, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { LayoutDashboard, Plug, Settings, GitPullRequest, ChevronLeft, ChevronRight, ChevronDown } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { WorkspaceSwitcher } from '@/components/layout/WorkspaceSwitcher';
import { UserMenu } from '@/components/layout/UserMenu';
import { useAuth } from '@/contexts/AuthContext';
import { hasPermission } from '@/lib/permissions';
import { useExtensions } from '@/platform/extensions/hooks';
import { useSidebar } from '@/components/layout/SidebarProvider';
import { PERSONAL_LINKS, WORKSPACE_LINKS } from '@/features/settings/layout/settingsNavLinks';

type NavItem = {
  href: string;
  label: string;
  icon: LucideIcon;
};

const NAV_ITEMS: NavItem[] = [
  { href: '/dashboard', label: 'nav.dashboard', icon: LayoutDashboard },
  { href: '/reviewer', label: 'nav.reviewer', icon: GitPullRequest },
  { href: '/installations', label: 'nav.installations', icon: Plug },
];

const NAV_LINK_RADIUS = 'rounded-[var(--app-radius-md)]';

function isNavActive(pathname: string, href: string): boolean {
  return pathname === href || pathname.startsWith(`${href}/`);
}

function settingsLinkClassName(isActive: boolean): string {
  return [
    'block rounded-lg px-3 py-2 text-sm pl-8',
    'focus-visible:ring-2 ring-[color:var(--app-ring-strong)]',
    isActive
      ? 'bg-[color:var(--app-chip-active)] text-[color:var(--app-text-strong)]'
      : 'text-[color:var(--app-text-muted)] hover:bg-[color:var(--app-chip)]',
  ].join(' ');
}

export function AppSidebar({ overlay = false }: { overlay?: boolean }) {
  const { t } = useTranslation();
  const location = useLocation();
  const navExtensions = useExtensions('nav_item');
  const { state, toggle, expand } = useSidebar();
  const collapsed = state === 'collapsed';
  const { user } = useAuth();

  const [settingsOpen, setSettingsOpen] = useState(false);
  const settingsActive = isNavActive(location.pathname, '/settings');

  const workspaceLinks = WORKSPACE_LINKS.filter(
    (item) =>
      !item.permission
      || hasPermission(
        user?.role ?? undefined,
        item.permission,
        user?.platform_role ?? undefined,
      ),
  );

  // Auto-open settings accordion when a settings page is active
  const showSettings = settingsOpen || settingsActive;

  return (
    <aside
      className={`${overlay ? 'flex' : 'hidden md:flex'} shrink-0 flex-col border-r border-[color:var(--app-ring)] bg-[color:var(--app-surface)] transition-[width] duration-200 ease-in-out motion-reduce:transition-none`}
      style={{ width: collapsed ? '3.5rem' : '14rem' }}
    >
      <div className="px-4 py-3">
        <Link
          to="/reviewer"
          className="inline-flex items-center gap-2 font-mono rounded-[var(--app-radius-md)] focus-visible:outline-none focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
        >
          <svg
            aria-hidden
            className="h-6 w-6 shrink-0 text-[color:var(--app-primary)]"
            viewBox="0 0 24 24"
            fill="currentColor"
          >
            <path d="M4 3.5 20 12 4 20.5V15.2L12.4 12 4 8.8V3.5Z" />
          </svg>
          {!collapsed && (
            <span className="text-lg tracking-tight text-[color:var(--app-text-strong)]">revy</span>
          )}
        </Link>
      </div>
      <nav className="flex-1 overflow-y-auto px-2 py-2" aria-label={t('sidebar.mainNav')}>
        <ul className="space-y-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const active = isNavActive(location.pathname, item.href);
            return (
              <li key={item.href}>
                <Link
                  to={item.href}
                  title={collapsed ? t(item.label) : undefined}
                  className={[
                    'flex min-h-11 items-center gap-2 px-3 py-2 text-sm',
                    NAV_LINK_RADIUS,
                    'focus-visible:ring-2 ring-[color:var(--app-ring-strong)]',
                    active
                      ? 'bg-[color:var(--app-chip-active)] text-[color:var(--app-text-strong)]'
                      : 'text-[color:var(--app-text-muted)] hover:bg-[color:var(--app-chip)]',
                    collapsed ? 'justify-center' : '',
                  ].join(' ')}
                >
                  <Icon className="h-4 w-4 shrink-0" aria-hidden />
                  {!collapsed && t(item.label)}
                </Link>
              </li>
            );
          })}

          {/* Settings accordion group */}
          <li>
            <button
              type="button"
              aria-expanded={showSettings}
              onClick={() => {
                if (collapsed) {
                  expand();
                  setSettingsOpen(true);
                } else {
                  setSettingsOpen((prev) => !prev);
                }
              }}
              className={[
                'flex w-full min-h-11 items-center gap-2 px-3 py-2 text-sm',
                NAV_LINK_RADIUS,
                'focus-visible:ring-2 ring-[color:var(--app-ring-strong)]',
                settingsActive
                  ? 'bg-[color:var(--app-chip-active)] text-[color:var(--app-text-strong)]'
                  : 'text-[color:var(--app-text-muted)] hover:bg-[color:var(--app-chip)]',
                collapsed ? 'justify-center' : '',
              ].join(' ')}
              title={collapsed ? t('nav.settings') : undefined}
            >
              <Settings className="h-4 w-4 shrink-0" aria-hidden />
              {!collapsed && (
                <>
                  <span className="flex-1 text-left">{t('nav.settings')}</span>
                  <ChevronDown
                    className={`h-3 w-3 shrink-0 transition-transform ${showSettings ? 'rotate-180' : ''}`}
                  />
                </>
              )}
            </button>

            {!collapsed && showSettings && (
              <ul className="ml-2 mt-1 space-y-1 border-l border-[color:var(--app-ring)] pl-2">
                {/* Personal */}
                <li className="px-2 py-0.5">
                  <span className="text-[10px] font-semibold uppercase tracking-wide text-[color:var(--app-text-muted)]">
                    {t('settings.group.personal')}
                  </span>
                </li>
                {PERSONAL_LINKS.map((item) => {
                  const active = location.pathname === item.to;
                  return (
                    <li key={item.to}>
                      <NavLink to={item.to} className={() => settingsLinkClassName(active)}>
                        {t(item.label)}
                      </NavLink>
                    </li>
                  );
                })}
                {/* Workspace */}
                {workspaceLinks.length > 0 && (
                  <>
                    <li className="px-2 py-0.5">
                      <span className="text-[10px] font-semibold uppercase tracking-wide text-[color:var(--app-text-muted)]">
                        {t('settings.group.workspace')}
                      </span>
                    </li>
                    {workspaceLinks.map((item) => {
                      const active = location.pathname === item.to;
                      return (
                        <li key={item.to}>
                          <NavLink to={item.to} className={() => settingsLinkClassName(active)}>
                            {t(item.label)}
                          </NavLink>
                        </li>
                      );
                    })}
                  </>
                )}
              </ul>
            )}
          </li>

          {navExtensions.map((extension) => {
            const Component = extension.component;
            return <Component key={extension.id} />;
          })}
        </ul>
      </nav>
      <div className="mt-auto space-y-2 border-t border-[color:var(--app-ring)] px-2 py-3">
        <button
          type="button"
          onClick={toggle}
          className="flex w-full min-h-11 items-center justify-center rounded-[var(--app-radius-md)] text-[color:var(--app-text-muted)] hover:bg-[color:var(--app-chip)] focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
          title={collapsed ? t('sidebar.expandHint') : t('sidebar.collapseHint')}
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </button>
        {!collapsed && (
          <>
            <WorkspaceSwitcher />
            <UserMenu />
          </>
        )}
      </div>
    </aside>
  );
}