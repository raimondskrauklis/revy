// frontend/src/features/dashboard/hooks.ts
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@/contexts/AuthContext';
import { fetchWorkspaceAudit } from '@/features/dashboard/api';
import { fetchInstallations } from '@/features/installations/api';
import { fetchMemberCount } from '@/features/settings/api';

export const dashboardQueryKeys = {
  audit: (workspaceId: string, limit?: number) =>
    ['dashboard', 'audit', workspaceId, limit ?? 10] as const,
  checklistContext: (workspaceId: string) =>
    ['dashboard', 'checklist-context', workspaceId] as const,
};

export function useWorkspaceAudit(
  workspaceId: string | null | undefined,
  options?: { limit?: number },
) {
  const limit = options?.limit ?? 10;

  return useQuery({
    queryKey: dashboardQueryKeys.audit(workspaceId ?? '', limit),
    queryFn: () => fetchWorkspaceAudit(workspaceId!, { limit }),
    enabled: Boolean(workspaceId),
  });
}

export function useChecklistContext(workspaceId: string | null | undefined) {
  const { user } = useAuth();

  return useQuery({
    queryKey: dashboardQueryKeys.checklistContext(workspaceId ?? ''),
    queryFn: async () => {
      const [memberCount, installations] = await Promise.all([
        fetchMemberCount(workspaceId!),
        fetchInstallations(workspaceId!),
      ]);
      return {
        workspaceId: workspaceId!,
        memberCount: memberCount.count,
        installationCount: installations.length,
        hasVerifiedInstallation: installations.some((row) => Boolean(row.verified_at)),
        plan: user?.workspace_plan ?? 'free',
      };
    },
    enabled: Boolean(workspaceId),
  });
}
