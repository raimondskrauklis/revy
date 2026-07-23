// frontend/src/shared/types/enums.ts
/** Workspace-scoped roles — from workspace_memberships / GET /api/v1/me */
export enum AppRole {
  admin = 'admin',
  operator = 'operator',
  viewer = 'viewer',
}

/** Platform staff — not workspace-scoped */
export enum PlatformRole {
  super_admin = 'super_admin',
}
