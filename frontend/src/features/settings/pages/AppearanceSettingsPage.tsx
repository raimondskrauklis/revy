// frontend/src/features/settings/pages/AppearanceSettingsPage.tsx
import { useTranslation } from 'react-i18next';

export function AppearanceSettingsPage() {
  const { t } = useTranslation();

  return (
    <div className="max-w-lg space-y-4">
      <h1 className="text-xl font-semibold text-[color:var(--app-text-strong)]">
        {t('settings.nav.appearance')}
      </h1>
      <p className="text-sm text-[color:var(--app-text-muted)]">{t('settings.appearance.body')}</p>
    </div>
  );
}
