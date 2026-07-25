// frontend/src/platform/extensions/registerRevy.ts
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
}
