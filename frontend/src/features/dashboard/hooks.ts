// frontend/src/features/dashboard/hooks.ts
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@/contexts/AuthContext';
import { fetchWorkspaceAudit } from '@/features/dashboard/api';
import { fetchInstallations } from '@/features/installations/api';
import { fetchBillingStatus, fetchMembers } from '@/features/settings/api';
import { hasPermission } from '@/lib/permissions';

export const dashboardQueryKeys = {
  audit: (workspaceId: string, limit?: number) =>
    ['dashboard', 'audit', workspaceId, limit ?? 10] as const,
  checklistContext: (workspaceId: string, includeBilling: boolean) =>
    ['dashboard', 'checklist-context', workspaceId, includeBilling] as const,
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
  const includeBilling = hasPermission(
    user?.role ?? undefined,
    'admin:users',
    user?.platform_role ?? undefined,
  );

  return useQuery({
    queryKey: dashboardQueryKeys.checklistContext(workspaceId ?? '', includeBilling),
    queryFn: async () => {
      const [membersPage, installations, billing] = await Promise.all([
        fetchMembers(workspaceId!),
        fetchInstallations(workspaceId!),
        includeBilling
          ? fetchBillingStatus(workspaceId!)
          : Promise.resolve({ plan: 'free', stripe_enabled: false }),
      ]);
      return {
        workspaceId: workspaceId!,
        memberCount: membersPage.items.length,
        installationCount: installations.length,
        plan: billing.plan,
      };
    },
    enabled: Boolean(workspaceId),
  });
}
