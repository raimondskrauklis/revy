// frontend/src/features/reviewer/pages/PullRequestListPage.tsx
import { Link, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
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

  if (isLoading) {
    return <p className="text-sm text-[color:var(--app-text-muted)]">{t('common.loading')}</p>;
  }

  if (pullRequests.length === 0) {
    return (
      <p className="text-sm text-[color:var(--app-text-muted)]">{t('reviewer.pullRequests.empty')}</p>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg ring-1 ring-[color:var(--app-ring)]">
      <table className="min-w-full text-left text-sm">
        <thead className="bg-[color:var(--app-chip)] text-[color:var(--app-text-muted)]">
          <tr>
            <th className="px-3 py-2 font-medium">{t('reviewer.pullRequests.number')}</th>
            <th className="px-3 py-2 font-medium">{t('reviewer.pullRequests.title')}</th>
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
              <td className="px-3 py-2 text-[color:var(--app-text-strong)]">{pullRequest.title}</td>
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
  );
}
