// frontend/src/features/admin/api.ts
import apiClient, { parseSuccess } from '@/lib/api';
import type { CursorPage } from '@/features/settings/types';
import type { UserStatus } from '@/lib/me';

export interface PendingUser {
  id: string;
  email: string;
  full_name: string | null;
  status: UserStatus;
  created_at: string;
}

export type WorkspaceStatus = 'active' | 'suspended';

export interface AdminWorkspaceListItem {
  id: string;
  name: string;
  slug: string;
  status: WorkspaceStatus;
  plan: string | null;
  member_count: number;
  created_at: string;
}

export interface AdminWorkspaceDetail extends AdminWorkspaceListItem {
  stripe_customer_id: string | null;
  updated_at: string;
}

export interface AdminKpis {
  workspaces_total: number;
  workspaces_active: number;
  workspaces_suspended: number;
  workspaces_deleted: number;
  users_active: number;
  users_pending_approval: number;
}

export interface AdminSettings {
  registration_require_admin_approval: boolean;
  registration_require_profile_form: boolean;
}

export interface PlatformAuditListItem {
  id: string;
  created_at: string;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  actor_user_id: string;
  actor_email: string;
  impersonator_user_id: string | null;
  impersonator_email: string | null;
  metadata: Record<string, unknown>;
  workspace_id: string | null;
}

export interface AdminWorkspaceMember {
  user_id: string;
  email: string;
  full_name: string | null;
  status: UserStatus;
  role: string;
  joined_at: string;
}

export interface ActiveImpersonation {
  active: boolean;
  target_user_id?: string;
  target_email?: string;
  reason?: string;
  started_at?: string;
}

export interface AdminWorkspaceListParams {
  cursor?: string;
  limit?: number;
  status?: WorkspaceStatus;
  search?: string;
}

export interface PlatformAuditParams {
  cursor?: string;
  limit?: number;
  workspace_id?: string;
  actor_user_id?: string;
  action_prefix?: string;
  created_at_from?: string;
  created_at_to?: string;
}

export async function fetchPendingUsers(): Promise<PendingUser[]> {
  const response = await apiClient.get('/admin/users/pending');
  return parseSuccess<PendingUser[]>(response);
}

export async function approvePendingUser(userId: string): Promise<void> {
  await apiClient.post(`/admin/users/${userId}/approve`);
}

export async function rejectPendingUser(userId: string): Promise<void> {
  await apiClient.post(`/admin/users/${userId}/reject`);
}

export async function fetchAdminWorkspaces(
  params?: AdminWorkspaceListParams,
): Promise<CursorPage<AdminWorkspaceListItem>> {
  const response = await apiClient.get('/admin/workspaces', { params });
  return parseSuccess<CursorPage<AdminWorkspaceListItem>>(response);
}

export async function fetchAdminWorkspaceDetail(
  workspaceId: string,
): Promise<AdminWorkspaceDetail> {
  const response = await apiClient.get(`/admin/workspaces/${workspaceId}`);
  return parseSuccess<AdminWorkspaceDetail>(response);
}

export async function suspendAdminWorkspace(workspaceId: string): Promise<AdminWorkspaceDetail> {
  const response = await apiClient.post(`/admin/workspaces/${workspaceId}/suspend`);
  return parseSuccess<AdminWorkspaceDetail>(response);
}

export async function unsuspendAdminWorkspace(
  workspaceId: string,
): Promise<AdminWorkspaceDetail> {
  const response = await apiClient.post(`/admin/workspaces/${workspaceId}/unsuspend`);
  return parseSuccess<AdminWorkspaceDetail>(response);
}

export async function fetchAdminKpis(): Promise<AdminKpis> {
  const response = await apiClient.get('/admin/kpis');
  return parseSuccess<AdminKpis>(response);
}

export async function fetchAdminSettings(): Promise<AdminSettings> {
  const response = await apiClient.get('/admin/settings');
  return parseSuccess<AdminSettings>(response);
}

export async function fetchPlatformAudit(
  params?: PlatformAuditParams,
): Promise<CursorPage<PlatformAuditListItem>> {
  const response = await apiClient.get('/admin/audit', { params });
  return parseSuccess<CursorPage<PlatformAuditListItem>>(response);
}

export async function fetchAdminWorkspaceMembers(
  workspaceId: string,
  params?: { cursor?: string; limit?: number },
): Promise<CursorPage<AdminWorkspaceMember>> {
  const response = await apiClient.get(`/admin/workspaces/${workspaceId}/members`, { params });
  return parseSuccess<CursorPage<AdminWorkspaceMember>>(response);
}

export async function startImpersonation(
  userId: string,
  reason: string,
): Promise<ActiveImpersonation> {
  const response = await apiClient.post('/admin/impersonation/start', {
    user_id: userId,
    reason,
  });
  return parseSuccess<ActiveImpersonation>(response);
}

export async function stopImpersonation(): Promise<ActiveImpersonation> {
  const response = await apiClient.post('/admin/impersonation/stop');
  return parseSuccess<ActiveImpersonation>(response);
}
