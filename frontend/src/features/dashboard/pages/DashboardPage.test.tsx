// frontend/src/features/dashboard/pages/DashboardPage.test.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { DashboardPage } from '@/features/dashboard/pages/DashboardPage';
import { AppRole } from '@/shared/types/enums';

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

vi.mock('@/features/dashboard/hooks', () => ({
  useWorkspaceAudit: vi.fn(),
  useChecklistContext: vi.fn(),
}));

vi.mock('@/platform/extensions/hooks', () => ({
  useExtensions: vi.fn(),
}));

import { useAuth } from '@/contexts/AuthContext';
import { useChecklistContext, useWorkspaceAudit } from '@/features/dashboard/hooks';
import { useExtensions } from '@/platform/extensions/hooks';

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useWorkspaceAudit).mockReturnValue({
      data: { items: [], cursor: { has_next: false, next_cursor: null } },
      isLoading: false,
    } as unknown as ReturnType<typeof useWorkspaceAudit>);
    vi.mocked(useChecklistContext).mockReturnValue({
      data: {
        workspaceId: 'ws-1',
        memberCount: 1,
        installationCount: 0,
        hasVerifiedInstallation: false,
        plan: 'free',
      },
      isLoading: false,
    } as unknown as ReturnType<typeof useChecklistContext>);
    vi.mocked(useExtensions).mockReturnValue([]);
  });

  it('shows no-workspace state without workspace widgets', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: {
        id: '1',
        email: 'user@example.com',
        full_name: 'User',
        status: 'active',
        platform_role: null,
        workspace_id: null,
        role: null,
        memberships: [],
        locale: 'en',
        timezone: 'UTC',
      },
    } as unknown as ReturnType<typeof useAuth>);

    renderPage();

    expect(screen.getByText(/select a workspace/i)).toBeInTheDocument();
    expect(screen.queryByText(/quick actions/i)).not.toBeInTheDocument();
  });

  it('renders workspace widgets when workspace is selected', async () => {
    vi.mocked(useAuth).mockReturnValue({
      user: {
        id: '1',
        email: 'admin@example.com',
        full_name: 'Admin',
        status: 'active',
        platform_role: null,
        workspace_id: 'ws-1',
        role: AppRole.admin,
        memberships: [
          {
            workspace_id: 'ws-1',
            workspace_name: 'Acme',
            workspace_slug: 'acme',
            role: AppRole.admin,
          },
        ],
        locale: 'en',
        timezone: 'UTC',
      },
    } as unknown as ReturnType<typeof useAuth>);

    renderPage();

    expect(await screen.findByText(/welcome, admin/i)).toBeInTheDocument();
    expect(screen.getByText(/quick actions/i)).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /recent activity/i })).toBeInTheDocument();
  });
});
