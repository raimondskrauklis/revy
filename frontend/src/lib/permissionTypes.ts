// frontend/src/lib/permissionTypes.ts
/** Mirror backend Permission enum — docs/backend/PERMISSIONS.md */
export type Permission =
  | 'items:view'
  | 'items:manage'
  | 'admin:users'
  | 'admin:workspaces'
  | 'admin:system';
