// frontend/src/features/settings/pages/SecuritySettingsPage.tsx
import { useTranslation } from 'react-i18next';

export function SecuritySettingsPage() {
  const { t } = useTranslation();

  return (
    <div className="max-w-lg space-y-4">
      <h1 className="text-xl font-semibold text-[color:var(--app-text-strong)]">
        {t('settings.nav.security')}
      </h1>
      <div className="flex flex-col items-center gap-4 rounded-[var(--app-radius-md)] border border-[color:var(--app-ring)] bg-[color:var(--app-surface)] p-8 text-center">
        <p className="text-sm text-[color:var(--app-text-muted)]">
          {t('settings.security.body')}
        </p>
        <a
          href="https://github.com/raimondskrauklis/revy/issues/new"
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm text-[color:var(--app-link)] hover:underline"
        >
          {t('dashboard.devNotice.feedback')}
        </a>
      </div>
    </div>
  );
}