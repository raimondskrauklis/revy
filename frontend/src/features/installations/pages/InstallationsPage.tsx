// frontend/src/features/installations/pages/InstallationsPage.tsx
import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useSearchParams } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import {
  connectInstallation,
  fetchInstallations,
  registerInstallation,
  verifyInstallation,
  type GitHubInstallation,
  type RegisterInstallationPayload,
} from '@/features/installations/api';
import { ConnectGitHubPanel } from '@/features/installations/components/ConnectGitHubPanel';
import { InstallationsTable } from '@/features/installations/components/InstallationsTable';
import { AppRole } from '@/shared/types/enums';
import { mapApiError } from '@/shared/errors';
import { showDomainErrorToast } from '@/shared/errors/toasts';

const SETUP_ERROR_KEYS = new Set([
  'invalid_state',
  'not_configured',
  'oauth_denied',
  'github_installer_mismatch',
  'conflict',
  'not_found',
  'github_unavailable',
  'plan_upgrade_required',
]);

export function InstallationsPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [searchParams] = useSearchParams();
  const workspaceId = user?.workspace_id ?? null;
  const canConnect = user?.role === AppRole.admin && user?.status === 'active';
  const setupError = searchParams.get('setup_error');
  const setupErrorKey = setupError && SETUP_ERROR_KEYS.has(setupError) ? setupError : null;

  const [installations, setInstallations] = useState<GitHubInstallation[]>([]);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const loadInstallations = useCallback(async () => {
    if (!workspaceId) {
      setInstallations([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      setInstallations(await fetchInstallations(workspaceId));
    } catch (error) {
      showDomainErrorToast(mapApiError(error));
    } finally {
      setLoading(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    void loadInstallations();
  }, [loadInstallations]);

  async function handleConnect() {
    if (!workspaceId) return;
    setConnecting(true);
    try {
      const { install_url } = await connectInstallation(workspaceId);
      window.location.assign(install_url);
    } catch (error) {
      showDomainErrorToast(mapApiError(error));
      setConnecting(false);
    }
  }

  async function handleRegister(payload: RegisterInstallationPayload) {
    if (!workspaceId) return;
    setSubmitting(true);
    try {
      const created = await registerInstallation(workspaceId, payload);
      try {
        await verifyInstallation(workspaceId, created.id);
      } catch (error) {
        showDomainErrorToast(mapApiError(error));
      }
      await loadInstallations();
    } catch (error) {
      showDomainErrorToast(mapApiError(error));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-[color:var(--app-text-strong)]">
          {t('installations.title')}
        </h1>
        <p className="text-sm text-[color:var(--app-text-muted)]">{t('installations.subtitle')}</p>
      </div>

      {setupError ? (
        <p
          role="alert"
          className="rounded-lg bg-[color:var(--app-chip)] px-4 py-3 text-sm text-[color:var(--app-text-strong)]"
        >
          {t(`installations.setupError.${setupErrorKey ?? 'unknown'}`)}
        </p>
      ) : null}

      {!workspaceId ? (
        <p className="text-sm text-[color:var(--app-text-muted)]">{t('installations.noWorkspace')}</p>
      ) : loading ? (
        <p className="text-sm text-[color:var(--app-text-muted)]">{t('common.loading')}</p>
      ) : (
        <InstallationsTable installations={installations} />
      )}

      {canConnect && workspaceId ? (
        <ConnectGitHubPanel
          connecting={connecting}
          submittingFallback={submitting}
          onConnect={handleConnect}
          onFallbackSubmit={handleRegister}
        />
      ) : null}
    </div>
  );
}
