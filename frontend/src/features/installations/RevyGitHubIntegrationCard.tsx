// frontend/src/features/installations/RevyGitHubIntegrationCard.tsx
import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { fetchInstallations } from '@/features/installations/api';
import { mapApiError } from '@/shared/errors';
import { showDomainErrorToast } from '@/shared/errors/toasts';

export function RevyGitHubIntegrationCard() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const workspaceId = user?.workspace_id ?? null;
  const [count, setCount] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  const loadCount = useCallback(async () => {
    if (!workspaceId) {
      setCount(0);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const installations = await fetchInstallations(workspaceId);
      setCount(installations.length);
    } catch (error) {
      showDomainErrorToast(mapApiError(error));
      setCount(0);
    } finally {
      setLoading(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    void loadCount();
  }, [loadCount]);

  return (
    <article className="flex h-full flex-col justify-between gap-4 rounded-lg bg-[color:var(--app-surface)] p-4 ring-1 ring-[color:var(--app-ring)]">
      <div className="space-y-2">
        <h3 className="text-base font-medium text-[color:var(--app-text-strong)]">
          {t('settings.integrations.github.title')}
        </h3>
        <p className="text-sm text-[color:var(--app-text-muted)]">
          {t('settings.integrations.github.description')}
        </p>
        <p className="text-sm text-[color:var(--app-text-strong)]">
          {loading
            ? t('common.loading')
            : t('settings.integrations.github.count', { count: count ?? 0 })}
        </p>
      </div>
      <Link
        to="/installations"
        className="inline-flex min-h-11 items-center justify-center rounded-lg bg-[color:var(--app-cta-bg)] px-4 text-sm font-medium text-[color:var(--app-cta-fg)] focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
      >
        {t('settings.integrations.github.manage')}
      </Link>
    </article>
  );
}
