// frontend/src/platform/extensions/registerRevy.ts
import { InstallationsSummaryWidget } from '@/features/installations/InstallationsSummaryWidget';
import { PlanSummaryWidget } from '@/features/dashboard/widgets/PlanSummaryWidget';
import { RevyGitHubIntegrationCard } from '@/features/installations/RevyGitHubIntegrationCard';
import { registerExtension } from '@/platform/extensions/registry';

export function registerRevyExtensions(): void {
  registerExtension({
    id: 'revy-github',
    slot: 'settings_integration',
    component: RevyGitHubIntegrationCard,
    permission: 'items:view',
    order: 10,
  });
  registerExtension({
    id: 'installations-summary',
    slot: 'dashboard_widget',
    component: InstallationsSummaryWidget,
    permission: 'items:view',
    order: 20,
  });
  registerExtension({
    id: 'plan-summary',
    slot: 'dashboard_widget',
    component: PlanSummaryWidget,
    permission: 'items:view',
    order: 25,
  });
}
