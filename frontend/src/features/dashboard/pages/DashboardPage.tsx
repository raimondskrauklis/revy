// frontend/src/features/dashboard/pages/DashboardPage.tsx
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/contexts/AuthContext';
import { DashboardGrid } from '@/features/dashboard/layout/DashboardGrid';
import { SetupChecklistWidget } from '@/features/dashboard/widgets/SetupChecklistWidget';
import { DevNoticeWidget } from '@/features/dashboard/widgets/DevNoticeWidget';
import { useExtensions } from '@/platform/extensions/hooks';
import { WidgetErrorBoundary } from '@/platform/extensions/WidgetErrorBoundary';

export function DashboardPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const dashboardWidgets = useExtensions('dashboard_widget');
  const hasWorkspace = Boolean(user?.workspace_id);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-[color:var(--app-text-strong)]">
          {t('nav.dashboard')}
        </h1>
      </div>

      {hasWorkspace ? (
        <>
          <DevNoticeWidget />
          <SetupChecklistWidget />
          {dashboardWidgets.length > 0 ? (
            <DashboardGrid>
              {dashboardWidgets.map((extension) => {
                const Component = extension.component;
                return (
                  <WidgetErrorBoundary key={extension.id}>
                    <Component />
                  </WidgetErrorBoundary>
                );
              })}
            </DashboardGrid>
          ) : null}
        </>
      ) : (
        <p className="text-sm text-[color:var(--app-text-muted)]">{t('dashboard.noWorkspace')}</p>
      )}
    </div>
  );
}
