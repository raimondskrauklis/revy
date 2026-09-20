// frontend/src/features/settings/layout/settingsNavLinks.ts
import type { Permission } from '@/lib/permissionTypes';

interface SettingsNavLink {
  to: string;
  label: string;
  permission?: Permission;
}

export const PERSONAL_LINKS: SettingsNavLink[] = [
  { to: '/settings/profile', label: 'settings.nav.profile' },
  { to: '/settings/security', label: 'settings.nav.security' },
  { to: '/settings/appearance', label: 'settings.nav.appearance' },
];

export const WORKSPACE_LINKS: SettingsNavLink[] = [
  { to: '/settings/workspace', label: 'settings.nav.workspace', permission: 'admin:users' },
  { to: '/settings/review', label: 'settings.nav.review', permission: 'admin:users' },
  { to: '/settings/team', label: 'settings.nav.team' },
  { to: '/settings/integrations', label: 'settings.nav.integrations' },
  { to: '/settings/billing', label: 'settings.nav.billing', permission: 'admin:users' },
  { to: '/settings/danger', label: 'settings.nav.danger' },
];