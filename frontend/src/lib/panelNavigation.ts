// frontend/src/lib/panelNavigation.ts
/**
 * Panel → page navigation — docs/frontend/patterns/STACKED_PANELS.md
 */
import { appRouter } from '@/lib/routerInstance';
import { useStackStore } from '@/stores/stackStore';

export function buildEntityPagePath(entityType: string, entityId: string): string {
  return `/${entityType}/${entityId}`;
}

export function navigateFromPanel(
  to: string,
  opts?: { state?: unknown; replace?: boolean },
): void {
  useStackStore.getState().clear();
  void appRouter.navigate(to, opts);
}
