// frontend/src/features/settings/pages/IntegrationsSettingsPage.tsx
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/contexts/AuthContext';
import { getExtensions } from '@/platform/extensions/registry';

export function IntegrationsSettingsPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const extensions = getExtensions(
    'settings_integration',
    user?.role ?? undefined,
    user?.platform_role ?? undefined,
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-[color:var(--app-text-strong)]">
          {t('settings.nav.integrations')}
        </h1>
        <p className="text-sm text-[color:var(--app-text-muted)]">
          {t('settings.integrations.subtitle')}
        </p>
      </div>
      {extensions.length === 0 ? (
        <p className="text-sm text-[color:var(--app-text-muted)]">
          {t('settings.integrations.empty')}
        </p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {extensions.map((extension) => {
            const Component = extension.component;
            return <Component key={extension.id} />;
          })}
        </div>
      )}
    </div>
  );
}
