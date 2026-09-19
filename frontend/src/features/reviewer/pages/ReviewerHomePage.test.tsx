// frontend/src/features/reviewer/pages/ReviewerHomePage.test.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fetchInstallations } from '@/features/installations/api';
import { fetchInstallationRepositories } from '@/features/reviewer/api';
import { ReviewerHomePage } from '@/features/reviewer/pages/ReviewerHomePage';
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

vi.mock('@/shared/errors/toasts', () => ({
  showDomainErrorToast: vi.fn(),
}));

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

function renderHome() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={['/reviewer']}>
        <Routes>
          <Route path="/reviewer" element={<ReviewerHomePage />} />
          <Route
            path="/reviewer/repositories/:id/pull-requests"
            element={<div>PR list</div>}
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('ReviewerHomePage', () => {
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

  it('navigates to the PR list when there is one installation and one repo', async () => {
    vi.mocked(fetchInstallations).mockResolvedValue([makeInstallation('inst-1', 'acme')]);
    vi.mocked(fetchInstallationRepositories).mockResolvedValue({
      items: [makeRepo('repo-1', 'api')],
      cursor: { has_next: false, next_cursor: null },
    });

    renderHome();

    expect(await screen.findByText('PR list')).toBeInTheDocument();
  });

  it('renders a table and does not hop when there are two repos', async () => {
    vi.mocked(fetchInstallations).mockResolvedValue([makeInstallation('inst-1', 'acme')]);
    vi.mocked(fetchInstallationRepositories).mockResolvedValue({
      items: [makeRepo('repo-1', 'api'), makeRepo('repo-2', 'web')],
      cursor: { has_next: false, next_cursor: null },
    });

    const { container } = renderHome();

    expect(await screen.findByText('api')).toBeInTheDocument();
    expect(screen.getByText('web')).toBeInTheDocument();
    expect(screen.queryByText('PR list')).not.toBeInTheDocument();
    expect(container.querySelector('select')).toBeNull();
  });

  it('shows QuietSelect and does not hop when there are two installations', async () => {
    vi.mocked(fetchInstallations).mockResolvedValue([
      makeInstallation('inst-1', 'acme'),
      makeInstallation('inst-2', 'other'),
    ]);
    vi.mocked(fetchInstallationRepositories).mockResolvedValue({
      items: [makeRepo('repo-1', 'api')],
      cursor: { has_next: false, next_cursor: null },
    });

    const { container } = renderHome();

    expect(await screen.findByText('acme')).toBeInTheDocument();
    expect(screen.queryByText('PR list')).not.toBeInTheDocument();
    expect(container.querySelector('select')).toBeNull();
    expect(screen.getByRole('combobox')).toBeInTheDocument();
  });

  it('shows an inline error when repositories fail to load', async () => {
    vi.mocked(fetchInstallations).mockResolvedValue([makeInstallation('inst-1', 'acme')]);
    vi.mocked(fetchInstallationRepositories).mockRejectedValue(new Error('boom'));

    renderHome();

    expect(await screen.findByText(/could not load repositories/i)).toBeInTheDocument();
  });
});
