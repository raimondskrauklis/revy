// frontend/src/features/reviewer/pages/ReviewerHomePage.tsx
import { useEffect, useState, useCallback } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useQueryClient } from '@tanstack/react-query';
import { TableSkeleton } from '@/components/ui/TableSkeleton';
import {
  QuietSelect,
  QuietSelectContent,
  QuietSelectItem,
  QuietSelectTrigger,
  QuietSelectValue,
} from '@/components/ui/quiet-select';
import { useInstallationRepositories, reviewerQueryKeys } from '@/features/reviewer/hooks';
import { useReviewerRepoHop } from '@/features/reviewer/useReviewerRepoHop';
import { mapApiError } from '@/shared/errors';
import { showDomainErrorToast } from '@/shared/errors/toasts';

export function ReviewerHomePage() {
  const { t } = useTranslation();
  const {
    workspaceId,
    installations,
    installationsError,
    isLoadingInstallations,
    shouldHop,
    hopRepositoryId,
    hopRepositories,
    hopReposLoading,
    hopReposError,
    hopReposRef,
    isLoading: hopLoading,
  } = useReviewerRepoHop();

  const [selectedInstallationId, setSelectedInstallationId] = useState<string | null>(null);
  const multiInstall = installations.length > 1;
  const activeInstallationId = selectedInstallationId ?? installations[0]?.id ?? null;

  const queryClient = useQueryClient();
  const handleRefresh = useCallback(() => {
    if (workspaceId) {
      queryClient.invalidateQueries({ queryKey: reviewerQueryKeys.installations(workspaceId) });
      queryClient.invalidateQueries({ queryKey: ['reviewer', 'repositories', workspaceId] });
    }
  }, [queryClient, workspaceId]);

  const selectedReposQuery = useInstallationRepositories(
    workspaceId,
    multiInstall ? activeInstallationId : null,
  );

  const repositories = multiInstall ? selectedReposQuery.items : hopRepositories;
  const loadingRepos = multiInstall ? selectedReposQuery.isLoading : hopReposLoading;
  const reposError = multiInstall ? selectedReposQuery.error : hopReposError;
  const ref = multiInstall ? selectedReposQuery.ref : hopReposRef;

  useEffect(() => {
    if (installationsError) {
      showDomainErrorToast(mapApiError(installationsError));
    }
  }, [installationsError]);

  useEffect(() => {
    if (reposError) {
      showDomainErrorToast(mapApiError(reposError));
    }
  }, [reposError]);

  if (!workspaceId) {
    return (
      <p className="text-sm text-[color:var(--app-text-muted)]">{t('reviewer.noWorkspace')}</p>
    );
  }

  if (shouldHop && hopRepositoryId) {
    return (
      <Navigate to={`/reviewer/repositories/${hopRepositoryId}/pull-requests`} replace />
    );
  }

  const listError = installationsError ?? reposError;

  return (
    <div className="space-y-6">
      {installations.length > 1 && activeInstallationId ? (
        <label className="flex max-w-md flex-col gap-1 text-sm">
          <span className="text-[color:var(--app-text-muted)]">{t('reviewer.installation')}</span>
          <QuietSelect value={activeInstallationId} onValueChange={setSelectedInstallationId}>
            <QuietSelectTrigger fullWidth>
              <QuietSelectValue />
            </QuietSelectTrigger>
            <QuietSelectContent>
              {installations.map((installation) => (
                <QuietSelectItem key={installation.id} value={installation.id}>
                  {installation.account_login}
                </QuietSelectItem>
              ))}
            </QuietSelectContent>
          </QuietSelect>
        </label>
      ) : null}

      {listError ? (
        <p className="text-sm text-[color:var(--app-danger)]">{t('reviewer.repositories.error')}</p>
      ) : hopLoading || isLoadingInstallations || loadingRepos ? (
        <TableSkeleton rows={3} columns={3} />
      ) : repositories.length === 0 ? (
        <div className="flex flex-col items-center gap-4 py-12 text-center">
          <p className="text-sm font-medium text-[color:var(--app-text-strong)]">
            {t('reviewer.repositories.empty')}
          </p>
          <p className="text-sm text-[color:var(--app-text-muted)]">
            {t('reviewer.repositories.emptyHelp')}
          </p>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={handleRefresh}
              className="inline-flex min-h-11 items-center justify-center rounded-[var(--app-radius-md)] bg-[color:var(--app-chip)] px-4 text-sm font-medium text-[color:var(--app-text-strong)] hover:bg-[color:var(--app-chip-active)]"
            >
              {t('reviewer.repositories.refresh')}
            </button>
            <Link
              to="/installations"
              className="inline-flex min-h-11 items-center justify-center rounded-[var(--app-radius-md)] bg-[color:var(--app-cta-bg)] px-4 text-sm font-medium text-[color:var(--app-cta-fg)] hover:opacity-95"
            >
              {t('reviewer.repositories.manageInstallations')}
            </Link>
          </div>
        </div>
      ) : (
        <>
          {/* Mobile cards */}
          <div className="md:hidden flex flex-col gap-2">
            {repositories.map((repo) => (
              <Link
                key={repo.id}
                to={`/reviewer/repositories/${repo.id}/pull-requests`}
                className="flex flex-col gap-1 rounded-[var(--app-radius-sm)] border border-[color:var(--app-ring)] bg-[color:var(--app-surface)] p-3 shadow-[inset_0_0_0_1px_var(--app-ring)]"
              >
                <span className="text-sm font-medium text-[color:var(--app-text-strong)]">
                  {repo.name}
                </span>
                <span className="font-mono text-xs text-[color:var(--app-text-muted)]">
                  {repo.full_name}
                </span>
              </Link>
            ))}
          </div>

          {/* Desktop table */}
          <div className="hidden md:block overflow-x-auto rounded-[var(--app-radius-sm)] shadow-[inset_0_0_0_1px_var(--app-ring)]">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-[color:var(--app-chip)] text-[color:var(--app-text-muted)]">
                <tr>
                  <th className="px-3 py-2 font-medium">{t('reviewer.repositories.name')}</th>
                  <th className="px-3 py-2 font-medium">{t('reviewer.repositories.fullName')}</th>
                </tr>
              </thead>
              <tbody>
                {repositories.map((repository) => (
                  <tr key={repository.id} className="border-t border-[color:var(--app-ring)]">
                    <td className="px-3 py-2">
                      <Link
                        to={`/reviewer/repositories/${repository.id}/pull-requests`}
                        className="font-medium text-[color:var(--app-text-strong)] hover:underline focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
                      >
                        {repository.name}
                      </Link>
                    </td>
                    <td className="px-3 py-2 font-mono text-[color:var(--app-text-muted)]">
                      {repository.full_name}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div ref={ref} className="h-4" />
          </div>
        </>
      )}
    </div>
  );
}
