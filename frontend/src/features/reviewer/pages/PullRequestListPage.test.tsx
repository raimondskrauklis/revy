// frontend/src/features/reviewer/pages/PullRequestListPage.test.tsx
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { PullRequestListPage } from '@/features/reviewer/pages/PullRequestListPage';
import { AppRole } from '@/shared/types/enums';

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

vi.mock('@/features/reviewer/hooks', () => ({
  usePullRequests: vi.fn(),
}));

vi.mock('@/shared/errors/toasts', () => ({
  showDomainErrorToast: vi.fn(),
}));

import { useAuth } from '@/contexts/AuthContext';
import { usePullRequests } from '@/features/reviewer/hooks';

function renderList() {
  return render(
    <MemoryRouter initialEntries={['/reviewer/repositories/repo-1/pull-requests']}>
      <Routes>
        <Route
          path="/reviewer/repositories/:repoId/pull-requests"
          element={<PullRequestListPage />}
        />
      </Routes>
    </MemoryRouter>,
  );
}

describe('PullRequestListPage', () => {
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

  it('shows loading copy', () => {
    vi.mocked(usePullRequests).mockReturnValue({
      items: [],
      isLoading: true,
      error: null,
      ref: vi.fn(),
    } as unknown as ReturnType<typeof usePullRequests>);

    renderList();
    expect(screen.getByText(/loading pull requests/i)).toBeInTheDocument();
  });

  it('shows empty copy', () => {
    vi.mocked(usePullRequests).mockReturnValue({
      items: [],
      isLoading: false,
      error: null,
      ref: vi.fn(),
    } as unknown as ReturnType<typeof usePullRequests>);

    renderList();
    expect(screen.getByText(/no pull requests ingested/i)).toBeInTheDocument();
  });

  it('shows inline error text, not toast-only', () => {
    vi.mocked(usePullRequests).mockReturnValue({
      items: [],
      isLoading: false,
      error: new Error('boom'),
      ref: vi.fn(),
    } as unknown as ReturnType<typeof usePullRequests>);

    renderList();
    expect(screen.getByText(/could not load pull requests/i)).toBeInTheDocument();
  });
});
