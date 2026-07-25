// frontend/src/features/settings/api.test.ts
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AppRole } from '@/shared/types/enums';

vi.mock('@/lib/api', () => ({
  default: {
    get: vi.fn(),
    patch: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
  parseSuccess: vi.fn(),
}));

import apiClient, { parseSuccess } from '@/lib/api';
import {
  createInvitation,
  fetchInvitations,
  fetchMembers,
  patchWorkspace,
  removeMember,
  revokeInvitation,
  updateMemberRole,
} from '@/features/settings/api';

describe('settings api', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('patchWorkspace calls workspace endpoint', async () => {
    const workspace = {
      id: 'ws-1',
      name: 'Acme',
      slug: 'acme',
      status: 'active' as const,
    };
    vi.mocked(apiClient.patch).mockResolvedValue({ data: {} });
    vi.mocked(parseSuccess).mockResolvedValue(workspace);

    const result = await patchWorkspace('ws-1', { name: 'Acme' });

    expect(apiClient.patch).toHaveBeenCalledWith('/workspaces/ws-1', { name: 'Acme' });
    expect(result).toEqual(workspace);
  });

  it('fetchMembers requests members list', async () => {
    const page = { items: [], cursor: { next_cursor: null, has_next: false } };
    vi.mocked(apiClient.get).mockResolvedValue({ data: {} });
    vi.mocked(parseSuccess).mockResolvedValue(page);

    await fetchMembers('ws-1');

    expect(apiClient.get).toHaveBeenCalledWith('/workspaces/ws-1/members', {
      params: undefined,
    });
  });

  it('updateMemberRole patches member role', async () => {
    const member = {
      user_id: 'u-1',
      email: 'a@example.com',
      full_name: null,
      role: AppRole.viewer,
      created_at: '2026-01-01T00:00:00Z',
    };
    vi.mocked(apiClient.patch).mockResolvedValue({ data: {} });
    vi.mocked(parseSuccess).mockResolvedValue(member);

    await updateMemberRole('ws-1', 'u-1', { role: AppRole.viewer });

    expect(apiClient.patch).toHaveBeenCalledWith('/workspaces/ws-1/members/u-1', {
      role: AppRole.viewer,
    });
  });

  it('removeMember deletes member', async () => {
    vi.mocked(apiClient.delete).mockResolvedValue({ data: {} });

    await removeMember('ws-1', 'u-1');

    expect(apiClient.delete).toHaveBeenCalledWith('/workspaces/ws-1/members/u-1');
  });

  it('fetchInvitations defaults to pending status', async () => {
    const page = { items: [], cursor: { next_cursor: null, has_next: false } };
    vi.mocked(apiClient.get).mockResolvedValue({ data: {} });
    vi.mocked(parseSuccess).mockResolvedValue(page);

    await fetchInvitations('ws-1');

    expect(apiClient.get).toHaveBeenCalledWith('/workspaces/ws-1/invitations', {
      params: { status: 'pending' },
    });
  });

  it('revokeInvitation deletes invitation', async () => {
    vi.mocked(apiClient.delete).mockResolvedValue({ data: {} });

    await revokeInvitation('ws-1', 'inv-1');

    expect(apiClient.delete).toHaveBeenCalledWith('/workspaces/ws-1/invitations/inv-1');
  });

  it('createInvitation posts invitation payload', async () => {
    const invitation = {
      id: 'inv-1',
      email: 'new@example.com',
      role: AppRole.viewer,
      status: 'pending' as const,
      expires_at: '2026-12-31T00:00:00Z',
      created_at: '2026-01-01T00:00:00Z',
    };
    vi.mocked(apiClient.post).mockResolvedValue({ data: {} });
    vi.mocked(parseSuccess).mockResolvedValue(invitation);

    const result = await createInvitation('ws-1', {
      email: 'new@example.com',
      role: AppRole.viewer,
    });

    expect(apiClient.post).toHaveBeenCalledWith('/workspaces/ws-1/invitations', {
      email: 'new@example.com',
      role: AppRole.viewer,
    });
    expect(result).toEqual(invitation);
  });
});
