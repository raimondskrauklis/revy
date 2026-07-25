// frontend/src/features/admin/pages/AdminDashboardPage.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { AdminDashboardPage } from '@/features/admin/pages/AdminDashboardPage';

vi.mock('@/features/admin/api', () => ({
  fetchAdminKpis: vi.fn(),
}));

import { fetchAdminKpis } from '@/features/admin/api';

describe('AdminDashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders KPI cards', async () => {
    vi.mocked(fetchAdminKpis).mockResolvedValue({
      workspaces_total: 10,
      workspaces_active: 8,
      workspaces_suspended: 2,
      users_active: 50,
      users_pending_approval: 0,
    });

    render(
      <MemoryRouter>
        <AdminDashboardPage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText('10')).toBeInTheDocument();
      expect(screen.getByText(/total workspaces/i)).toBeInTheDocument();
    });
  });

  it('shows pending approval banner', async () => {
    vi.mocked(fetchAdminKpis).mockResolvedValue({
      workspaces_total: 1,
      workspaces_active: 1,
      workspaces_suspended: 0,
      users_active: 5,
      users_pending_approval: 2,
    });

    render(
      <MemoryRouter>
        <AdminDashboardPage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText(/review signup queue/i)).toBeInTheDocument();
    });
  });
});
