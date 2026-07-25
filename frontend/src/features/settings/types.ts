// frontend/src/features/settings/types.ts
import type { AppRole } from '@/shared/types/enums';

export type InvitationStatus = 'pending' | 'accepted' | 'revoked' | 'expired';

export type WorkspaceStatus = 'active' | 'suspended';

export interface Workspace {
  id: string;
  name: string;
  slug: string;
  status: WorkspaceStatus;
}

export interface Member {
  user_id: string;
  email: string;
  full_name: string | null;
  role: AppRole;
  created_at: string;
}

export interface Invitation {
  id: string;
  email: string;
  role: AppRole;
  status: InvitationStatus;
  expires_at: string;
  created_at: string;
}

export interface CursorMeta {
  next_cursor: string | null;
  has_next: boolean;
}

export interface CursorPage<T> {
  items: T[];
  cursor: CursorMeta;
}

export interface WorkspaceUpdatePayload {
  name: string;
}

export interface MemberRoleUpdatePayload {
  role: AppRole;
}

export interface InvitationCreatePayload {
  email: string;
  role: AppRole;
}

export interface BillingStatus {
  plan: string;
  stripe_enabled: boolean;
}

export interface CheckoutSessionResponse {
  url: string;
}

export interface PortalSessionResponse {
  url: string;
}

export type ExportJobStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface ExportJobCreateResponse {
  job_id: string;
}

export interface ExportJobStatusResponse {
  status: ExportJobStatus;
  created_at: string;
  completed_at: string | null;
  expires_at: string | null;
}

export interface DeleteWorkspacePayload {
  confirm_slug: string;
}

export interface DeleteAccountPayload {
  confirm_email: string;
}
