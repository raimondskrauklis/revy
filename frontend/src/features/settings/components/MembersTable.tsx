// frontend/src/features/settings/components/MembersTable.tsx
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  QuietSelect,
  QuietSelectContent,
  QuietSelectItem,
  QuietSelectTrigger,
  QuietSelectValue,
} from '@/components/ui/quiet-select';
import { Button } from '@/components/ui/button';
import { formatDate } from '@/lib/date';
import type { Member } from '@/features/settings/types';
import { AppRole } from '@/shared/types/enums';

const ROLE_OPTIONS = [AppRole.admin, AppRole.operator, AppRole.viewer] as const;

interface MembersTableProps {
  members: Member[];
  canManage: boolean;
  currentUserId?: string;
  busyUserId: string | null;
  onRoleChange: (userId: string, role: AppRole) => Promise<void>;
  onRemove: (userId: string) => Promise<void>;
  loadMoreRef?: (node?: Element | null) => void;
  isFetchingNextPage?: boolean;
}

export function MembersTable({
  members,
  canManage,
  currentUserId,
  busyUserId,
  onRoleChange,
  onRemove,
  loadMoreRef,
  isFetchingNextPage,
}: MembersTableProps) {
  const { t } = useTranslation();
  const [confirmRemoveId, setConfirmRemoveId] = useState<string | null>(null);

  if (members.length === 0) {
    return (
      <p className="text-sm text-[color:var(--app-text-muted)]">{t('settings.team.members.empty')}</p>
    );
  }

  return (
    <div className="space-y-3">
      <div className="overflow-x-auto ring-1 ring-[color:var(--app-ring)] rounded-lg">
        <table className="min-w-full text-sm">
          <thead className="bg-[color:var(--app-table-header)] text-[color:var(--app-text-muted)]">
            <tr>
              <th className="px-4 py-3 text-left font-medium">
                {t('settings.team.members.columns.name')}
              </th>
              <th className="px-4 py-3 text-left font-medium">
                {t('settings.team.members.columns.email')}
              </th>
              <th className="px-4 py-3 text-left font-medium">
                {t('settings.team.members.columns.role')}
              </th>
              <th className="px-4 py-3 text-left font-medium">
                {t('settings.team.members.columns.joined')}
              </th>
              {canManage ? (
                <th className="px-4 py-3 text-left font-medium">
                  {t('settings.team.members.columns.actions')}
                </th>
              ) : null}
            </tr>
          </thead>
          <tbody>
            {members.map((member, index) => {
              const isBusy = busyUserId === member.user_id;
              const isSelf = member.user_id === currentUserId;
              return (
                <tr
                  key={member.user_id}
                  className={
                    index % 2 === 0
                      ? 'bg-[color:var(--app-table-row)]'
                      : 'bg-[color:var(--app-table-row-alt)]'
                  }
                >
                  <td className="px-4 py-3 text-[color:var(--app-text-strong)]">
                    {member.full_name ?? '—'}
                  </td>
                  <td className="px-4 py-3 text-[color:var(--app-text-muted)]">{member.email}</td>
                  <td className="px-4 py-3">
                    {canManage ? (
                      <QuietSelect
                        value={member.role}
                        onValueChange={(value) => void onRoleChange(member.user_id, value as AppRole)}
                        disabled={isBusy}
                      >
                        <QuietSelectTrigger className="min-w-32">
                          <QuietSelectValue />
                        </QuietSelectTrigger>
                        <QuietSelectContent>
                          {ROLE_OPTIONS.map((role) => (
                            <QuietSelectItem key={role} value={role}>
                              {t(`settings.team.roles.${role}`)}
                            </QuietSelectItem>
                          ))}
                        </QuietSelectContent>
                      </QuietSelect>
                    ) : (
                      <span className="text-[color:var(--app-text-muted)]">
                        {t(`settings.team.roles.${member.role}`)}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-[color:var(--app-text-muted)]">
                    {formatDate(member.created_at)}
                  </td>
                  {canManage ? (
                    <td className="px-4 py-3">
                      {confirmRemoveId === member.user_id ? (
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="text-sm text-[color:var(--app-text-muted)]">
                            {t('settings.team.members.removeConfirm')}
                          </span>
                          <Button
                            type="button"
                            variant="destructive"
                            size="sm"
                            className="min-h-11"
                            disabled={isBusy}
                            onClick={() => {
                              void onRemove(member.user_id).finally(() => setConfirmRemoveId(null));
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
                            onClick={() => setConfirmRemoveId(null)}
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
                          disabled={isBusy || isSelf}
                          onClick={() => setConfirmRemoveId(member.user_id)}
                        >
                          {t('settings.team.members.remove')}
                        </Button>
                      )}
                    </td>
                  ) : null}
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
