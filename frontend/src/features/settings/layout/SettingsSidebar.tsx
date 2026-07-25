// frontend/src/features/settings/layout/SettingsSidebar.tsx
import { useTranslation } from 'react-i18next';

export function SettingsSidebar() {
  const { t } = useTranslation();

  return (
    <nav
      className="w-full shrink-0 md:w-52"
      aria-label={t('settings.sidebar.label')}
    >
      <div className="space-y-6">
        <div>
          <h2 className="px-3 text-xs font-semibold uppercase tracking-wide text-[color:var(--app-text-muted)]">
            {t('settings.group.personal')}
          </h2>
        </div>
        <div>
          <h2 className="px-3 text-xs font-semibold uppercase tracking-wide text-[color:var(--app-text-muted)]">
            {t('settings.group.workspace')}
          </h2>
        </div>
      </div>
    </nav>
  );
}
