// frontend/src/features/admin/pages/WorkspacesPage.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { WorkspacesPage } from '@/features/admin/pages/WorkspacesPage';

vi.mock('@/features/admin/api', () => ({
  fetchAdminWorkspaces: vi.fn(),
}));

import { fetchAdminWorkspaces } from '@/features/admin/api';

describe('WorkspacesPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows empty state when no workspaces', async () => {
    vi.mocked(fetchAdminWorkspaces).mockResolvedValue({
      items: [],
      cursor: { next_cursor: null, has_next: false },
    });

    render(
      <MemoryRouter>
        <WorkspacesPage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText(/no workspaces found/i)).toBeInTheDocument();
    });
  });

  it('lists workspaces', async () => {
    vi.mocked(fetchAdminWorkspaces).mockResolvedValue({
      items: [
        {
          id: 'ws-1',
          name: 'Acme Corp',
          slug: 'acme',
          status: 'active',
          plan: 'pro',
          member_count: 3,
          created_at: '2026-01-01T00:00:00Z',
        },
      ],
      cursor: { next_cursor: null, has_next: false },
    });

    render(
      <MemoryRouter>
        <WorkspacesPage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText('Acme Corp')).toBeInTheDocument();
      expect(screen.getByText('acme')).toBeInTheDocument();
    });
  });
});
