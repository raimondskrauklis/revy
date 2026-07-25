// frontend/src/features/settings/pages/TeamSettingsPage.test.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { TeamSettingsPage } from '@/features/settings/pages/TeamSettingsPage';
import { AppRole } from '@/shared/types/enums';

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

vi.mock('@/features/settings/api', () => ({
  fetchMembers: vi.fn(),
  fetchInvitations: vi.fn(),
}));

import { useAuth } from '@/contexts/AuthContext';
import { fetchMembers, fetchInvitations } from '@/features/settings/api';

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <TeamSettingsPage />
    </QueryClientProvider>,
  );
}

describe('TeamSettingsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows members and permissions matrix for viewers', async () => {
    vi.mocked(useAuth).mockReturnValue({
      user: {
        id: '2',
        email: 'viewer@example.com',
        full_name: null,
        status: 'active',
        platform_role: null,
        workspace_id: 'ws-1',
        role: AppRole.viewer,
        memberships: [],
      },
    } as unknown as ReturnType<typeof useAuth>);
    vi.mocked(fetchMembers).mockResolvedValue({
      items: [
        {
          user_id: '2',
          email: 'viewer@example.com',
          full_name: null,
          role: AppRole.viewer,
          created_at: '2026-01-01T00:00:00Z',
        },
      ],
      cursor: { next_cursor: null, has_next: false },
    });

    renderPage();

    expect(await screen.findByText('viewer@example.com')).toBeInTheDocument();
    expect(screen.getByText(/role permissions/i)).toBeInTheDocument();
    expect(screen.queryByText(/invite member/i)).not.toBeInTheDocument();
    expect(fetchInvitations).not.toHaveBeenCalled();
  });

  it('shows invite form for admins', async () => {
    vi.mocked(useAuth).mockReturnValue({
      user: {
        id: '1',
        email: 'admin@example.com',
        full_name: 'Admin',
        status: 'active',
        platform_role: null,
        workspace_id: 'ws-1',
        role: AppRole.admin,
        memberships: [],
      },
    } as unknown as ReturnType<typeof useAuth>);
    vi.mocked(fetchMembers).mockResolvedValue({
      items: [],
      cursor: { next_cursor: null, has_next: false },
    });
    vi.mocked(fetchInvitations).mockResolvedValue({
      items: [],
      cursor: { next_cursor: null, has_next: false },
    });

    renderPage();

    expect(await screen.findByText(/invite member/i)).toBeInTheDocument();
    expect(fetchInvitations).toHaveBeenCalled();
  });
});
