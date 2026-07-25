// frontend/src/features/admin/components/ImpersonationBanner.tsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/contexts/AuthContext';
import { stopImpersonation } from '@/features/admin/api';
import { Button } from '@/components/ui/button';
import { mapApiError } from '@/shared/errors';
import { showDomainErrorToast } from '@/shared/errors/toasts';

export function ImpersonationBanner() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { user, refetchUser } = useAuth();
  const [busy, setBusy] = useState(false);

  if (!user?.impersonation?.active) {
    return null;
  }

  const { target_email: targetEmail, reason } = user.impersonation;
  const reasonSnippet = reason.length > 80 ? `${reason.slice(0, 80)}…` : reason;

  async function handleStop() {
    setBusy(true);
    try {
      await stopImpersonation();
      await refetchUser();
      void navigate('/dashboard');
    } catch (error) {
      showDomainErrorToast(mapApiError(error));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      role="status"
      className="shrink-0 border-b border-[color-mix(in_oklab,var(--app-warning)_30%,transparent)] bg-[color:var(--app-warning-subtle)] px-4 py-2"
    >
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-[color:var(--app-text-strong)]">
          {t('admin.impersonation.banner', {
            email: targetEmail,
            reason: reasonSnippet,
          })}
        </p>
        <Button type="button" size="sm" variant="outline" disabled={busy} onClick={() => void handleStop()}>
          {busy ? t('common.loading') : t('admin.impersonation.stop')}
        </Button>
      </div>
    </div>
  );
}
