// frontend/src/features/admin/pages/WorkspacesPage.tsx
import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  fetchAdminWorkspaces,
  type AdminWorkspaceListItem,
  type WorkspaceStatus,
} from '@/features/admin/api';
import { QuietInput } from '@/components/ui/quiet-input';
import {
  QuietSelect,
  QuietSelectContent,
  QuietSelectItem,
  QuietSelectTrigger,
  QuietSelectValue,
} from '@/components/ui/quiet-select';
import { Button } from '@/components/ui/button';
import { formatDate } from '@/lib/date';
import { mapApiError } from '@/shared/errors';
import { showDomainErrorToast } from '@/shared/errors/toasts';

type StatusFilter = WorkspaceStatus | 'all';

export function WorkspacesPage() {
  const { t } = useTranslation();
  const [workspaces, setWorkspaces] = useState<AdminWorkspaceListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasNext, setHasNext] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);

  const loadWorkspaces = useCallback(
    async (cursor?: string) => {
      const isLoadMore = Boolean(cursor);
      if (isLoadMore) {
        setLoadingMore(true);
      } else {
        setLoading(true);
      }
      try {
        const page = await fetchAdminWorkspaces({
          cursor,
          search: search.trim() || undefined,
          status: statusFilter === 'all' ? undefined : statusFilter,
        });
        setWorkspaces((prev) => (isLoadMore ? [...prev, ...page.items] : page.items));
        setNextCursor(page.cursor.next_cursor);
        setHasNext(page.cursor.has_next);
      } catch (error) {
        showDomainErrorToast(mapApiError(error));
      } finally {
        setLoading(false);
        setLoadingMore(false);
      }
    },
    [search, statusFilter],
  );

  useEffect(() => {
    void loadWorkspaces();
  }, [loadWorkspaces]);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold text-[color:var(--app-text-strong)]">
          {t('admin.workspaces.title')}
        </h1>
        <p className="text-sm text-[color:var(--app-text-muted)]">
          {t('admin.workspaces.description')}
        </p>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row">
        <QuietInput
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder={t('admin.workspaces.searchPlaceholder')}
          aria-label={t('admin.workspaces.searchPlaceholder')}
          className="sm:max-w-xs"
        />
        <QuietSelect
          value={statusFilter}
          onValueChange={(value) => setStatusFilter(value as StatusFilter)}
        >
          <QuietSelectTrigger aria-label={t('admin.workspaces.statusFilter')}>
            <QuietSelectValue />
          </QuietSelectTrigger>
          <QuietSelectContent>
            <QuietSelectItem value="all">{t('admin.workspaces.status.all')}</QuietSelectItem>
            <QuietSelectItem value="active">{t('admin.workspaces.status.active')}</QuietSelectItem>
            <QuietSelectItem value="suspended">
              {t('admin.workspaces.status.suspended')}
            </QuietSelectItem>
          </QuietSelectContent>
        </QuietSelect>
      </div>

      {loading ? (
        <p className="text-sm text-[color:var(--app-text-muted)]">{t('common.loading')}</p>
      ) : workspaces.length === 0 ? (
        <p className="text-sm text-[color:var(--app-text-muted)]">{t('admin.workspaces.empty')}</p>
      ) : (
        <div className="overflow-x-auto rounded-lg ring-1 ring-[color:var(--app-ring)]">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead className="bg-[color:var(--app-chip)] text-[color:var(--app-text-muted)]">
              <tr>
                <th className="px-4 py-3 font-medium">{t('admin.workspaces.columns.name')}</th>
                <th className="px-4 py-3 font-medium">{t('admin.workspaces.columns.slug')}</th>
                <th className="px-4 py-3 font-medium">{t('admin.workspaces.columns.status')}</th>
                <th className="px-4 py-3 font-medium">{t('admin.workspaces.columns.plan')}</th>
                <th className="px-4 py-3 font-medium">{t('admin.workspaces.columns.members')}</th>
                <th className="px-4 py-3 font-medium">{t('admin.workspaces.columns.created')}</th>
              </tr>
            </thead>
            <tbody>
              {workspaces.map((workspace) => (
                <tr
                  key={workspace.id}
                  className="border-t border-[color:var(--app-ring)] hover:bg-[color:var(--app-chip)]"
                >
                  <td className="px-4 py-3">
                    <Link
                      to={`/admin/workspaces/${workspace.id}`}
                      className="font-medium text-[color:var(--app-link)] hover:underline focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
                    >
                      {workspace.name}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-[color:var(--app-text-muted)]">{workspace.slug}</td>
                  <td className="px-4 py-3">
                    {t(`admin.workspaces.status.${workspace.status}`)}
                  </td>
                  <td className="px-4 py-3 text-[color:var(--app-text-muted)]">
                    {workspace.plan ?? '—'}
                  </td>
                  <td className="px-4 py-3">{workspace.member_count}</td>
                  <td className="px-4 py-3 text-[color:var(--app-text-muted)]">
                    {formatDate(workspace.created_at)}
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
          onClick={() => void loadWorkspaces(nextCursor)}
        >
          {loadingMore ? t('common.loading') : t('common.loadMore')}
        </Button>
      ) : null}
    </div>
  );
}
