// frontend/src/features/admin/pages/WorkspaceDetailPage.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { WorkspaceDetailPage } from '@/features/admin/pages/WorkspaceDetailPage';

vi.mock('@/features/admin/api', () => ({
  fetchAdminWorkspaceDetail: vi.fn(),
  fetchAdminWorkspaceMembers: vi.fn(),
  suspendAdminWorkspace: vi.fn(),
  unsuspendAdminWorkspace: vi.fn(),
}));

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({
    refetchUser: vi.fn(),
  }),
}));

import {
  fetchAdminWorkspaceDetail,
  fetchAdminWorkspaceMembers,
  suspendAdminWorkspace,
} from '@/features/admin/api';

const workspace = {
  id: 'ws-1',
  name: 'Acme Corp',
  slug: 'acme',
  status: 'active' as const,
  plan: 'pro',
  member_count: 3,
  stripe_customer_id: 'cus_***',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-02T00:00:00Z',
};

describe('WorkspaceDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(fetchAdminWorkspaceMembers).mockResolvedValue({
      items: [],
      cursor: { next_cursor: null, has_next: false },
    });
  });

  it('renders workspace detail', async () => {
    vi.mocked(fetchAdminWorkspaceDetail).mockResolvedValue(workspace);

    render(
      <MemoryRouter initialEntries={['/admin/workspaces/ws-1']}>
        <Routes>
          <Route path="/admin/workspaces/:workspaceId" element={<WorkspaceDetailPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Acme Corp' })).toBeInTheDocument();
      expect(screen.getByText('cus_***')).toBeInTheDocument();
    });
  });

  it('confirms suspend action', async () => {
    const user = userEvent.setup();
    vi.mocked(fetchAdminWorkspaceDetail).mockResolvedValue(workspace);
    vi.mocked(suspendAdminWorkspace).mockResolvedValue({ ...workspace, status: 'suspended' });

    render(
      <MemoryRouter initialEntries={['/admin/workspaces/ws-1']}>
        <Routes>
          <Route path="/admin/workspaces/:workspaceId" element={<WorkspaceDetailPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /suspend workspace/i })).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /suspend workspace/i }));
    await user.click(screen.getByRole('button', { name: /confirm/i }));

    await waitFor(() => {
      expect(suspendAdminWorkspace).toHaveBeenCalledWith('ws-1');
    });
  });
});
