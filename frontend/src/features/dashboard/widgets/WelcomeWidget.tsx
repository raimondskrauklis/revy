// frontend/src/features/dashboard/widgets/WelcomeWidget.tsx
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/contexts/AuthContext';

export function WelcomeWidget() {
  const { t } = useTranslation();
  const { user } = useAuth();

  if (!user?.workspace_id) {
    return (
      <section className="rounded-lg bg-[color:var(--app-surface)] p-4 ring-1 ring-[color:var(--app-ring)]">
        <p className="text-sm text-[color:var(--app-text-muted)]">{t('dashboard.noWorkspace')}</p>
      </section>
    );
  }

  const workspaceName =
    user.memberships.find((membership) => membership.workspace_id === user.workspace_id)
      ?.workspace_name ?? t('header.workspace.unknown');
  const displayName = user.full_name?.trim() || user.email;

  return (
    <section className="rounded-lg bg-[color:var(--app-surface)] p-4 ring-1 ring-[color:var(--app-ring)]">
      <h2 className="text-lg font-semibold text-[color:var(--app-text-strong)]">
        {t('dashboard.welcome.greeting', { name: displayName })}
      </h2>
      <p className="mt-1 text-sm text-[color:var(--app-text-muted)]">
        {t('dashboard.welcome.workspace', { workspace: workspaceName })}
      </p>
    </section>
  );
}
