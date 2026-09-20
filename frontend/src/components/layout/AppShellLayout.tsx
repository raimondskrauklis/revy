// frontend/src/components/layout/AppShellLayout.tsx
/**
 * App shell — sidebar nav + main Outlet.
 * KP equivalent: WorkspaceLayout + StandardSidebar.
 * See docs/frontend/patterns/LAYOUT_GUIDE.md and reference/ROUTING.md
 */
import { Link, Outlet, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { LayoutDashboard, Plug, Settings } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { ImpersonationBanner } from '@/features/admin/components/ImpersonationBanner';
import { StackShell } from '@/components/layout/StackShell';
import { AppHeader } from '@/components/layout/AppHeader';
import { WorkspaceSwitcher } from '@/components/layout/WorkspaceSwitcher';
import { UserMenu } from '@/components/layout/UserMenu';
import { useExtensions } from '@/platform/extensions/hooks';

type NavItem = {
  href: string;
  label: string;
  icon: LucideIcon;
};

const NAV_ITEMS: NavItem[] = [
  { href: '/dashboard', label: 'nav.dashboard', icon: LayoutDashboard },
  { href: '/installations', label: 'nav.installations', icon: Plug },
  { href: '/settings', label: 'nav.settings', icon: Settings },
];

const NAV_LINK_RADIUS = 'rounded-[var(--app-radius-md)]';

function isNavActive(pathname: string, href: string): boolean {
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function AppShellLayout() {
  const { t } = useTranslation();
  const location = useLocation();
  const navExtensions = useExtensions('nav_item');

  return (
    <div className="flex h-screen min-h-0 overflow-hidden bg-[color:var(--app-canvas)]">
      <aside className="hidden md:flex w-56 shrink-0 flex-col border-r border-[color:var(--app-ring)] bg-[color:var(--app-surface)]">
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
            <span className="text-lg tracking-tight text-[color:var(--app-text-strong)]">revy</span>
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
                    className={[
                      'flex min-h-11 items-center gap-2 px-3 py-2 text-sm',
                      NAV_LINK_RADIUS,
                      'focus-visible:ring-2 ring-[color:var(--app-ring-strong)]',
                      active
                        ? 'bg-[color:var(--app-chip-active)] text-[color:var(--app-text-strong)]'
                        : 'text-[color:var(--app-text-muted)] hover:bg-[color:var(--app-chip)]',
                    ].join(' ')}
                  >
                    <Icon className="h-4 w-4 shrink-0" aria-hidden />
                    {t(item.label)}
                  </Link>
                </li>
              );
            })}
            {navExtensions.map((extension) => {
              const Component = extension.component;
              return <Component key={extension.id} />;
            })}
          </ul>
        </nav>
        <div className="mt-auto space-y-2 border-t border-[color:var(--app-ring)] px-2 py-3">
          <WorkspaceSwitcher />
          <UserMenu />
        </div>
      </aside>

      <main className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <ImpersonationBanner />
        <AppHeader />
        <div className="flex-1 overflow-y-auto p-4 md:p-6">
          <Outlet />
        </div>
      </main>
      <StackShell />
    </div>
  );
}
