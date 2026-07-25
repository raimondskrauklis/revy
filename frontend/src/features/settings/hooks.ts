// frontend/src/features/settings/hooks.ts
export const settingsQueryKeys = {
  workspace: (workspaceId: string) => ['settings', 'workspace', workspaceId] as const,
  members: (workspaceId: string) => ['settings', 'members', workspaceId] as const,
  invitations: (workspaceId: string, status = 'pending') =>
    ['settings', 'invitations', workspaceId, status] as const,
};
