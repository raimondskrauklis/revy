// frontend/src/features/reviewer/pages/PullRequestListPage.tsx
import { Link, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { TableSkeleton } from '@/components/ui/TableSkeleton';
import { PullRequestStateBadge } from '@/features/reviewer/components/PullRequestStateBadge';
import { usePullRequests } from '@/features/reviewer/hooks';
import { mapApiError } from '@/shared/errors';
import { showDomainErrorToast } from '@/shared/errors/toasts';

export function PullRequestListPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const workspaceId = user?.workspace_id ?? null;
  const { repoId } = useParams<{ repoId: string }>();

  const { items: pullRequests, isLoading, error, ref } = usePullRequests(workspaceId, repoId);

  useEffect(() => {
    if (error) {
      showDomainErrorToast(mapApiError(error));
    }
  }, [error]);

  if (!workspaceId || !repoId) {
    return (
      <p className="text-sm text-[color:var(--app-text-muted)]">{t('reviewer.noWorkspace')}</p>
    );
  }

  if (error) {
    return (
      <p className="text-sm text-[color:var(--app-danger)]">{t('reviewer.pullRequests.error')}</p>
    );
  }

  if (isLoading) {
    return <TableSkeleton rows={3} columns={5} />;
  }

  if (pullRequests.length === 0) {
    return (
      <p className="text-sm text-[color:var(--app-text-muted)]">{t('reviewer.pullRequests.empty')}</p>
    );
  }

  return (
    <>
      {/* Mobile cards */}
      <div className="md:hidden flex flex-col gap-2">
        {pullRequests.map((pr) => (
          <Link
            key={pr.id}
            to={`/reviewer/repositories/${repoId}/pull-requests/${pr.id}`}
            className="flex flex-col gap-1.5 rounded-[var(--app-radius-sm)] border border-[color:var(--app-ring)] bg-[color:var(--app-surface)] p-3 shadow-[inset_0_0_0_1px_var(--app-ring)]"
          >
            <div className="flex items-center justify-between gap-2">
              <span className="text-sm font-medium text-[color:var(--app-link)]">#{pr.number}</span>
              <span className="font-mono text-[10px] text-[color:var(--app-text-muted)]">
                {pr.head_sha.slice(0, 7)}
              </span>
            </div>
            <p className="text-sm text-[color:var(--app-text-strong)]">{pr.title}</p>
            <div className="flex items-center gap-2">
              <PullRequestStateBadge pullRequest={pr} />
              <span className="text-xs text-[color:var(--app-text-muted)]">
                {t('reviewer.pullRequests.revisions')}: {pr.revision_count}
              </span>
            </div>
          </Link>
        ))}
      </div>

      {/* Desktop table */}
      <div className="hidden md:block overflow-x-auto rounded-[var(--app-radius-sm)] shadow-[inset_0_0_0_1px_var(--app-ring)]">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-[color:var(--app-chip)] text-[color:var(--app-text-muted)]">
            <tr>
              <th className="px-3 py-2 font-medium">{t('reviewer.pullRequests.number')}</th>
              <th className="px-3 py-2 font-medium">{t('reviewer.pullRequests.title')}</th>
              <th className="px-3 py-2 font-medium">{t('reviewer.pullRequests.status')}</th>
              <th className="px-3 py-2 font-medium">{t('reviewer.pullRequests.headSha')}</th>
              <th className="px-3 py-2 font-medium">{t('reviewer.pullRequests.revisions')}</th>
            </tr>
          </thead>
          <tbody>
            {pullRequests.map((pullRequest) => (
              <tr key={pullRequest.id} className="border-t border-[color:var(--app-ring)]">
                <td className="px-3 py-2">
                  <Link
                    to={`/reviewer/repositories/${repoId}/pull-requests/${pullRequest.id}`}
                    className="font-medium text-[color:var(--app-link)] hover:underline"
                  >
                    #{pullRequest.number}
                  </Link>
                </td>
                <td className="px-3 py-2 font-sans text-[color:var(--app-text-strong)]">
                  {pullRequest.title}
                </td>
                <td className="px-3 py-2">
                  <PullRequestStateBadge pullRequest={pullRequest} />
                </td>
                <td className="px-3 py-2 font-mono text-xs text-[color:var(--app-text-muted)]">
                  {pullRequest.head_sha.slice(0, 7)}
                </td>
                <td className="px-3 py-2 text-[color:var(--app-text-muted)]">
                  {pullRequest.revision_count}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div ref={ref} className="h-4" />
      </div>
    </>
  );
}
