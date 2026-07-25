// frontend/src/platform/extensions/registry.ts
import { hasPermission } from '@/lib/permissions';
import type { AppRole, PlatformRole } from '@/shared/types/enums';
import type { ExtensionDefinition } from '@/platform/extensions/types';
import type { ExtensionSlot } from '@/platform/extensions/slots';

export type { ExtensionDefinition } from '@/platform/extensions/types';

const extensions: ExtensionDefinition[] = [];

export function registerExtension(definition: ExtensionDefinition): void {
  if (extensions.some((item) => item.id === definition.id)) {
    throw new Error(`Extension already registered: ${definition.id}`);
  }
  extensions.push(definition);
}

export function getExtensions(
  slot: ExtensionSlot,
  workspaceRole?: AppRole,
  platformRole?: PlatformRole,
): ExtensionDefinition[] {
  return extensions
    .filter((definition) => definition.slot === slot)
    .filter(
      (definition) =>
        !definition.permission
        || hasPermission(workspaceRole, definition.permission, platformRole),
    )
    .sort((left, right) => (left.order ?? 0) - (right.order ?? 0));
}

export function clearExtensions(): void {
  extensions.length = 0;
}
