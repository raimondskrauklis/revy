// frontend/src/features/dashboard/widgets/RecentActivityWidget.tsx
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/contexts/AuthContext';
import { useWorkspaceAudit } from '@/features/dashboard/hooks';
import { formatRelative } from '@/lib/date';

function activityLabelKey(action: string): string {
  return `dashboard.activity.${action}`;
}

export function RecentActivityWidget() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const workspaceId = user?.workspace_id ?? null;
  const { data, isLoading } = useWorkspaceAudit(workspaceId, { limit: 10 });

  if (!workspaceId) {
    return null;
  }

  return (
    <section className="space-y-3 rounded-lg bg-[color:var(--app-surface)] p-4 ring-1 ring-[color:var(--app-ring)]">
      <h2 className="text-base font-medium text-[color:var(--app-text-strong)]">
        {t('dashboard.activity.title')}
      </h2>
      {isLoading ? (
        <p className="text-sm text-[color:var(--app-text-muted)]">{t('common.loading')}</p>
      ) : !data?.items.length ? (
        <p className="text-sm text-[color:var(--app-text-muted)]">{t('dashboard.activity.empty')}</p>
      ) : (
        <ul className="space-y-3">
          {data.items.map((item) => (
            <li key={item.id} className="flex flex-col gap-0.5 sm:flex-row sm:items-baseline sm:justify-between">
              <div>
                <p className="text-sm text-[color:var(--app-text-strong)]">
                  {t(activityLabelKey(item.action), {
                    email: item.actor_email,
                    defaultValue: item.action,
                  })}
                </p>
                <p className="text-xs text-[color:var(--app-text-muted)]">{item.actor_email}</p>
              </div>
              <time
                className="text-xs text-[color:var(--app-text-muted)]"
                dateTime={item.created_at}
              >
                {formatRelative(item.created_at)}
              </time>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
