// frontend/src/features/admin/pages/AdminUsersPage.tsx
import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  approvePendingUser,
  fetchPendingUsers,
  rejectPendingUser,
  type PendingUser,
} from '@/features/admin/api';
import { PendingUsersTable } from '@/features/admin/components/PendingUsersTable';
import { mapApiError } from '@/shared/errors';
import { showDomainErrorToast } from '@/shared/errors/toasts';

export function AdminUsersPage() {
  const { t } = useTranslation();
  const [users, setUsers] = useState<PendingUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyUserId, setBusyUserId] = useState<string | null>(null);

  const loadUsers = useCallback(async () => {
    setLoading(true);
    try {
      setUsers(await fetchPendingUsers());
    } catch (error) {
      showDomainErrorToast(mapApiError(error));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadUsers();
  }, [loadUsers]);

  async function handleApprove(userId: string) {
    setBusyUserId(userId);
    try {
      await approvePendingUser(userId);
      await loadUsers();
    } catch (error) {
      showDomainErrorToast(mapApiError(error));
    } finally {
      setBusyUserId(null);
    }
  }

  async function handleReject(userId: string) {
    setBusyUserId(userId);
    try {
      await rejectPendingUser(userId);
      await loadUsers();
    } catch (error) {
      showDomainErrorToast(mapApiError(error));
    } finally {
      setBusyUserId(null);
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-[color:var(--app-text-strong)]">
        {t('admin.users.title')}
      </h1>
      <p className="text-sm text-[color:var(--app-text-muted)]">{t('admin.users.description')}</p>
      {loading ? (
        <p className="text-sm text-[color:var(--app-text-muted)]">{t('common.loading')}</p>
      ) : (
        <PendingUsersTable
          users={users}
          onApprove={handleApprove}
          onReject={handleReject}
          busyUserId={busyUserId}
        />
      )}
    </div>
  );
}
