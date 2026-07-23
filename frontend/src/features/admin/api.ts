// frontend/src/features/admin/api.ts
import apiClient, { parseSuccess } from '@/lib/api';
import type { UserStatus } from '@/lib/me';

export interface PendingUser {
  id: string;
  email: string;
  full_name: string | null;
  status: UserStatus;
  created_at: string;
}

export async function fetchPendingUsers(): Promise<PendingUser[]> {
  const response = await apiClient.get('/admin/users/pending');
  return parseSuccess<PendingUser[]>(response);
}

export async function approvePendingUser(userId: string): Promise<void> {
  await apiClient.post(`/admin/users/${userId}/approve`);
}

export async function rejectPendingUser(userId: string): Promise<void> {
  await apiClient.post(`/admin/users/${userId}/reject`);
}
