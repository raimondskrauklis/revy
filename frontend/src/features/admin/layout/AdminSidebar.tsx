// frontend/src/features/admin/layout/AdminSidebar.tsx
import { NavLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Building2,
  ClipboardList,
  LayoutDashboard,
  Settings,
  Users,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

const NAV_ITEMS: { to: string; label: string; icon: LucideIcon }[] = [
  { to: '/admin/dashboard', label: 'admin.nav.dashboard', icon: LayoutDashboard },
  { to: '/admin/workspaces', label: 'admin.nav.workspaces', icon: Building2 },
  { to: '/admin/users', label: 'admin.nav.users', icon: Users },
  { to: '/admin/audit', label: 'admin.nav.audit', icon: ClipboardList },
  { to: '/admin/settings', label: 'admin.nav.settings', icon: Settings },
];

function linkClassName({ isActive }: { isActive: boolean }): string {
  return [
    'flex min-h-11 items-center gap-2 rounded-lg px-3 py-2 text-sm',
    'focus-visible:ring-2 ring-[color:var(--app-ring-strong)]',
    isActive
      ? 'bg-[color:var(--app-chip-active)] text-[color:var(--app-text-strong)]'
      : 'text-[color:var(--app-text-muted)] hover:bg-[color:var(--app-chip)]',
  ].join(' ');
}

export function AdminSidebar() {
  const { t } = useTranslation();

  return (
    <nav className="w-full shrink-0 md:w-56" aria-label={t('admin.sidebar.label')}>
      <ul className="space-y-1">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <li key={item.to}>
              <NavLink to={item.to} className={linkClassName}>
                <Icon className="h-4 w-4 shrink-0" aria-hidden />
                {t(item.label)}
              </NavLink>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
