// frontend/src/components/layout/MobileBottomNav.tsx
import { Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { LayoutDashboard, GitPullRequest, Plug, Settings } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

type Tab = {
  href: string;
  label: string;
  icon: LucideIcon;
};

const TABS: Tab[] = [
  { href: '/dashboard', label: 'nav.dashboard', icon: LayoutDashboard },
  { href: '/reviewer', label: 'nav.reviewer', icon: GitPullRequest },
  { href: '/installations', label: 'nav.installations', icon: Plug },
  { href: '/settings/profile', label: 'nav.settings', icon: Settings },
];

export function MobileBottomNav() {
  const { t } = useTranslation();
  const { pathname } = useLocation();

  return (
    <nav
      className="md:hidden fixed bottom-0 left-0 right-0 h-14 bg-[color:var(--app-surface)] border-t border-[color:var(--app-ring)] z-40"
      aria-label={t('sidebar.mainNav')}
    >
      <ul className="flex h-full">
        {TABS.map((tab) => {
          const Icon = tab.icon;
          const isActive =
            pathname === tab.href ||
            (tab.href !== '/' && pathname.startsWith(tab.href) && tab.href !== '/dashboard')
            || (tab.href === '/dashboard' && pathname === '/dashboard');

          return (
            <li key={tab.href} className="flex-1">
              <Link
                to={tab.href}
                className={`flex flex-col items-center justify-center h-full gap-0.5 text-[10px] ${
                  isActive
                    ? 'text-[color:var(--app-primary)] font-medium'
                    : 'text-[color:var(--app-text-muted)]'
                }`}
              >
                <Icon className="h-5 w-5" aria-hidden />
                <span>{t(tab.label)}</span>
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}