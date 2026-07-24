// frontend/src/features/auth/api.ts
import apiClient, { parseSuccess } from '@/lib/api';
import type { MeUser } from '@/lib/me';

export interface CompleteProfilePayload {
  full_name: string;
}

export async function completeProfile(payload: CompleteProfilePayload): Promise<MeUser> {
  const response = await apiClient.post('/users/complete-profile', payload);
  return parseSuccess<MeUser>(response);
}
