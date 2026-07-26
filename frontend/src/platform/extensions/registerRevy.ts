// frontend/src/platform/extensions/registerRevy.ts
import { InstallationsSummaryWidget } from '@/features/installations/InstallationsSummaryWidget';
import { PlanSummaryWidget } from '@/features/dashboard/widgets/PlanSummaryWidget';
import { RevyGitHubIntegrationCard } from '@/features/installations/RevyGitHubIntegrationCard';
import { ReviewerNavItem } from '@/features/reviewer/ReviewerNavItem';
import { ReviewerSummaryWidget } from '@/features/reviewer/ReviewerSummaryWidget';
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
    id: 'reviewer-nav',
    slot: 'nav_item',
    component: ReviewerNavItem,
    permission: 'items:view',
    order: 15,
  });
  registerExtension({
    id: 'installations-summary',
    slot: 'dashboard_widget',
    component: InstallationsSummaryWidget,
    permission: 'items:view',
    order: 20,
  });
  registerExtension({
    id: 'reviewer-summary',
    slot: 'dashboard_widget',
    component: ReviewerSummaryWidget,
    permission: 'items:view',
    order: 25,
  });
  registerExtension({
    id: 'plan-summary',
    slot: 'dashboard_widget',
    component: PlanSummaryWidget,
    permission: 'admin:users',
    order: 30,
  });
}
