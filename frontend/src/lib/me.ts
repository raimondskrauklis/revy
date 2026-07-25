// frontend/src/lib/me.ts
/** GET /api/v1/me client — docs/backend/ME_ENDPOINT.md */
import apiClient, { parseSuccess, setStoredWorkspaceId } from '@/lib/api';
import { AppRole, PlatformRole } from '@/shared/types/enums';

export type UserStatus =
  | 'pending_activation'
  | 'pending_email_verification'
  | 'pending_profile'
  | 'pending_approval'
  | 'active'
  | 'rejected'
  | 'suspended';

export interface MeMembership {
  workspace_id: string;
  workspace_name: string;
  workspace_slug: string;
  role: AppRole;
}

export interface MeImpersonation {
  active: boolean;
  actor_user_id: string;
  target_user_id: string;
  target_email: string;
  reason: string;
}

export interface MeUser {
  id: string;
  email: string;
  full_name: string | null;
  status: UserStatus;
  platform_role: PlatformRole | null;
  locale: string;
  timezone: string;
  workspace_id: string | null;
  workspace_plan: string | null;
  role: AppRole | null;
  memberships: MeMembership[];
  impersonation?: MeImpersonation | null;
}

export async function fetchMe(): Promise<MeUser> {
  const response = await apiClient.get('/me');
  return parseSuccess<MeUser>(response);
}

export async function setActiveWorkspace(workspaceId: string): Promise<MeUser> {
  const response = await apiClient.patch('/me/workspace', { workspace_id: workspaceId });
  const me = await parseSuccess<MeUser>(response);
  setStoredWorkspaceId(me.workspace_id);
  return me;
}

export interface MeUpdatePayload {
  full_name?: string | null;
  locale?: string;
  timezone?: string;
}

export async function patchMe(payload: MeUpdatePayload): Promise<MeUser> {
  const response = await apiClient.patch('/me', payload);
  return parseSuccess<MeUser>(response);
}

export function syncStoredWorkspace(me: MeUser): MeUser {
  const stored = localStorage.getItem('active_workspace_id');
  if (stored && me.memberships.some((m) => m.workspace_id === stored)) {
    const membership = me.memberships.find((m) => m.workspace_id === stored);
    return {
      ...me,
      workspace_id: stored,
      role: membership?.role ?? me.role,
    };
  }
  if (me.workspace_id) {
    setStoredWorkspaceId(me.workspace_id);
  }
  return me;
}
