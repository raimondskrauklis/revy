// frontend/src/platform/extensions/hooks.ts
import { useAuth } from '@/contexts/AuthContext';
import { getExtensions } from '@/platform/extensions/registry';
import type { ExtensionDefinition } from '@/platform/extensions/types';
import type { ExtensionSlot } from '@/platform/extensions/slots';

function meetsMinPlan(currentPlan: string, minPlan?: string): boolean {
  if (!minPlan) {
    return true;
  }
  if (minPlan === 'pro') {
    return currentPlan === 'pro';
  }
  return currentPlan === minPlan;
}

export function useExtensions(slot: ExtensionSlot): ExtensionDefinition[] {
  const { user } = useAuth();
  const plan = user?.workspace_plan ?? 'free';

  return getExtensions(slot, user?.role ?? undefined, user?.platform_role ?? undefined).filter(
    (definition) => meetsMinPlan(plan, definition.minPlan),
  );
}
