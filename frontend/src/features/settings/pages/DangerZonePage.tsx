// frontend/src/features/settings/pages/DangerZonePage.tsx
import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { ConfirmDestructiveModal } from '@/features/settings/components/ConfirmDestructiveModal';
import {
  useCreateExportJob,
  useDeleteAccount,
  useDeleteWorkspace,
  useExportJobStatus,
  useLeaveWorkspace,
  downloadUserExport,
} from '@/features/settings/hooks';
import { useAuth } from '@/contexts/AuthContext';
import { hasPermission } from '@/lib/permissions';
import { mapApiError } from '@/shared/errors';
import { showDomainErrorToast } from '@/shared/errors/toasts';

type ActiveModal = 'leave' | 'deleteWorkspace' | 'deleteAccount' | null;

export function DangerZonePage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { user, logout, refetchUser } = useAuth();
  const workspaceId = user?.workspace_id ?? null;
  const membership = useMemo(
    () => user?.memberships.find((item) => item.workspace_id === workspaceId) ?? null,
    [user?.memberships, workspaceId],
  );
  const canManageWorkspace = hasPermission(
    user?.role ?? undefined,
    'admin:users',
    user?.platform_role ?? undefined,
  );

  const [activeModal, setActiveModal] = useState<ActiveModal>(null);
  const [exportJobId, setExportJobId] = useState<string | null>(null);

  const createExport = useCreateExportJob();
  const exportStatus = useExportJobStatus(exportJobId);
  const leaveWorkspace = useLeaveWorkspace(workspaceId);
  const deleteWorkspace = useDeleteWorkspace(workspaceId);
  const deleteAccount = useDeleteAccount();

  const exportState = exportStatus.data?.status;
  const isExportBusy =
    createExport.isPending
    || exportState === 'pending'
    || exportState === 'processing';

  async function handleRequestExport() {
    try {
      const result = await createExport.mutateAsync();
      setExportJobId(result.job_id);
    } catch (error) {
      showDomainErrorToast(mapApiError(error));
    }
  }

  async function handleDownloadExport() {
    if (!exportJobId) return;
    try {
      const blob = await downloadUserExport(exportJobId);
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `revy-export-${exportJobId}.zip`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      showDomainErrorToast(mapApiError(error));
    }
  }

  async function handleLeaveWorkspace() {
    try {
      await leaveWorkspace.mutateAsync();
      setActiveModal(null);
      await refetchUser();
      navigate('/dashboard');
    } catch (error) {
      showDomainErrorToast(mapApiError(error));
    }
  }

  async function handleDeleteWorkspace() {
    if (!membership) return;
    try {
      await deleteWorkspace.mutateAsync({ confirm_slug: membership.workspace_slug });
      setActiveModal(null);
      await refetchUser();
      navigate('/dashboard');
    } catch (error) {
      showDomainErrorToast(mapApiError(error));
    }
  }

  async function handleDeleteAccount() {
    if (!user) return;
    try {
      await deleteAccount.mutateAsync({ confirm_email: user.email });
      setActiveModal(null);
      logout();
    } catch (error) {
      showDomainErrorToast(mapApiError(error));
    }
  }

  if (!user) {
    return null;
  }

  return (
    <div className="space-y-8">
      <h1 className="text-xl font-semibold text-[color:var(--app-text-strong)]">
        {t('settings.nav.danger')}
      </h1>

      <section className="max-w-2xl space-y-3 rounded-lg bg-[color:var(--app-surface)] p-4 ring-1 ring-[color:var(--app-ring)]">
        <h2 className="text-sm font-semibold text-[color:var(--app-text-strong)]">
          {t('settings.danger.export.title')}
        </h2>
        <p className="text-sm text-[color:var(--app-text-muted)]">
          {t('settings.danger.export.body')}
        </p>
        {exportJobId && exportState ? (
          <p className="text-sm text-[color:var(--app-text-muted)]">
            {t(`settings.danger.export.status.${exportState}`)}
          </p>
        ) : null}
        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            onClick={handleRequestExport}
            disabled={isExportBusy}
            className="min-h-11 rounded-lg bg-[color:var(--app-chip)] px-4 text-sm font-medium text-[color:var(--app-text-strong)] focus-visible:ring-2 ring-[color:var(--app-ring-strong)] disabled:opacity-50"
          >
            {t('settings.danger.export.request')}
          </button>
          {exportState === 'completed' ? (
            <button
              type="button"
              onClick={handleDownloadExport}
              className="min-h-11 rounded-lg bg-[color:var(--app-cta-bg)] px-4 text-sm font-medium text-[color:var(--app-cta-fg)] focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
            >
              {t('settings.danger.export.download')}
            </button>
          ) : null}
        </div>
      </section>

      {workspaceId ? (
        <section className="max-w-2xl space-y-3 rounded-lg bg-[color:var(--app-surface)] p-4 ring-1 ring-[color:var(--app-danger)]">
          <h2 className="text-sm font-semibold text-[color:var(--app-danger)]">
            {t('settings.danger.leave.title')}
          </h2>
          <p className="text-sm text-[color:var(--app-text-muted)]">
            {t('settings.danger.leave.body')}
          </p>
          <button
            type="button"
            onClick={() => setActiveModal('leave')}
            className="min-h-11 rounded-lg bg-[color:var(--app-danger)] px-4 text-sm font-medium text-[color:var(--app-on-accent)] focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
          >
            {t('settings.danger.leave.action')}
          </button>
        </section>
      ) : null}

      {canManageWorkspace && workspaceId && membership ? (
        <section className="max-w-2xl space-y-3 rounded-lg bg-[color:var(--app-surface)] p-4 ring-1 ring-[color:var(--app-danger)]">
          <h2 className="text-sm font-semibold text-[color:var(--app-danger)]">
            {t('settings.danger.deleteWorkspace.title')}
          </h2>
          <p className="text-sm text-[color:var(--app-text-muted)]">
            {t('settings.danger.deleteWorkspace.body')}
          </p>
          <button
            type="button"
            onClick={() => setActiveModal('deleteWorkspace')}
            className="min-h-11 rounded-lg bg-[color:var(--app-danger)] px-4 text-sm font-medium text-[color:var(--app-on-accent)] focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
          >
            {t('settings.danger.deleteWorkspace.action')}
          </button>
        </section>
      ) : null}

      <section className="max-w-2xl space-y-3 rounded-lg bg-[color:var(--app-surface)] p-4 ring-1 ring-[color:var(--app-danger)]">
        <h2 className="text-sm font-semibold text-[color:var(--app-danger)]">
          {t('settings.danger.deleteAccount.title')}
        </h2>
        <p className="text-sm text-[color:var(--app-text-muted)]">
          {t('settings.danger.deleteAccount.body')}
        </p>
        <button
          type="button"
          onClick={() => setActiveModal('deleteAccount')}
          className="min-h-11 rounded-lg bg-[color:var(--app-danger)] px-4 text-sm font-medium text-[color:var(--app-on-accent)] focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
        >
          {t('settings.danger.deleteAccount.action')}
        </button>
      </section>

      <ConfirmDestructiveModal
        open={activeModal === 'leave'}
        title={t('settings.danger.leave.confirmTitle')}
        description={t('settings.danger.leave.confirmBody')}
        confirmLabel={t('settings.danger.leave.action')}
        isLoading={leaveWorkspace.isPending}
        onClose={() => setActiveModal(null)}
        onConfirm={handleLeaveWorkspace}
      />

      <ConfirmDestructiveModal
        open={activeModal === 'deleteWorkspace'}
        title={t('settings.danger.deleteWorkspace.confirmTitle')}
        description={t('settings.danger.deleteWorkspace.confirmBody')}
        confirmLabel={t('settings.danger.deleteWorkspace.action')}
        confirmMatch={membership?.workspace_slug}
        confirmMatchLabel={t('settings.danger.deleteWorkspace.confirmMatchLabel', {
          slug: membership?.workspace_slug ?? '',
        })}
        isLoading={deleteWorkspace.isPending}
        onClose={() => setActiveModal(null)}
        onConfirm={handleDeleteWorkspace}
      />

      <ConfirmDestructiveModal
        open={activeModal === 'deleteAccount'}
        title={t('settings.danger.deleteAccount.confirmTitle')}
        description={t('settings.danger.deleteAccount.confirmBody')}
        confirmLabel={t('settings.danger.deleteAccount.action')}
        confirmMatch={user.email}
        confirmMatchLabel={t('settings.danger.deleteAccount.confirmMatchLabel', {
          email: user.email,
        })}
        isLoading={deleteAccount.isPending}
        onClose={() => setActiveModal(null)}
        onConfirm={handleDeleteAccount}
      />
    </div>
  );
}
