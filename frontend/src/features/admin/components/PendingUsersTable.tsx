// frontend/src/features/admin/components/PendingUsersTable.tsx
import { useTranslation } from 'react-i18next';
import type { PendingUser } from '@/features/admin/api';

interface PendingUsersTableProps {
  users: PendingUser[];
  onApprove: (userId: string) => void;
  onReject: (userId: string) => void;
  busyUserId: string | null;
}

export function PendingUsersTable({
  users,
  onApprove,
  onReject,
  busyUserId,
}: PendingUsersTableProps) {
  const { t } = useTranslation();

  if (users.length === 0) {
    return (
      <p className="text-sm text-[color:var(--app-text-muted)]">{t('admin.users.empty')}</p>
    );
  }

  return (
    <div className="overflow-x-auto ring-1 ring-[color:var(--app-ring)] rounded-lg">
      <table className="w-full text-sm">
        <thead className="bg-[color:var(--app-surface-muted)] text-left">
          <tr>
            <th className="px-4 py-3 font-medium text-[color:var(--app-text-muted)]">
              {t('admin.users.columns.email')}
            </th>
            <th className="px-4 py-3 font-medium text-[color:var(--app-text-muted)]">
              {t('admin.users.columns.name')}
            </th>
            <th className="px-4 py-3 font-medium text-[color:var(--app-text-muted)]">
              {t('admin.users.columns.actions')}
            </th>
          </tr>
        </thead>
        <tbody>
          {users.map((user) => {
            const busy = busyUserId === user.id;
            return (
              <tr
                key={user.id}
                className="border-t border-[color:var(--app-ring)] bg-[color:var(--app-table-row)]"
              >
                <td className="px-4 py-3 text-[color:var(--app-text-strong)]">{user.email}</td>
                <td className="px-4 py-3 text-[color:var(--app-text-muted)]">
                  {user.full_name ?? '—'}
                </td>
                <td className="px-4 py-3 space-x-2">
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => onApprove(user.id)}
                    className="min-h-11 px-3 rounded-lg bg-[color:var(--app-cta-bg)] text-[color:var(--app-cta-fg)] focus-visible:ring-2 ring-[color:var(--app-ring-strong)] disabled:opacity-50"
                  >
                    {t('admin.users.approve')}
                  </button>
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => onReject(user.id)}
                    className="min-h-11 px-3 rounded-lg ring-1 ring-[color:var(--app-ring)] text-[color:var(--app-text-strong)] focus-visible:ring-2 ring-[color:var(--app-ring-strong)] disabled:opacity-50"
                  >
                    {t('admin.users.reject')}
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
