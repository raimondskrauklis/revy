// frontend/src/features/settings/pages/SettingsPage.tsx

import { useTranslation } from 'react-i18next';
import { QuietComponentsDemo } from '@/features/settings/components/QuietComponentsDemo';

export function SettingsPage() {
  const { t } = useTranslation();

  return (
    <div className="space-y-8">
      <h1 className="text-xl font-semibold text-[color:var(--app-text-strong)]">
        {t('settings.title')}
      </h1>
      <QuietComponentsDemo />
    </div>
  );
}
