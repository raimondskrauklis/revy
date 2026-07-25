// frontend/src/platform/extensions/hooks.ts
import { useAuth } from '@/contexts/AuthContext';
import { getExtensions } from '@/platform/extensions/registry';
import type { ExtensionDefinition } from '@/platform/extensions/types';
import type { ExtensionSlot } from '@/platform/extensions/slots';

export function useExtensions(slot: ExtensionSlot): ExtensionDefinition[] {
  const { user } = useAuth();
  return getExtensions(slot, user?.role ?? undefined, user?.platform_role ?? undefined);
}
