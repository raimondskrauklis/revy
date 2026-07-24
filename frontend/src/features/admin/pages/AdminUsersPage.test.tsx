// frontend/src/features/admin/pages/AdminUsersPage.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { AdminUsersPage } from '@/features/admin/pages/AdminUsersPage';

vi.mock('@/features/admin/api', () => ({
  fetchPendingUsers: vi.fn(),
  approvePendingUser: vi.fn(),
  rejectPendingUser: vi.fn(),
}));

import { fetchPendingUsers } from '@/features/admin/api';

describe('AdminUsersPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows empty state when queue is empty', async () => {
    vi.mocked(fetchPendingUsers).mockResolvedValue([]);

    render(<AdminUsersPage />);

    await waitFor(() => {
      expect(screen.getByText(/no users awaiting approval/i)).toBeInTheDocument();
    });
  });

  it('lists pending users', async () => {
    vi.mocked(fetchPendingUsers).mockResolvedValue([
      {
        id: 'u1',
        email: 'pending@example.com',
        full_name: 'Pending User',
        status: 'pending_approval',
        created_at: '2026-01-01T00:00:00Z',
      },
    ]);

    render(<AdminUsersPage />);

    await waitFor(() => {
      expect(screen.getByText('pending@example.com')).toBeInTheDocument();
    });
  });
});
