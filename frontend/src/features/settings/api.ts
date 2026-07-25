// frontend/src/features/settings/api.ts
import apiClient, { parseSuccess } from '@/lib/api';
import type {
  CursorPage,
  Invitation,
  Member,
  MemberRoleUpdatePayload,
  Workspace,
  WorkspaceUpdatePayload,
} from '@/features/settings/types';
import type { InvitationStatus } from '@/features/settings/types';

export async function patchWorkspace(
  workspaceId: string,
  payload: WorkspaceUpdatePayload,
): Promise<Workspace> {
  const response = await apiClient.patch(`/workspaces/${workspaceId}`, payload);
  return await parseSuccess<Workspace>(response);
}

export async function fetchMembers(
  workspaceId: string,
  cursor?: string,
): Promise<CursorPage<Member>> {
  const response = await apiClient.get(`/workspaces/${workspaceId}/members`, {
    params: cursor ? { cursor } : undefined,
  });
  return await parseSuccess<CursorPage<Member>>(response);
}

export async function updateMemberRole(
  workspaceId: string,
  userId: string,
  payload: MemberRoleUpdatePayload,
): Promise<Member> {
  const response = await apiClient.patch(
    `/workspaces/${workspaceId}/members/${userId}`,
    payload,
  );
  return await parseSuccess<Member>(response);
}

export async function removeMember(workspaceId: string, userId: string): Promise<void> {
  await apiClient.delete(`/workspaces/${workspaceId}/members/${userId}`);
}

export async function fetchInvitations(
  workspaceId: string,
  status: InvitationStatus = 'pending',
  cursor?: string,
): Promise<CursorPage<Invitation>> {
  const response = await apiClient.get(`/workspaces/${workspaceId}/invitations`, {
    params: { status, ...(cursor ? { cursor } : {}) },
  });
  return await parseSuccess<CursorPage<Invitation>>(response);
}

export async function revokeInvitation(
  workspaceId: string,
  invitationId: string,
): Promise<void> {
  await apiClient.delete(`/workspaces/${workspaceId}/invitations/${invitationId}`);
}
