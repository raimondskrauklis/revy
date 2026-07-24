// frontend/src/features/installations/pages/InstallationsPage.test.tsx
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { InstallationsPage } from '@/features/installations/pages/InstallationsPage';
import { AppRole } from '@/shared/types/enums';

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

vi.mock('@/features/installations/api', () => ({
  fetchInstallations: vi.fn(),
  registerInstallation: vi.fn(),
}));

import { useAuth } from '@/contexts/AuthContext';
import { fetchInstallations } from '@/features/installations/api';

describe('InstallationsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows empty state when no installations', async () => {
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
    vi.mocked(fetchInstallations).mockResolvedValue([]);

    render(<InstallationsPage />);

    expect(await screen.findByText(/no github installations/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /register installation/i })).toBeInTheDocument();
  });

  it('hides register form for viewers', async () => {
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
    vi.mocked(fetchInstallations).mockResolvedValue([]);

    render(<InstallationsPage />);

    expect(await screen.findByText(/no github installations/i)).toBeInTheDocument();
    expect(screen.queryByText(/register installation/i)).not.toBeInTheDocument();
  });
});
