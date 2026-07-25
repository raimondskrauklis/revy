// frontend/src/features/settings/api.ts
import apiClient, { parseSuccess } from '@/lib/api';
import type {
  BillingStatus,
  CheckoutSessionResponse,
  CursorPage,
  DeleteAccountPayload,
  DeleteWorkspacePayload,
  ExportJobCreateResponse,
  ExportJobStatusResponse,
  Invitation,
  InvitationCreatePayload,
  Member,
  MemberRoleUpdatePayload,
  PortalSessionResponse,
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

export async function fetchMemberCount(workspaceId: string): Promise<{ count: number }> {
  const response = await apiClient.get(`/workspaces/${workspaceId}/members/count`);
  return await parseSuccess<{ count: number }>(response);
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

export async function createInvitation(
  workspaceId: string,
  payload: InvitationCreatePayload,
): Promise<Invitation> {
  const response = await apiClient.post(`/workspaces/${workspaceId}/invitations`, payload);
  return await parseSuccess<Invitation>(response);
}

export async function fetchBillingStatus(workspaceId: string): Promise<BillingStatus> {
  const response = await apiClient.get(`/workspaces/${workspaceId}/billing`);
  return await parseSuccess<BillingStatus>(response);
}

export async function createCheckoutSession(workspaceId: string): Promise<CheckoutSessionResponse> {
  const response = await apiClient.post(`/workspaces/${workspaceId}/billing/checkout-session`, {
    plan: 'pro',
  });
  return await parseSuccess<CheckoutSessionResponse>(response);
}

export async function createPortalSession(workspaceId: string): Promise<PortalSessionResponse> {
  const response = await apiClient.post(`/workspaces/${workspaceId}/billing/portal-session`);
  return await parseSuccess<PortalSessionResponse>(response);
}

export async function createExportJob(): Promise<ExportJobCreateResponse> {
  const response = await apiClient.post('/me/export');
  return await parseSuccess<ExportJobCreateResponse>(response);
}

export async function fetchExportJobStatus(jobId: string): Promise<ExportJobStatusResponse> {
  const response = await apiClient.get(`/me/export/${jobId}`);
  return await parseSuccess<ExportJobStatusResponse>(response);
}

export async function downloadExportJob(jobId: string): Promise<Blob> {
  const response = await apiClient.get(`/me/export/${jobId}/download`, {
    responseType: 'blob',
  });
  return response.data as Blob;
}

export async function leaveWorkspace(workspaceId: string): Promise<void> {
  await apiClient.post(`/workspaces/${workspaceId}/leave`);
}

export async function deleteWorkspace(
  workspaceId: string,
  payload: DeleteWorkspacePayload,
): Promise<void> {
  await apiClient.delete(`/workspaces/${workspaceId}`, { data: payload });
}

export async function deleteAccount(payload: DeleteAccountPayload): Promise<void> {
  await apiClient.delete('/me', { data: payload });
}
