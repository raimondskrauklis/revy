// frontend/src/features/reviewer/useReviewerRepoHop.test.ts
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import { type ReactNode, createElement } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fetchInstallations } from '@/features/installations/api';
import { fetchInstallationRepositories } from '@/features/reviewer/api';
import { useReviewerRepoHop } from '@/features/reviewer/useReviewerRepoHop';
import type { GitHubRepository } from '@/features/reviewer/types';
import { GitHubAccountType, GitHubInstallationStatus, AppRole } from '@/shared/types/enums';

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
    github_installation_id: Number(id.replace(/\D/g, '') || 1),
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

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return createElement(QueryClientProvider, { client }, children);
}

describe('useReviewerRepoHop', () => {
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

  it('hops when one installation has one repository', async () => {
    vi.mocked(fetchInstallations).mockResolvedValue([makeInstallation('inst-1', 'acme')]);
    vi.mocked(fetchInstallationRepositories).mockResolvedValue({
      items: [makeRepo('repo-1', 'api')],
      cursor: { has_next: false, next_cursor: null },
    });

    const { result } = renderHook(() => useReviewerRepoHop(), { wrapper });

    await waitFor(() => {
      expect(result.current.shouldHop).toBe(true);
    });
    expect(result.current.hopRepositoryId).toBe('repo-1');
  });

  it('does not hop when one installation has two repositories', async () => {
    vi.mocked(fetchInstallations).mockResolvedValue([makeInstallation('inst-1', 'acme')]);
    vi.mocked(fetchInstallationRepositories).mockResolvedValue({
      items: [makeRepo('repo-1', 'api'), makeRepo('repo-2', 'web')],
      cursor: { has_next: false, next_cursor: null },
    });

    const { result } = renderHook(() => useReviewerRepoHop(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
    expect(result.current.shouldHop).toBe(false);
  });

  it('does not hop when two installations exist even with one repo on the first', async () => {
    vi.mocked(fetchInstallations).mockResolvedValue([
      makeInstallation('inst-1', 'acme'),
      makeInstallation('inst-2', 'other'),
    ]);
    vi.mocked(fetchInstallationRepositories).mockResolvedValue({
      items: [makeRepo('repo-1', 'api')],
      cursor: { has_next: false, next_cursor: null },
    });

    const { result } = renderHook(() => useReviewerRepoHop(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
    expect(result.current.shouldHop).toBe(false);
    expect(fetchInstallationRepositories).not.toHaveBeenCalled();
  });

  it('does not hop when the first repository page has a next cursor', async () => {
    vi.mocked(fetchInstallations).mockResolvedValue([makeInstallation('inst-1', 'acme')]);
    vi.mocked(fetchInstallationRepositories).mockResolvedValue({
      items: [makeRepo('repo-1', 'api')],
      cursor: { has_next: true, next_cursor: 'c1' },
    });

    const { result } = renderHook(() => useReviewerRepoHop(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
    expect(result.current.shouldHop).toBe(false);
  });
});
