// frontend/src/features/settings/pages/SecuritySettingsPage.tsx
import { useTranslation } from 'react-i18next';

export function SecuritySettingsPage() {
  const { t } = useTranslation();

  return (
    <div className="max-w-lg space-y-4">
      <h1 className="text-xl font-semibold text-[color:var(--app-text-strong)]">
        {t('settings.nav.security')}
      </h1>
      <p className="text-sm text-[color:var(--app-text-muted)]">{t('settings.security.body')}</p>
    </div>
  );
}
