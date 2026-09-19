// frontend/src/features/installations/RevyGitHubIntegrationCard.test.tsx
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { RevyGitHubIntegrationCard } from '@/features/installations/RevyGitHubIntegrationCard';
import { AppRole, GitHubAccountType, GitHubInstallationStatus } from '@/shared/types/enums';

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

vi.mock('@/features/installations/api', () => ({
  fetchInstallations: vi.fn(),
}));

import { useAuth } from '@/contexts/AuthContext';
import { fetchInstallations } from '@/features/installations/api';

describe('RevyGitHubIntegrationCard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows installation count and manage link', async () => {
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
    vi.mocked(fetchInstallations).mockResolvedValue([
      {
        id: 'inst-1',
        workspace_id: 'ws-1',
        github_installation_id: 123,
        account_login: 'acme',
        account_type: GitHubAccountType.organization,
        account_id: 1,
        status: GitHubInstallationStatus.active,
        permissions_snapshot: null,
        verified_at: null,
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
      },
    ]);

    render(
      <MemoryRouter>
        <RevyGitHubIntegrationCard />
      </MemoryRouter>,
    );

    expect(await screen.findByText(/1 installation connected/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /manage installations/i })).toHaveAttribute(
      'href',
      '/installations',
    );
  });
});
