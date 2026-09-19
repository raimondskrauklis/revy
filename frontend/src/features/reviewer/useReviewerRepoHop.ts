// frontend/src/features/reviewer/useReviewerRepoHop.ts
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@/contexts/AuthContext';
import { fetchInstallations } from '@/features/installations/api';
import { reviewerQueryKeys, useInstallationRepositories } from '@/features/reviewer/hooks';

export function useReviewerRepoHop() {
  const { user } = useAuth();
  const workspaceId = user?.workspace_id ?? null;

  const installationsQuery = useQuery({
    queryKey: reviewerQueryKeys.installations(workspaceId ?? ''),
    queryFn: () => fetchInstallations(workspaceId!),
    enabled: Boolean(workspaceId),
  });

  const installations = installationsQuery.data ?? [];
  const hopInstallationId = installations.length <= 1 ? (installations[0]?.id ?? null) : null;

  const hopReposQuery = useInstallationRepositories(workspaceId, hopInstallationId);

  const isLoading =
    Boolean(workspaceId) &&
    (installationsQuery.isLoading ||
      (hopInstallationId != null && hopReposQuery.isLoading));

  const shouldHop =
    !isLoading && installations.length <= 1 && hopReposQuery.items.length === 1;

  return {
    workspaceId,
    installations,
    installationsError: installationsQuery.error,
    isLoadingInstallations: installationsQuery.isLoading,
    shouldHop,
    hopRepositoryId: shouldHop ? hopReposQuery.items[0]!.id : null,
    isLoading,
  };
}
