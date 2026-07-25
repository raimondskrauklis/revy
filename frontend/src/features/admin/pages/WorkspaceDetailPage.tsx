// frontend/src/features/admin/pages/WorkspaceDetailPage.tsx
import { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  fetchAdminWorkspaceDetail,
  fetchAdminWorkspaceMembers,
  startImpersonation,
  suspendAdminWorkspace,
  unsuspendAdminWorkspace,
  type AdminWorkspaceDetail,
  type AdminWorkspaceMember,
} from '@/features/admin/api';
import { ImpersonationStartModal } from '@/features/admin/components/ImpersonationStartModal';
import { Button } from '@/components/ui/button';
import { formatDateTime } from '@/lib/date';
import { useAuth } from '@/contexts/AuthContext';
import { mapApiError } from '@/shared/errors';
import { showDomainErrorToast } from '@/shared/errors/toasts';

export function WorkspaceDetailPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { refetchUser } = useAuth();
  const { workspaceId } = useParams<{ workspaceId: string }>();
  const [workspace, setWorkspace] = useState<AdminWorkspaceDetail | null>(null);
  const [members, setMembers] = useState<AdminWorkspaceMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [membersLoading, setMembersLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [confirmAction, setConfirmAction] = useState<'suspend' | 'unsuspend' | null>(null);
  const [impersonateTarget, setImpersonateTarget] = useState<AdminWorkspaceMember | null>(null);

  const loadWorkspace = useCallback(async () => {
    if (!workspaceId) return;
    setLoading(true);
    try {
      setWorkspace(await fetchAdminWorkspaceDetail(workspaceId));
    } catch (error) {
      showDomainErrorToast(mapApiError(error));
    } finally {
      setLoading(false);
    }
  }, [workspaceId]);

  const loadMembers = useCallback(async () => {
    if (!workspaceId) return;
    setMembersLoading(true);
    try {
      const page = await fetchAdminWorkspaceMembers(workspaceId);
      setMembers(page.items);
    } catch (error) {
      showDomainErrorToast(mapApiError(error));
    } finally {
      setMembersLoading(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    void loadWorkspace();
    void loadMembers();
  }, [loadWorkspace, loadMembers]);

  async function handleConfirm() {
    if (!workspaceId || !confirmAction) return;
    setBusy(true);
    try {
      const updated =
        confirmAction === 'suspend'
          ? await suspendAdminWorkspace(workspaceId)
          : await unsuspendAdminWorkspace(workspaceId);
      setWorkspace(updated);
      setConfirmAction(null);
    } catch (error) {
      showDomainErrorToast(mapApiError(error));
    } finally {
      setBusy(false);
    }
  }

  async function handleStartImpersonation(reason: string) {
    if (!impersonateTarget) return;
    setBusy(true);
    try {
      await startImpersonation(impersonateTarget.user_id, reason);
      await refetchUser();
      setImpersonateTarget(null);
      void navigate('/dashboard');
    } catch (error) {
      showDomainErrorToast(mapApiError(error));
    } finally {
      setBusy(false);
    }
  }

  if (!workspaceId) {
    return null;
  }

  if (loading) {
    return <p className="text-sm text-[color:var(--app-text-muted)]">{t('common.loading')}</p>;
  }

  if (!workspace) {
    return <p className="text-sm text-[color:var(--app-text-muted)]">{t('admin.workspaces.notFound')}</p>;
  }

  const isSuspended = workspace.status === 'suspended';

  return (
    <div className="space-y-6">
      <div>
        <Link
          to="/admin/workspaces"
          className="text-sm text-[color:var(--app-link)] hover:underline"
        >
          {t('admin.workspaces.backToList')}
        </Link>
        <h1 className="mt-2 text-xl font-semibold text-[color:var(--app-text-strong)]">
          {workspace.name}
        </h1>
        <p className="text-sm text-[color:var(--app-text-muted)]">{workspace.slug}</p>
      </div>

      <dl className="grid gap-4 sm:grid-cols-2">
        <div>
          <dt className="text-xs font-medium uppercase text-[color:var(--app-text-muted)]">
            {t('admin.workspaces.detail.status')}
          </dt>
          <dd className="mt-1 text-sm text-[color:var(--app-text-strong)]">
            {t(`admin.workspaces.status.${workspace.status}`)}
          </dd>
        </div>
        <div>
          <dt className="text-xs font-medium uppercase text-[color:var(--app-text-muted)]">
            {t('admin.workspaces.detail.plan')}
          </dt>
          <dd className="mt-1 text-sm text-[color:var(--app-text-strong)]">
            {workspace.plan ?? '—'}
          </dd>
        </div>
        <div>
          <dt className="text-xs font-medium uppercase text-[color:var(--app-text-muted)]">
            {t('admin.workspaces.detail.members')}
          </dt>
          <dd className="mt-1 text-sm text-[color:var(--app-text-strong)]">
            {workspace.member_count}
          </dd>
        </div>
        <div>
          <dt className="text-xs font-medium uppercase text-[color:var(--app-text-muted)]">
            {t('admin.workspaces.detail.stripeCustomer')}
          </dt>
          <dd className="mt-1 text-sm text-[color:var(--app-text-strong)]">
            {workspace.stripe_customer_id ?? '—'}
          </dd>
        </div>
        <div>
          <dt className="text-xs font-medium uppercase text-[color:var(--app-text-muted)]">
            {t('admin.workspaces.detail.created')}
          </dt>
          <dd className="mt-1 text-sm text-[color:var(--app-text-strong)]">
            {formatDateTime(workspace.created_at)}
          </dd>
        </div>
        <div>
          <dt className="text-xs font-medium uppercase text-[color:var(--app-text-muted)]">
            {t('admin.workspaces.detail.updated')}
          </dt>
          <dd className="mt-1 text-sm text-[color:var(--app-text-strong)]">
            {formatDateTime(workspace.updated_at)}
          </dd>
        </div>
      </dl>

      <section className="space-y-3">
        <div>
          <h2 className="text-sm font-semibold text-[color:var(--app-text-strong)]">
            {t('admin.workspaces.members.title')}
          </h2>
          <p className="text-sm text-[color:var(--app-text-muted)]">
            {t('admin.workspaces.members.description')}
          </p>
        </div>

        {impersonateTarget ? (
          <ImpersonationStartModal
            targetEmail={impersonateTarget.email}
            busy={busy}
            onCancel={() => setImpersonateTarget(null)}
            onConfirm={(reason) => void handleStartImpersonation(reason)}
          />
        ) : null}

        {membersLoading ? (
          <p className="text-sm text-[color:var(--app-text-muted)]">{t('common.loading')}</p>
        ) : members.length === 0 ? (
          <p className="text-sm text-[color:var(--app-text-muted)]">{t('admin.workspaces.members.empty')}</p>
        ) : (
          <div className="overflow-x-auto rounded-lg ring-1 ring-[color:var(--app-ring)]">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead className="bg-[color:var(--app-chip)] text-[color:var(--app-text-muted)]">
                <tr>
                  <th className="px-4 py-3 font-medium">{t('admin.workspaces.members.columns.email')}</th>
                  <th className="px-4 py-3 font-medium">{t('admin.workspaces.members.columns.role')}</th>
                  <th className="px-4 py-3 font-medium">{t('admin.workspaces.members.columns.status')}</th>
                  <th className="px-4 py-3 font-medium">{t('admin.workspaces.members.columns.actions')}</th>
                </tr>
              </thead>
              <tbody>
                {members.map((member) => (
                  <tr
                    key={member.user_id}
                    className="border-t border-[color:var(--app-ring)] hover:bg-[color:var(--app-chip)]"
                  >
                    <td className="px-4 py-3">
                      <div className="text-[color:var(--app-text-strong)]">{member.email}</div>
                      {member.full_name ? (
                        <div className="text-xs text-[color:var(--app-text-muted)]">{member.full_name}</div>
                      ) : null}
                    </td>
                    <td className="px-4 py-3 text-[color:var(--app-text-muted)]">
                      {t(`settings.team.roles.${member.role}`)}
                    </td>
                    <td className="px-4 py-3 text-[color:var(--app-text-muted)]">
                      {member.status}
                    </td>
                    <td className="px-4 py-3">
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        disabled={member.status !== 'active' || busy}
                        onClick={() => setImpersonateTarget(member)}
                      >
                        {t('admin.impersonation.start')}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {confirmAction ? (
        <div className="rounded-lg bg-[color:var(--app-chip)] p-4 space-y-3">
          <p className="text-sm text-[color:var(--app-text-strong)]">
            {confirmAction === 'suspend'
              ? t('admin.workspaces.confirmSuspend')
              : t('admin.workspaces.confirmUnsuspend')}
          </p>
          <div className="flex gap-2">
            <Button
              type="button"
              variant={confirmAction === 'suspend' ? 'destructive' : 'default'}
              disabled={busy}
              onClick={() => void handleConfirm()}
            >
              {t('common.confirm')}
            </Button>
            <Button
              type="button"
              variant="outline"
              disabled={busy}
              onClick={() => setConfirmAction(null)}
            >
              {t('common.cancel')}
            </Button>
          </div>
        </div>
      ) : (
        <div>
          {isSuspended ? (
            <Button type="button" onClick={() => setConfirmAction('unsuspend')}>
              {t('admin.workspaces.unsuspend')}
            </Button>
          ) : (
            <Button type="button" variant="destructive" onClick={() => setConfirmAction('suspend')}>
              {t('admin.workspaces.suspend')}
            </Button>
          )}
        </div>
      )}
    </div>
  );
}
