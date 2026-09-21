// frontend/src/features/settings/pages/BillingSettingsPage.tsx
import { useTranslation } from 'react-i18next';
import { useSearchParams } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { useBillingStatus } from '@/features/settings/hooks';

export function BillingSettingsPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const workspaceId = user?.workspace_id ?? null;
  const [searchParams] = useSearchParams();

  const { data: billing, isLoading } = useBillingStatus(workspaceId);

  const plan = billing?.plan ?? 'free';
  const stripeEnabled = billing?.stripe_enabled ?? false;
  const stripeReturn = searchParams.get('session_id') ? 'success' : null;

  if (!user || !workspaceId) {
    return null;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-[color:var(--app-text-strong)]">
        {t('settings.nav.billing')}
      </h1>

      {stripeReturn === 'success' && (
        <div className="rounded-[var(--app-radius-md)] border border-[color:var(--app-success)] bg-[color:var(--app-success-subtle)] px-4 py-3 text-sm text-[color:var(--app-text-strong)]">
          {t('settings.billing.stripeReturn.success')}
        </div>
      )}

      {isLoading ? (
        <p className="text-sm text-[color:var(--app-text-muted)]">{t('common.loading')}</p>
      ) : (
        <div className="space-y-4 rounded-lg bg-[color:var(--app-surface)] p-4 ring-1 ring-[color:var(--app-ring)]">
          <div className="flex items-center justify-between gap-3">
            <span className="text-sm text-[color:var(--app-text-muted)]">
              {t('settings.billing.currentPlan')}
            </span>
            <span className="rounded-full bg-[color:var(--app-chip-active)] px-3 py-1 text-sm font-medium text-[color:var(--app-text-strong)]">
              {t(`settings.billing.plans.${plan}`)}
            </span>
          </div>

          {!stripeEnabled && (
            <p className="text-sm text-[color:var(--app-text-muted)]">
              {t('settings.billing.notConfigured')}
            </p>
          )}
        </div>
      )}
    </div>
  );
}