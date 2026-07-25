// frontend/src/features/settings/pages/SettingsShellPage.tsx
import { useTranslation } from 'react-i18next';

export function SettingsShellPage() {
  const { t } = useTranslation();

  return (
    <div>
      <h1 className="text-xl font-semibold text-[color:var(--app-text-strong)]">
        {t('settings.shell.title')}
      </h1>
    </div>
  );
}
