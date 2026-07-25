// frontend/src/features/dashboard/pages/DashboardPage.tsx
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/contexts/AuthContext';
import { DashboardGrid } from '@/features/dashboard/layout/DashboardGrid';
import { QuickActionsWidget } from '@/features/dashboard/widgets/QuickActionsWidget';
import { RecentActivityWidget } from '@/features/dashboard/widgets/RecentActivityWidget';
import { SetupChecklistWidget } from '@/features/dashboard/widgets/SetupChecklistWidget';
import { WelcomeWidget } from '@/features/dashboard/widgets/WelcomeWidget';
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

      <WelcomeWidget />

      {hasWorkspace ? (
        <>
          <SetupChecklistWidget />
          <QuickActionsWidget />
          <RecentActivityWidget />
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
      ) : null}
    </div>
  );
}
