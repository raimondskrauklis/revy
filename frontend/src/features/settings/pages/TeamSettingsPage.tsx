// frontend/src/features/settings/pages/TeamSettingsPage.tsx
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/contexts/AuthContext';
import { InviteMemberForm } from '@/features/settings/components/InviteMemberForm';
import { InvitationsTable } from '@/features/settings/components/InvitationsTable';
import { MembersTable } from '@/features/settings/components/MembersTable';
import { PermissionsMatrix } from '@/features/settings/components/PermissionsMatrix';
import {
  useCreateInvitation,
  useInvitations,
  useMembers,
  useRemoveMember,
  useRevokeInvitation,
  useUpdateMemberRole,
} from '@/features/settings/hooks';
import { hasPermission } from '@/lib/permissions';
import { mapApiError } from '@/shared/errors';
import { showDomainErrorToast } from '@/shared/errors/toasts';
import { AppRole } from '@/shared/types/enums';

export function TeamSettingsPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const workspaceId = user?.workspace_id ?? null;
  const canManage = hasPermission(
    user?.role ?? undefined,
    'admin:users',
    user?.platform_role ?? undefined,
  );

  const membersQuery = useMembers(workspaceId);
  const invitationsQuery = useInvitations(workspaceId, canManage);
  const updateMemberRole = useUpdateMemberRole(workspaceId);
  const removeMember = useRemoveMember(workspaceId);
  const createInvitation = useCreateInvitation(workspaceId);
  const revokeInvitation = useRevokeInvitation(workspaceId);

  const [busyUserId, setBusyUserId] = useState<string | null>(null);
  const [busyInvitationId, setBusyInvitationId] = useState<string | null>(null);

  async function handleRoleChange(userId: string, role: AppRole) {
    setBusyUserId(userId);
    try {
      await updateMemberRole.mutateAsync({ userId, payload: { role } });
    } catch (error) {
      showDomainErrorToast(mapApiError(error));
    } finally {
      setBusyUserId(null);
    }
  }

  async function handleRemove(userId: string) {
    setBusyUserId(userId);
    try {
      await removeMember.mutateAsync(userId);
    } catch (error) {
      showDomainErrorToast(mapApiError(error));
    } finally {
      setBusyUserId(null);
    }
  }

  async function handleInvite(payload: { email: string; role: AppRole }) {
    await createInvitation.mutateAsync(payload);
  }

  async function handleRevoke(invitationId: string) {
    setBusyInvitationId(invitationId);
    try {
      await revokeInvitation.mutateAsync(invitationId);
    } catch (error) {
      showDomainErrorToast(mapApiError(error));
    } finally {
      setBusyInvitationId(null);
    }
  }

  if (!workspaceId) {
    return (
      <p className="text-sm text-[color:var(--app-text-muted)]">{t('settings.team.noWorkspace')}</p>
    );
  }

  return (
    <div className="space-y-8">
      <h1 className="text-xl font-semibold text-[color:var(--app-text-strong)]">
        {t('settings.nav.team')}
      </h1>

      <section className="space-y-3">
        <h2 className="text-lg font-medium text-[color:var(--app-text-strong)]">
          {t('settings.team.members.title')}
        </h2>
        {membersQuery.isLoading ? (
          <p className="text-sm text-[color:var(--app-text-muted)]">{t('common.loading')}</p>
        ) : (
          <MembersTable
            members={membersQuery.items}
            canManage={canManage}
            currentUserId={user?.id}
            busyUserId={busyUserId}
            onRoleChange={handleRoleChange}
            onRemove={handleRemove}
            loadMoreRef={membersQuery.ref}
            isFetchingNextPage={membersQuery.isFetchingNextPage}
          />
        )}
      </section>

      {canManage ? (
        <>
          <section className="space-y-3">
            <h2 className="text-lg font-medium text-[color:var(--app-text-strong)]">
              {t('settings.team.invitations.title')}
            </h2>
            {invitationsQuery.isLoading ? (
              <p className="text-sm text-[color:var(--app-text-muted)]">{t('common.loading')}</p>
            ) : (
              <InvitationsTable
                invitations={invitationsQuery.items}
                busyInvitationId={busyInvitationId}
                onRevoke={handleRevoke}
                loadMoreRef={invitationsQuery.ref}
                isFetchingNextPage={invitationsQuery.isFetchingNextPage}
              />
            )}
          </section>

          <InviteMemberForm onInvite={handleInvite} submitting={createInvitation.isPending} />
        </>
      ) : null}

      <PermissionsMatrix />
    </div>
  );
}
