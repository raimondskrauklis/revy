// frontend/src/features/dashboard/widgets/QuickActionsWidget.tsx
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { hasPermission } from '@/lib/permissions';

const linkClassName =
  'inline-flex min-h-11 items-center justify-center rounded-lg bg-[color:var(--app-surface)] px-4 text-sm font-medium text-[color:var(--app-text-strong)] ring-1 ring-[color:var(--app-ring)] focus-visible:ring-2 ring-[color:var(--app-ring-strong)]';

export function QuickActionsWidget() {
  const { t } = useTranslation();
  const { user } = useAuth();

  if (!user?.workspace_id) {
    return null;
  }

  const canInvite = hasPermission(
    user.role ?? undefined,
    'admin:users',
    user.platform_role ?? undefined,
  );

  return (
    <section className="space-y-3 rounded-lg bg-[color:var(--app-surface)] p-4 ring-1 ring-[color:var(--app-ring)]">
      <h2 className="text-base font-medium text-[color:var(--app-text-strong)]">
        {t('dashboard.quickActions.title')}
      </h2>
      <div className="flex flex-wrap gap-3">
        <Link to="/settings/profile" className={linkClassName}>
          {t('dashboard.quickActions.settings')}
        </Link>
        <Link to="/installations" className={linkClassName}>
          {t('dashboard.quickActions.installations')}
        </Link>
        {canInvite ? (
          <Link to="/settings/team" className={linkClassName}>
            {t('dashboard.quickActions.inviteTeammate')}
          </Link>
        ) : null}
      </div>
    </section>
  );
}
