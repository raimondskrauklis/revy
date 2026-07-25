// frontend/src/features/admin/pages/AuditSearchPage.tsx
import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  fetchPlatformAudit,
  type PlatformAuditListItem,
} from '@/features/admin/api';
import { QuietInput } from '@/components/ui/quiet-input';
import { Button } from '@/components/ui/button';
import { formatDateTime } from '@/lib/date';
import { mapApiError } from '@/shared/errors';
import { showDomainErrorToast } from '@/shared/errors/toasts';

function auditActionLabel(t: (key: string) => string, action: string): string {
  const key = `admin.audit.actions.${action}`;
  const translated = t(key);
  return translated === key ? action : translated;
}

export function AuditSearchPage() {
  const { t } = useTranslation();
  const [items, setItems] = useState<PlatformAuditListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasNext, setHasNext] = useState(false);

  const [workspaceId, setWorkspaceId] = useState('');
  const [actorUserId, setActorUserId] = useState('');
  const [actionPrefix, setActionPrefix] = useState('');
  const [createdAtFrom, setCreatedAtFrom] = useState('');
  const [createdAtTo, setCreatedAtTo] = useState('');

  const loadAudit = useCallback(
    async (cursor?: string) => {
      const isLoadMore = Boolean(cursor);
      if (isLoadMore) {
        setLoadingMore(true);
      } else {
        setLoading(true);
      }
      try {
        const page = await fetchPlatformAudit({
          cursor,
          workspace_id: workspaceId.trim() || undefined,
          actor_user_id: actorUserId.trim() || undefined,
          action_prefix: actionPrefix.trim() || undefined,
          created_at_from: createdAtFrom.trim() || undefined,
          created_at_to: createdAtTo.trim() || undefined,
        });
        setItems((prev) => (isLoadMore ? [...prev, ...page.items] : page.items));
        setNextCursor(page.cursor.next_cursor);
        setHasNext(page.cursor.has_next);
      } catch (error) {
        showDomainErrorToast(mapApiError(error));
      } finally {
        setLoading(false);
        setLoadingMore(false);
      }
    },
    [workspaceId, actorUserId, actionPrefix, createdAtFrom, createdAtTo],
  );

  useEffect(() => {
    void loadAudit();
  }, [loadAudit]);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold text-[color:var(--app-text-strong)]">
          {t('admin.audit.title')}
        </h1>
        <p className="text-sm text-[color:var(--app-text-muted)]">{t('admin.audit.description')}</p>
        <p className="text-xs text-[color:var(--app-text-muted)]">{t('admin.audit.impersonatorHint')}</p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <QuietInput
          value={workspaceId}
          onChange={(event) => setWorkspaceId(event.target.value)}
          placeholder={t('admin.audit.filters.workspaceId')}
          aria-label={t('admin.audit.filters.workspaceId')}
        />
        <QuietInput
          value={actorUserId}
          onChange={(event) => setActorUserId(event.target.value)}
          placeholder={t('admin.audit.filters.actorUserId')}
          aria-label={t('admin.audit.filters.actorUserId')}
        />
        <QuietInput
          value={actionPrefix}
          onChange={(event) => setActionPrefix(event.target.value)}
          placeholder={t('admin.audit.filters.actionPrefix')}
          aria-label={t('admin.audit.filters.actionPrefix')}
        />
        <QuietInput
          type="date"
          value={createdAtFrom}
          onChange={(event) => setCreatedAtFrom(event.target.value)}
          aria-label={t('admin.audit.filters.createdAtFrom')}
        />
        <QuietInput
          type="date"
          value={createdAtTo}
          onChange={(event) => setCreatedAtTo(event.target.value)}
          aria-label={t('admin.audit.filters.createdAtTo')}
        />
      </div>

      {loading ? (
        <p className="text-sm text-[color:var(--app-text-muted)]">{t('common.loading')}</p>
      ) : items.length === 0 ? (
        <p className="text-sm text-[color:var(--app-text-muted)]">{t('admin.audit.empty')}</p>
      ) : (
        <div className="overflow-x-auto rounded-lg ring-1 ring-[color:var(--app-ring)]">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead className="bg-[color:var(--app-chip)] text-[color:var(--app-text-muted)]">
              <tr>
                <th className="px-4 py-3 font-medium">{t('admin.audit.columns.time')}</th>
                <th className="px-4 py-3 font-medium">{t('admin.audit.columns.action')}</th>
                <th className="px-4 py-3 font-medium">{t('admin.audit.columns.actor')}</th>
                <th className="px-4 py-3 font-medium">{t('admin.audit.columns.impersonator')}</th>
                <th className="px-4 py-3 font-medium">{t('admin.audit.columns.workspace')}</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr
                  key={item.id}
                  className="border-t border-[color:var(--app-ring)] hover:bg-[color:var(--app-chip)]"
                >
                  <td className="px-4 py-3 text-[color:var(--app-text-muted)]">
                    {formatDateTime(item.created_at)}
                  </td>
                  <td className="px-4 py-3">{auditActionLabel(t, item.action)}</td>
                  <td className="px-4 py-3 text-[color:var(--app-text-muted)]">{item.actor_email}</td>
                  <td className="px-4 py-3 text-[color:var(--app-text-muted)]">
                    {item.impersonator_email ?? '—'}
                  </td>
                  <td className="px-4 py-3 text-[color:var(--app-text-muted)]">
                    {item.workspace_id ?? '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {hasNext && nextCursor ? (
        <Button
          type="button"
          variant="outline"
          disabled={loadingMore}
          onClick={() => void loadAudit(nextCursor)}
        >
          {loadingMore ? t('common.loading') : t('common.loadMore')}
        </Button>
      ) : null}
    </div>
  );
}
