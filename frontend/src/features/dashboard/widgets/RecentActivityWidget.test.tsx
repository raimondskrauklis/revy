// frontend/src/features/dashboard/widgets/RecentActivityWidget.test.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { RecentActivityWidget } from '@/features/dashboard/widgets/RecentActivityWidget';
import { AppRole } from '@/shared/types/enums';

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

vi.mock('@/features/dashboard/hooks', () => ({
  useWorkspaceAudit: vi.fn(),
}));

import { useAuth } from '@/contexts/AuthContext';
import { useWorkspaceAudit } from '@/features/dashboard/hooks';

function renderWidget() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <RecentActivityWidget />
    </QueryClientProvider>,
  );
}

describe('RecentActivityWidget', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows empty state when no audit items', async () => {
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
        locale: 'en',
        timezone: 'UTC',
      },
    } as unknown as ReturnType<typeof useAuth>);
    vi.mocked(useWorkspaceAudit).mockReturnValue({
      data: { items: [], cursor: { has_next: false, next_cursor: null } },
      isLoading: false,
    } as unknown as ReturnType<typeof useWorkspaceAudit>);

    renderWidget();

    expect(await screen.findByText(/no recent activity/i)).toBeInTheDocument();
  });

  it('renders audit items with actor email', async () => {
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
        locale: 'en',
        timezone: 'UTC',
      },
    } as unknown as ReturnType<typeof useAuth>);
    vi.mocked(useWorkspaceAudit).mockReturnValue({
      data: {
        items: [
          {
            id: 'audit-1',
            created_at: '2026-01-01T12:00:00Z',
            action: 'workspace.updated',
            resource_type: 'workspace',
            resource_id: 'ws-1',
            actor_user_id: '1',
            actor_email: 'admin@example.com',
            metadata: {},
          },
        ],
        cursor: { has_next: false, next_cursor: null },
      },
      isLoading: false,
    } as unknown as ReturnType<typeof useWorkspaceAudit>);

    renderWidget();

    expect(await screen.findByText(/updated the workspace/i)).toBeInTheDocument();
    expect(screen.getAllByText('admin@example.com').length).toBeGreaterThan(0);
  });
});
