// frontend/src/features/settings/components/InvitationsTable.tsx
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/button';
import { formatDate } from '@/lib/date';
import type { Invitation } from '@/features/settings/types';

interface InvitationsTableProps {
  invitations: Invitation[];
  busyInvitationId: string | null;
  onRevoke: (invitationId: string) => Promise<void>;
  loadMoreRef?: (node?: Element | null) => void;
  isFetchingNextPage?: boolean;
}

export function InvitationsTable({
  invitations,
  busyInvitationId,
  onRevoke,
  loadMoreRef,
  isFetchingNextPage,
}: InvitationsTableProps) {
  const { t } = useTranslation();
  const [confirmRevokeId, setConfirmRevokeId] = useState<string | null>(null);

  if (invitations.length === 0) {
    return (
      <p className="text-sm text-[color:var(--app-text-muted)]">
        {t('settings.team.invitations.empty')}
      </p>
    );
  }

  return (
    <div className="space-y-3">
      <div className="overflow-x-auto ring-1 ring-[color:var(--app-ring)] rounded-lg">
        <table className="min-w-full text-sm">
          <thead className="bg-[color:var(--app-table-header)] text-[color:var(--app-text-muted)]">
            <tr>
              <th className="px-4 py-3 text-left font-medium">
                {t('settings.team.invitations.columns.email')}
              </th>
              <th className="px-4 py-3 text-left font-medium">
                {t('settings.team.invitations.columns.role')}
              </th>
              <th className="px-4 py-3 text-left font-medium">
                {t('settings.team.invitations.columns.expires')}
              </th>
              <th className="px-4 py-3 text-left font-medium">
                {t('settings.team.invitations.columns.actions')}
              </th>
            </tr>
          </thead>
          <tbody>
            {invitations.map((invitation, index) => {
              const isBusy = busyInvitationId === invitation.id;
              return (
                <tr
                  key={invitation.id}
                  className={
                    index % 2 === 0
                      ? 'bg-[color:var(--app-table-row)]'
                      : 'bg-[color:var(--app-table-row-alt)]'
                  }
                >
                  <td className="px-4 py-3 text-[color:var(--app-text-strong)]">
                    {invitation.email}
                  </td>
                  <td className="px-4 py-3 text-[color:var(--app-text-muted)]">
                    {t(`settings.team.roles.${invitation.role}`)}
                  </td>
                  <td className="px-4 py-3 text-[color:var(--app-text-muted)]">
                    {formatDate(invitation.expires_at)}
                  </td>
                  <td className="px-4 py-3">
                    {confirmRevokeId === invitation.id ? (
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-sm text-[color:var(--app-text-muted)]">
                          {t('settings.team.invitations.revokeConfirm')}
                        </span>
                        <Button
                          type="button"
                          variant="destructive"
                          size="sm"
                          className="min-h-11"
                          disabled={isBusy}
                          onClick={() => {
                            void onRevoke(invitation.id).finally(() => setConfirmRevokeId(null));
                          }}
                        >
                          {t('common.confirm')}
                        </Button>
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          className="min-h-11"
                          disabled={isBusy}
                          onClick={() => setConfirmRevokeId(null)}
                        >
                          {t('common.cancel')}
                        </Button>
                      </div>
                    ) : (
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        className="min-h-11"
                        disabled={isBusy}
                        onClick={() => setConfirmRevokeId(invitation.id)}
                      >
                        {t('settings.team.invitations.revoke')}
                      </Button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {loadMoreRef ? <div ref={loadMoreRef} className="h-1" aria-hidden /> : null}
      {isFetchingNextPage ? (
        <p className="text-sm text-[color:var(--app-text-muted)]">{t('common.loading')}</p>
      ) : null}
    </div>
  );
}
