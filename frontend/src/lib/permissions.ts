// frontend/src/lib/permissions.ts
/**
 * UI permission helpers — mirrors backend ROLE_PERMISSIONS.
 * Workspace vs platform: docs/backend/TENANCY.md
 */
import { AppRole, PlatformRole } from '@/shared/types/enums';
import type { Permission } from '@/lib/permissionTypes';

const WORKSPACE_ROLE_PERMISSIONS: Record<AppRole, ReadonlySet<Permission>> = {
  [AppRole.admin]: new Set(['items:view', 'items:manage', 'admin:users']),
  [AppRole.operator]: new Set(['items:view', 'items:manage']),
  [AppRole.viewer]: new Set(['items:view']),
};

/** Workspace role → permission list for settings matrix UI. */
export const ROLE_PERMISSIONS: Record<AppRole, readonly Permission[]> = {
  [AppRole.admin]: ['items:view', 'items:manage', 'admin:users'],
  [AppRole.operator]: ['items:view', 'items:manage'],
  [AppRole.viewer]: ['items:view'],
};

export function hasPermission(
  workspaceRole: AppRole | undefined,
  permission: Permission,
  platformRole?: PlatformRole,
): boolean {
  if (platformRole === PlatformRole.super_admin) return true;
  if (workspaceRole == null) return false;
  return WORKSPACE_ROLE_PERMISSIONS[workspaceRole]?.has(permission) ?? false;
}

export function isPlatformAdmin(platformRole?: PlatformRole): boolean {
  return platformRole === PlatformRole.super_admin;
}

export function hasItemsManagePermission(
  workspaceRole: AppRole | undefined,
  platformRole?: PlatformRole,
): boolean {
  return hasPermission(workspaceRole, 'items:manage', platformRole);
}

export function canManageWorkspaces(platformRole?: PlatformRole): boolean {
  return platformRole === PlatformRole.super_admin;
}
