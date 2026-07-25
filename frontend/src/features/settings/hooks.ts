// frontend/src/features/settings/hooks.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useInfiniteList } from '@/hooks/useInfiniteList';
import {
  createInvitation,
  fetchInvitations,
  fetchMembers,
  patchWorkspace,
  removeMember,
  revokeInvitation,
  updateMemberRole,
} from '@/features/settings/api';
import type {
  Invitation,
  InvitationCreatePayload,
  Member,
  MemberRoleUpdatePayload,
  WorkspaceUpdatePayload,
} from '@/features/settings/types';

export const settingsQueryKeys = {
  workspace: (workspaceId: string) => ['settings', 'workspace', workspaceId] as const,
  members: (workspaceId: string) => ['settings', 'members', workspaceId] as const,
  invitations: (workspaceId: string, status = 'pending') =>
    ['settings', 'invitations', workspaceId, status] as const,
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
