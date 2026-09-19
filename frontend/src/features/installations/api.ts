// frontend/src/features/installations/api.ts
import apiClient, { parseSuccess } from '@/lib/api';
import type { GitHubAccountType, GitHubInstallationStatus } from '@/shared/types/enums';

export interface GitHubInstallation {
  id: string;
  workspace_id: string;
  github_installation_id: number;
  account_login: string;
  account_type: GitHubAccountType;
  account_id: number;
  status: GitHubInstallationStatus;
  permissions_snapshot: Record<string, string> | null;
  verified_at: string | null;
  created_at: string;
  updated_at: string;
}

interface CursorMeta {
  next_cursor: string | null;
  has_next: boolean;
}

interface CursorResponse<T> {
  items: T[];
  cursor: CursorMeta;
}

export interface RegisterInstallationPayload {
  github_installation_id: number;
  account_login: string;
  account_type: GitHubAccountType;
  account_id: number;
  permissions_snapshot?: Record<string, string>;
}

export async function fetchInstallations(workspaceId: string): Promise<GitHubInstallation[]> {
  const response = await apiClient.get(`/workspaces/${workspaceId}/installations`);
  const page = await parseSuccess<CursorResponse<GitHubInstallation>>(response);
  return page.items;
}

export async function registerInstallation(
  workspaceId: string,
  payload: RegisterInstallationPayload,
): Promise<GitHubInstallation> {
  const response = await apiClient.post(`/workspaces/${workspaceId}/installations`, payload);
  return await parseSuccess<GitHubInstallation>(response);
}

export interface ConnectInstallationResponse {
  install_url: string;
}

export async function connectInstallation(
  workspaceId: string,
): Promise<ConnectInstallationResponse> {
  const response = await apiClient.post(`/workspaces/${workspaceId}/installations/connect`);
  return await parseSuccess<ConnectInstallationResponse>(response);
}
