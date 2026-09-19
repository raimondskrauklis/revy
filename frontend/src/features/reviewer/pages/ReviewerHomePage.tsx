// frontend/src/features/reviewer/pages/ReviewerHomePage.tsx
import { useEffect, useState } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  QuietSelect,
  QuietSelectContent,
  QuietSelectItem,
  QuietSelectTrigger,
  QuietSelectValue,
} from '@/components/ui/quiet-select';
import { useInstallationRepositories } from '@/features/reviewer/hooks';
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
    isLoading: hopLoading,
  } = useReviewerRepoHop();

  const [selectedInstallationId, setSelectedInstallationId] = useState<string | null>(null);
  const activeInstallationId = selectedInstallationId ?? installations[0]?.id ?? null;

  const {
    items: repositories,
    isLoading: loadingRepos,
    error: reposError,
    ref,
  } = useInstallationRepositories(workspaceId, activeInstallationId);

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
        <p className="text-sm text-[color:var(--app-text-muted)]">{t('reviewer.repositories.loading')}</p>
      ) : repositories.length === 0 ? (
        <p className="text-sm text-[color:var(--app-text-muted)]">{t('reviewer.repositories.empty')}</p>
      ) : (
        <div className="overflow-x-auto rounded-[var(--app-radius-sm)] shadow-[inset_0_0_0_1px_var(--app-ring)]">
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
      )}
    </div>
  );
}
