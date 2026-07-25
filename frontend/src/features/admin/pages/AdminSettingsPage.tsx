// frontend/src/features/admin/pages/AdminSettingsPage.tsx
import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ExternalLink } from 'lucide-react';
import { fetchAdminSettings, type AdminSettings } from '@/features/admin/api';
import { getKeycloakAdminConsoleUrl } from '@/lib/keycloak';
import { optionalViteEnv } from '@/lib/env';
import { mapApiError } from '@/shared/errors';
import { showDomainErrorToast } from '@/shared/errors/toasts';

function FlagRow({ label, enabled }: { label: string; enabled: boolean }) {
  const { t } = useTranslation();
  return (
    <div className="flex items-center justify-between gap-4 py-2">
      <span className="text-sm text-[color:var(--app-text-strong)]">{label}</span>
      <span className="text-sm text-[color:var(--app-text-muted)]">
        {enabled ? t('common.yes') : t('common.no')}
      </span>
    </div>
  );
}

export function AdminSettingsPage() {
  const { t } = useTranslation();
  const [settings, setSettings] = useState<AdminSettings | null>(null);
  const [loading, setLoading] = useState(true);

  const keycloakAdminUrl = getKeycloakAdminConsoleUrl();
  const stripeDashboardUrl = optionalViteEnv('VITE_STRIPE_DASHBOARD_URL');

  const loadSettings = useCallback(async () => {
    setLoading(true);
    try {
      setSettings(await fetchAdminSettings());
    } catch (error) {
      showDomainErrorToast(mapApiError(error));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadSettings();
  }, [loadSettings]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-[color:var(--app-text-strong)]">
          {t('admin.settings.title')}
        </h1>
        <p className="text-sm text-[color:var(--app-text-muted)]">{t('admin.settings.description')}</p>
      </div>

      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-[color:var(--app-text-strong)]">
          {t('admin.settings.externalLinks')}
        </h2>
        <ul className="space-y-2">
          <li>
            <a
              href={keycloakAdminUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex min-h-11 items-center gap-2 text-sm text-[color:var(--app-link)] hover:underline focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
            >
              {t('admin.settings.keycloakAdmin')}
              <ExternalLink className="h-4 w-4" aria-hidden />
            </a>
          </li>
          {stripeDashboardUrl ? (
            <li>
              <a
                href={stripeDashboardUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex min-h-11 items-center gap-2 text-sm text-[color:var(--app-link)] hover:underline focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
              >
                {t('admin.settings.stripeDashboard')}
                <ExternalLink className="h-4 w-4" aria-hidden />
              </a>
            </li>
          ) : null}
        </ul>
      </section>

      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-[color:var(--app-text-strong)]">
          {t('admin.settings.registrationFlags')}
        </h2>
        {loading ? (
          <p className="text-sm text-[color:var(--app-text-muted)]">{t('common.loading')}</p>
        ) : settings ? (
          <div className="divide-y divide-[color:var(--app-ring)] rounded-lg ring-1 ring-[color:var(--app-ring)] px-4">
            <FlagRow
              label={t('admin.settings.requireAdminApproval')}
              enabled={settings.registration_require_admin_approval}
            />
            <FlagRow
              label={t('admin.settings.requireProfileForm')}
              enabled={settings.registration_require_profile_form}
            />
          </div>
        ) : null}
      </section>
    </div>
  );
}
