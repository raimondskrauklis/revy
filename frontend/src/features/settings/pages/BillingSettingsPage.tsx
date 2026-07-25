// frontend/src/features/settings/pages/BillingSettingsPage.tsx
import { useTranslation } from 'react-i18next';
import { useSearchParams } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import {
  useBillingStatus,
  useCreateCheckoutSession,
  useCreatePortalSession,
} from '@/features/settings/hooks';
import { mapApiError } from '@/shared/errors';
import { showDomainErrorToast } from '@/shared/errors/toasts';

export function BillingSettingsPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const workspaceId = user?.workspace_id ?? null;
  const [searchParams] = useSearchParams();
  const checkoutState = searchParams.get('checkout');

  const { data: billing, isLoading } = useBillingStatus(workspaceId);
  const checkoutMutation = useCreateCheckoutSession(workspaceId);
  const portalMutation = useCreatePortalSession(workspaceId);

  const isBusy = checkoutMutation.isPending || portalMutation.isPending;
  const plan = billing?.plan ?? 'free';
  const stripeEnabled = billing?.stripe_enabled ?? false;

  async function handleUpgrade() {
    try {
      const result = await checkoutMutation.mutateAsync();
      window.location.assign(result.url);
    } catch (error) {
      const domainError = mapApiError(error);
      if (domainError.code === 'billing_disabled') {
        return;
      }
      showDomainErrorToast(domainError);
    }
  }

  async function handleManage() {
    try {
      const result = await portalMutation.mutateAsync();
      window.location.assign(result.url);
    } catch (error) {
      const domainError = mapApiError(error);
      if (domainError.code === 'billing_disabled') {
        return;
      }
      showDomainErrorToast(domainError);
    }
  }

  if (!user || !workspaceId) {
    return null;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-[color:var(--app-text-strong)]">
        {t('settings.nav.billing')}
      </h1>

      {checkoutState === 'success' ? (
        <p className="rounded-lg bg-[color:var(--app-chip)] px-4 py-3 text-sm text-[color:var(--app-text-strong)]">
          {t('settings.billing.checkoutSuccess')}
        </p>
      ) : null}
      {checkoutState === 'cancel' ? (
        <p className="rounded-lg bg-[color:var(--app-chip)] px-4 py-3 text-sm text-[color:var(--app-text-muted)]">
          {t('settings.billing.checkoutCancel')}
        </p>
      ) : null}

      {isLoading ? (
        <p className="text-sm text-[color:var(--app-text-muted)]">{t('common.loading')}</p>
      ) : (
        <section className="max-w-lg space-y-4 rounded-lg bg-[color:var(--app-surface)] p-4 ring-1 ring-[color:var(--app-ring)]">
          <div className="flex items-center justify-between gap-3">
            <span className="text-sm text-[color:var(--app-text-muted)]">
              {t('settings.billing.currentPlan')}
            </span>
            <span className="rounded-full bg-[color:var(--app-chip-active)] px-3 py-1 text-sm font-medium text-[color:var(--app-text-strong)]">
              {t(`settings.billing.plans.${plan}`)}
            </span>
          </div>

          {!stripeEnabled ? (
            <p className="text-sm text-[color:var(--app-text-muted)]">
              {t('settings.billing.notConfigured')}
            </p>
          ) : (
            <div className="flex flex-wrap gap-3">
              {plan !== 'pro' ? (
                <button
                  type="button"
                  onClick={handleUpgrade}
                  disabled={isBusy}
                  className="min-h-11 rounded-lg bg-[color:var(--app-cta-bg)] px-4 text-sm font-medium text-[color:var(--app-cta-fg)] focus-visible:ring-2 ring-[color:var(--app-ring-strong)] disabled:opacity-50"
                >
                  {t('settings.billing.upgrade')}
                </button>
              ) : null}
              {plan === 'pro' ? (
                <button
                  type="button"
                  onClick={handleManage}
                  disabled={isBusy}
                  className="min-h-11 rounded-lg bg-[color:var(--app-chip)] px-4 text-sm font-medium text-[color:var(--app-text-strong)] focus-visible:ring-2 ring-[color:var(--app-ring-strong)] disabled:opacity-50"
                >
                  {t('settings.billing.manage')}
                </button>
              ) : null}
            </div>
          )}
        </section>
      )}
    </div>
  );
}
