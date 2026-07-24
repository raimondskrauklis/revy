// frontend/src/features/installations/pages/InstallationsPage.tsx
import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/contexts/AuthContext';
import {
  fetchInstallations,
  registerInstallation,
  type GitHubInstallation,
  type RegisterInstallationPayload,
} from '@/features/installations/api';
import { InstallationsTable } from '@/features/installations/components/InstallationsTable';
import { RegisterInstallationForm } from '@/features/installations/components/RegisterInstallationForm';
import { AppRole } from '@/shared/types/enums';
import { mapApiError } from '@/shared/errors';
import { showDomainErrorToast } from '@/shared/errors/toasts';

export function InstallationsPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const workspaceId = user?.workspace_id ?? null;
  const canRegister = user?.role === AppRole.admin;

  const [installations, setInstallations] = useState<GitHubInstallation[]>([]);
  const [loading, setLoading] = useState(true);
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

  async function handleRegister(payload: RegisterInstallationPayload) {
    if (!workspaceId) return;
    setSubmitting(true);
    try {
      await registerInstallation(workspaceId, payload);
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

      {!workspaceId ? (
        <p className="text-sm text-[color:var(--app-text-muted)]">{t('installations.noWorkspace')}</p>
      ) : loading ? (
        <p className="text-sm text-[color:var(--app-text-muted)]">{t('common.loading')}</p>
      ) : (
        <InstallationsTable installations={installations} />
      )}

      {canRegister && workspaceId ? (
        <RegisterInstallationForm onSubmit={handleRegister} submitting={submitting} />
      ) : null}
    </div>
  );
}
