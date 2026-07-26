// frontend/src/features/reviewer/pages/ReviewerHomePage.tsx
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/contexts/AuthContext';
import { fetchInstallations, type GitHubInstallation } from '@/features/installations/api';
import { useInstallationRepositories } from '@/features/reviewer/hooks';
import { mapApiError } from '@/shared/errors';
import { showDomainErrorToast } from '@/shared/errors/toasts';

export function ReviewerHomePage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const workspaceId = user?.workspace_id ?? null;

  const [installations, setInstallations] = useState<GitHubInstallation[]>([]);
  const [selectedInstallationId, setSelectedInstallationId] = useState<string | null>(null);
  const [loadingInstallations, setLoadingInstallations] = useState(true);

  const {
    items: repositories,
    isLoading: loadingRepos,
    error: reposError,
    ref,
  } = useInstallationRepositories(workspaceId, selectedInstallationId);

  useEffect(() => {
    if (!workspaceId) {
      setInstallations([]);
      setLoadingInstallations(false);
      return;
    }
    let cancelled = false;
    setLoadingInstallations(true);
    void fetchInstallations(workspaceId)
      .then((rows) => {
        if (cancelled) return;
        setInstallations(rows);
        if (rows[0]) {
          setSelectedInstallationId(rows[0].id);
        }
      })
      .catch((error) => {
        if (!cancelled) {
          showDomainErrorToast(mapApiError(error));
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoadingInstallations(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [workspaceId]);

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

  return (
    <div className="space-y-6">
      {installations.length > 1 ? (
        <label className="flex max-w-md flex-col gap-1 text-sm">
          <span className="text-[color:var(--app-text-muted)]">{t('reviewer.installation')}</span>
          <select
            className="min-h-11 rounded-lg border border-[color:var(--app-ring)] bg-[color:var(--app-surface)] px-3 text-[color:var(--app-text-strong)]"
            value={selectedInstallationId ?? ''}
            onChange={(event) => setSelectedInstallationId(event.target.value || null)}
          >
            {installations.map((installation) => (
              <option key={installation.id} value={installation.id}>
                {installation.account_login}
              </option>
            ))}
          </select>
        </label>
      ) : null}

      {loadingInstallations || loadingRepos ? (
        <p className="text-sm text-[color:var(--app-text-muted)]">{t('common.loading')}</p>
      ) : repositories.length === 0 ? (
        <p className="text-sm text-[color:var(--app-text-muted)]">{t('reviewer.repositories.empty')}</p>
      ) : (
        <div className="overflow-x-auto rounded-lg ring-1 ring-[color:var(--app-ring)]">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-[color:var(--app-chip)] text-[color:var(--app-text-muted)]">
              <tr>
                <th className="px-3 py-2 font-medium">{t('reviewer.repositories.name')}</th>
                <th className="px-3 py-2 font-medium">{t('reviewer.repositories.fullName')}</th>
                <th className="px-3 py-2 font-medium">{t('reviewer.repositories.actions')}</th>
              </tr>
            </thead>
            <tbody>
              {repositories.map((repository) => (
                <tr key={repository.id} className="border-t border-[color:var(--app-ring)]">
                  <td className="px-3 py-2 text-[color:var(--app-text-strong)]">{repository.name}</td>
                  <td className="px-3 py-2 font-mono text-[color:var(--app-text-muted)]">
                    {repository.full_name}
                  </td>
                  <td className="px-3 py-2">
                    <Link
                      to={`/reviewer/repositories/${repository.id}/pull-requests`}
                      className="text-[color:var(--app-link)] hover:underline focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
                    >
                      {t('reviewer.repositories.viewPullRequests')}
                    </Link>
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
