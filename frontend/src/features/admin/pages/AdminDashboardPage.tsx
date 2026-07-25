// frontend/src/features/admin/pages/AdminDashboardPage.tsx
import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { fetchAdminKpis, type AdminKpis } from '@/features/admin/api';
import { mapApiError } from '@/shared/errors';
import { showDomainErrorToast } from '@/shared/errors/toasts';

function KpiCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg bg-[color:var(--app-surface)] p-4 ring-1 ring-[color:var(--app-ring)]">
      <p className="text-xs font-medium uppercase tracking-wide text-[color:var(--app-text-muted)]">
        {label}
      </p>
      <p className="mt-2 text-2xl font-semibold text-[color:var(--app-text-strong)]">{value}</p>
    </div>
  );
}

export function AdminDashboardPage() {
  const { t } = useTranslation();
  const [kpis, setKpis] = useState<AdminKpis | null>(null);
  const [loading, setLoading] = useState(true);

  const loadKpis = useCallback(async () => {
    setLoading(true);
    try {
      setKpis(await fetchAdminKpis());
    } catch (error) {
      showDomainErrorToast(mapApiError(error));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadKpis();
  }, [loadKpis]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-[color:var(--app-text-strong)]">
          {t('admin.dashboard.title')}
        </h1>
        <p className="text-sm text-[color:var(--app-text-muted)]">{t('admin.dashboard.description')}</p>
      </div>

      {loading ? (
        <p className="text-sm text-[color:var(--app-text-muted)]">{t('common.loading')}</p>
      ) : kpis ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <KpiCard label={t('admin.dashboard.kpis.workspacesTotal')} value={kpis.workspaces_total} />
            <KpiCard label={t('admin.dashboard.kpis.workspacesActive')} value={kpis.workspaces_active} />
            <KpiCard
              label={t('admin.dashboard.kpis.workspacesSuspended')}
              value={kpis.workspaces_suspended}
            />
            <KpiCard
              label={t('admin.dashboard.kpis.workspacesDeleted')}
              value={kpis.workspaces_deleted}
            />
            <KpiCard label={t('admin.dashboard.kpis.usersActive')} value={kpis.users_active} />
            <KpiCard
              label={t('admin.dashboard.kpis.usersPendingApproval')}
              value={kpis.users_pending_approval}
            />
          </div>

          {kpis.users_pending_approval > 0 ? (
            <div className="rounded-lg bg-[color:var(--app-chip)] p-4">
              <p className="text-sm text-[color:var(--app-text-strong)]">
                {t('admin.dashboard.pendingApprovalBanner', {
                  count: kpis.users_pending_approval,
                })}
              </p>
              <Link
                to="/admin/users"
                className="mt-2 inline-block text-sm font-medium text-[color:var(--app-link)] hover:underline"
              >
                {t('admin.dashboard.reviewPendingUsers')}
              </Link>
            </div>
          ) : null}
        </>
      ) : null}
    </div>
  );
}
