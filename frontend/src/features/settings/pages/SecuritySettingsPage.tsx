// frontend/src/features/settings/pages/SecuritySettingsPage.tsx
import { useTranslation } from 'react-i18next';
import { ExternalLink } from 'lucide-react';
import { getKeycloakAccountUrl } from '@/lib/keycloak';

export function SecuritySettingsPage() {
  const { t } = useTranslation();
  const accountUrl = getKeycloakAccountUrl();

  return (
    <div className="max-w-lg space-y-4">
      <h1 className="text-xl font-semibold text-[color:var(--app-text-strong)]">
        {t('settings.nav.security')}
      </h1>
      <p className="text-sm text-[color:var(--app-text-muted)]">{t('settings.security.body')}</p>
      <a
        href={accountUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex min-h-11 items-center gap-2 rounded-lg bg-[color:var(--app-cta-bg)] px-4 text-sm font-medium text-[color:var(--app-cta-fg)] focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
      >
        {t('settings.security.openAccount')}
        <ExternalLink className="h-4 w-4" aria-hidden />
      </a>
    </div>
  );
}
