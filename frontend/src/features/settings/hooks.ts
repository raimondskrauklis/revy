// frontend/src/features/settings/hooks.ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@/contexts/AuthContext';
import { useInfiniteList } from '@/hooks/useInfiniteList';
import { hasPermission } from '@/lib/permissions';
import type {
  DeleteAccountPayload,
  DeleteWorkspacePayload,
  Invitation,
  InvitationCreatePayload,
  Member,
  MemberRoleUpdatePayload,
  WorkspaceUpdatePayload,
} from '@/features/settings/types';
import {
  createCheckoutSession,
  createExportJob,
  createInvitation,
  createPortalSession,
  deleteAccount,
  deleteWorkspace,
  downloadExportJob,
  fetchBillingStatus,
  fetchExportJobStatus,
  fetchInvitations,
  fetchMembers,
  leaveWorkspace,
  patchWorkspace,
  removeMember,
  revokeInvitation,
  updateMemberRole,
} from '@/features/settings/api';

export const settingsQueryKeys = {
  workspace: (workspaceId: string) => ['settings', 'workspace', workspaceId] as const,
  members: (workspaceId: string) => ['settings', 'members', workspaceId] as const,
  invitations: (workspaceId: string, status = 'pending') =>
    ['settings', 'invitations', workspaceId, status] as const,
  billing: (workspaceId: string) => ['settings', 'billing', workspaceId] as const,
  exportJob: (jobId: string) => ['settings', 'export', jobId] as const,
};

export function useMembers(workspaceId: string | null | undefined) {
  return useInfiniteList<Member>({
    queryKey: [...settingsQueryKeys.members(workspaceId ?? '')],
    queryFn: (cursor) => fetchMembers(workspaceId!, cursor ?? undefined),
    enabled: Boolean(workspaceId),
  });
}

export function useInvitations(workspaceId: string | null | undefined, enabled = true) {
  return useInfiniteList<Invitation>({
    queryKey: [...settingsQueryKeys.invitations(workspaceId ?? '')],
    queryFn: (cursor) => fetchInvitations(workspaceId!, 'pending', cursor ?? undefined),
    enabled: Boolean(workspaceId) && enabled,
  });
}

export function usePatchWorkspace(workspaceId: string | null | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: WorkspaceUpdatePayload) => {
      if (!workspaceId) throw new Error('workspace_required');
      return patchWorkspace(workspaceId, payload);
    },
    onSuccess: async () => {
      if (workspaceId) {
        await queryClient.invalidateQueries({ queryKey: settingsQueryKeys.workspace(workspaceId) });
      }
    },
  });
}

export function useUpdateMemberRole(workspaceId: string | null | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId, payload }: { userId: string; payload: MemberRoleUpdatePayload }) => {
      if (!workspaceId) throw new Error('workspace_required');
      return updateMemberRole(workspaceId, userId, payload);
    },
    onSuccess: async () => {
      if (workspaceId) {
        await queryClient.invalidateQueries({ queryKey: settingsQueryKeys.members(workspaceId) });
      }
    },
  });
}

export function useRemoveMember(workspaceId: string | null | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (userId: string) => {
      if (!workspaceId) throw new Error('workspace_required');
      return removeMember(workspaceId, userId);
    },
    onSuccess: async () => {
      if (workspaceId) {
        await queryClient.invalidateQueries({ queryKey: settingsQueryKeys.members(workspaceId) });
      }
    },
  });
}

export function useCreateInvitation(workspaceId: string | null | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: InvitationCreatePayload) => {
      if (!workspaceId) throw new Error('workspace_required');
      return createInvitation(workspaceId, payload);
    },
    onSuccess: async () => {
      if (workspaceId) {
        await queryClient.invalidateQueries({
          queryKey: settingsQueryKeys.invitations(workspaceId),
        });
      }
    },
  });
}

export function useRevokeInvitation(workspaceId: string | null | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (invitationId: string) => {
      if (!workspaceId) throw new Error('workspace_required');
      return revokeInvitation(workspaceId, invitationId);
    },
    onSuccess: async () => {
      if (workspaceId) {
        await queryClient.invalidateQueries({
          queryKey: settingsQueryKeys.invitations(workspaceId),
        });
      }
    },
  });
}

export function useBillingStatus(workspaceId: string | null | undefined) {
  const { user } = useAuth();
  const canManageBilling = hasPermission(
    user?.role ?? undefined,
    'admin:users',
    user?.platform_role ?? undefined,
  );

  return useQuery({
    queryKey: settingsQueryKeys.billing(workspaceId ?? ''),
    queryFn: () => fetchBillingStatus(workspaceId!),
    enabled: Boolean(workspaceId) && canManageBilling,
  });
}

export function useCreateCheckoutSession(workspaceId: string | null | undefined) {
  return useMutation({
    mutationFn: () => {
      if (!workspaceId) throw new Error('workspace_required');
      return createCheckoutSession(workspaceId);
    },
  });
}

export function useCreatePortalSession(workspaceId: string | null | undefined) {
  return useMutation({
    mutationFn: () => {
      if (!workspaceId) throw new Error('workspace_required');
      return createPortalSession(workspaceId);
    },
  });
}

export function useCreateExportJob() {
  return useMutation({
    mutationFn: () => createExportJob(),
  });
}

export function useExportJobStatus(jobId: string | null) {
  return useQuery({
    queryKey: settingsQueryKeys.exportJob(jobId ?? ''),
    queryFn: () => fetchExportJobStatus(jobId!),
    enabled: Boolean(jobId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === 'pending' || status === 'processing') {
        return 2000;
      }
      return false;
    },
  });
}

export function useLeaveWorkspace(workspaceId: string | null | undefined) {
  return useMutation({
    mutationFn: () => {
      if (!workspaceId) throw new Error('workspace_required');
      return leaveWorkspace(workspaceId);
    },
  });
}

export function useDeleteWorkspace(workspaceId: string | null | undefined) {
  return useMutation({
    mutationFn: (payload: DeleteWorkspacePayload) => {
      if (!workspaceId) throw new Error('workspace_required');
      return deleteWorkspace(workspaceId, payload);
    },
  });
}

export function useDeleteAccount() {
  return useMutation({
    mutationFn: (payload: DeleteAccountPayload) => deleteAccount(payload),
  });
}

export async function downloadUserExport(jobId: string): Promise<Blob> {
  return downloadExportJob(jobId);
}
