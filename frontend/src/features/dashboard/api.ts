// frontend/src/features/dashboard/api.ts
import apiClient, { parseSuccess } from '@/lib/api';
import type { CursorPage } from '@/features/settings/types';

export interface AuditListItem {
  id: string;
  created_at: string;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  actor_user_id: string;
  actor_email: string;
  metadata: Record<string, unknown>;
}

export async function fetchWorkspaceAudit(
  workspaceId: string,
  options?: { cursor?: string; limit?: number },
): Promise<CursorPage<AuditListItem>> {
  const response = await apiClient.get(`/workspaces/${workspaceId}/audit`, {
    params: {
      ...(options?.cursor ? { cursor: options.cursor } : {}),
      ...(options?.limit ? { limit: options.limit } : {}),
    },
  });
  return await parseSuccess<CursorPage<AuditListItem>>(response);
}
