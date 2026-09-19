// frontend/src/features/reviewer/ReviewerLayout.test.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fetchInstallations } from '@/features/installations/api';
import { fetchInstallationRepositories } from '@/features/reviewer/api';
import { ReviewerLayout } from '@/features/reviewer/ReviewerLayout';
import type { GitHubRepository } from '@/features/reviewer/types';
import { AppRole, GitHubAccountType, GitHubInstallationStatus } from '@/shared/types/enums';

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

vi.mock('@/features/installations/api', () => ({
  fetchInstallations: vi.fn(),
}));

vi.mock('@/features/reviewer/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/features/reviewer/api')>();
  return {
    ...actual,
    fetchInstallationRepositories: vi.fn(),
  };
});

import { useAuth } from '@/contexts/AuthContext';

function makeInstallation(id: string, login: string) {
  return {
    id,
    workspace_id: 'ws-1',
    github_installation_id: 1,
    account_login: login,
    account_type: GitHubAccountType.organization,
    account_id: 1,
    status: GitHubInstallationStatus.active,
    permissions_snapshot: null,
    verified_at: null,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  };
}

function makeRepo(id: string, name: string): GitHubRepository {
  return {
    id,
    installation_id: 'inst-1',
    workspace_id: 'ws-1',
    github_repository_id: 1,
    name,
    full_name: `acme/${name}`,
    default_branch: 'main',
    private: false,
    html_url: null,
    status: 'active',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  };
}

function renderLayout() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={['/reviewer/repositories/repo-1/pull-requests']}>
        <Routes>
          <Route path="/reviewer" element={<ReviewerLayout />}>
            <Route path="repositories/:id/pull-requests" element={<div>PRs</div>} />
          </Route>
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('ReviewerLayout', () => {
  beforeEach(() => {
    vi.clearAllMocks();
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
  });

  it('hides back to repositories when the one-repo hop applies', async () => {
    vi.mocked(fetchInstallations).mockResolvedValue([makeInstallation('inst-1', 'acme')]);
    vi.mocked(fetchInstallationRepositories).mockResolvedValue({
      items: [makeRepo('repo-1', 'api')],
      cursor: { has_next: false, next_cursor: null },
    });

    renderLayout();

    expect(await screen.findByText('PRs')).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.queryByRole('link', { name: /all repositories/i })).not.toBeInTheDocument();
    });
  });

  it('shows back to /reviewer when multiple repositories exist', async () => {
    vi.mocked(fetchInstallations).mockResolvedValue([makeInstallation('inst-1', 'acme')]);
    vi.mocked(fetchInstallationRepositories).mockResolvedValue({
      items: [makeRepo('repo-1', 'api'), makeRepo('repo-2', 'web')],
      cursor: { has_next: false, next_cursor: null },
    });

    renderLayout();

    expect(await screen.findByRole('link', { name: /all repositories/i })).toHaveAttribute(
      'href',
      '/reviewer',
    );
  });
});
