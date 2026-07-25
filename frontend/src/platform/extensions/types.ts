// frontend/src/platform/extensions/types.ts
import type { ComponentType } from 'react';
import type { Permission } from '@/lib/permissionTypes';
import type { ExtensionSlot } from '@/platform/extensions/slots';

export interface ExtensionDefinition {
  id: string;
  slot: ExtensionSlot;
  component: ComponentType;
  permission?: Permission;
  order?: number;
  minPlan?: string;
}
