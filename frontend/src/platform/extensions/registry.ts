// frontend/src/platform/extensions/registry.ts
import type { ComponentType } from 'react';
import { hasPermission } from '@/lib/permissions';
import type { Permission } from '@/lib/permissionTypes';
import type { ExtensionSlot } from '@/platform/extensions/slots';
import type { AppRole, PlatformRole } from '@/shared/types/enums';

export interface ExtensionDefinition {
  id: string;
  slot: ExtensionSlot;
  component: ComponentType;
  permission?: Permission;
  order?: number;
}

const extensions: ExtensionDefinition[] = [];

export function registerExtension(definition: ExtensionDefinition): void {
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
