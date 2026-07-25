// frontend/src/features/settings/components/PermissionsMatrix.tsx
import { useTranslation } from 'react-i18next';
import { ROLE_PERMISSIONS } from '@/lib/permissions';
import type { Permission } from '@/lib/permissionTypes';
import { AppRole } from '@/shared/types/enums';

const MATRIX_ROLES = [AppRole.admin, AppRole.operator, AppRole.viewer] as const;

const MATRIX_PERMISSIONS: Permission[] = ['items:view', 'items:manage', 'admin:users'];

const PERMISSION_I18N: Record<Permission, string> = {
  'items:view': 'settings.permissions.perms.itemsView',
  'items:manage': 'settings.permissions.perms.itemsManage',
  'admin:users': 'settings.permissions.perms.adminUsers',
  'admin:workspaces': 'settings.permissions.perms.adminWorkspaces',
  'admin:system': 'settings.permissions.perms.adminSystem',
};

const ROLE_I18N: Record<AppRole, string> = {
  [AppRole.admin]: 'settings.permissions.roles.admin',
  [AppRole.operator]: 'settings.permissions.roles.operator',
  [AppRole.viewer]: 'settings.permissions.roles.viewer',
};

export function PermissionsMatrix() {
  const { t } = useTranslation();

  return (
    <section className="space-y-3">
      <h2 className="text-lg font-medium text-[color:var(--app-text-strong)]">
        {t('settings.permissions.title')}
      </h2>
      <div className="overflow-x-auto ring-1 ring-[color:var(--app-ring)] rounded-lg">
        <table className="min-w-full text-sm">
          <thead className="bg-[color:var(--app-table-header)] text-[color:var(--app-text-muted)]">
            <tr>
              <th className="px-4 py-3 text-left font-medium">
                {t('settings.permissions.roleColumn')}
              </th>
              {MATRIX_PERMISSIONS.map((permission) => (
                <th key={permission} className="px-4 py-3 text-left font-medium">
                  {t(PERMISSION_I18N[permission])}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {MATRIX_ROLES.map((role, index) => {
              const granted = new Set(ROLE_PERMISSIONS[role]);
              return (
                <tr
                  key={role}
                  className={
                    index % 2 === 0
                      ? 'bg-[color:var(--app-table-row)]'
                      : 'bg-[color:var(--app-table-row-alt)]'
                  }
                >
                  <td className="px-4 py-3 font-medium text-[color:var(--app-text-strong)]">
                    {t(ROLE_I18N[role])}
                  </td>
                  {MATRIX_PERMISSIONS.map((permission) => (
                    <td key={permission} className="px-4 py-3 text-[color:var(--app-text-muted)]">
                      {granted.has(permission) ? t('settings.permissions.granted') : '—'}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
