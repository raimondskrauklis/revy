// frontend/src/features/installations/InstallationsSummaryWidget.test.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { InstallationsSummaryWidget } from '@/features/installations/InstallationsSummaryWidget';
import { AppRole } from '@/shared/types/enums';

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

vi.mock('@/features/dashboard/hooks', () => ({
  useChecklistContext: vi.fn(),
}));

import { useAuth } from '@/contexts/AuthContext';
import { useChecklistContext } from '@/features/dashboard/hooks';

function renderWidget() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <InstallationsSummaryWidget />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('InstallationsSummaryWidget', () => {
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
        locale: 'en',
        timezone: 'UTC',
      },
    } as unknown as ReturnType<typeof useAuth>);
    vi.mocked(useChecklistContext).mockReturnValue({
      data: {
        workspaceId: 'ws-1',
        memberCount: 1,
        installationCount: 2,
        hasVerifiedInstallation: false,
        plan: 'free',
      },
      isLoading: false,
    } as unknown as ReturnType<typeof useChecklistContext>);

    renderWidget();

    expect(await screen.findByText(/2 installations connected/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /manage installations/i })).toHaveAttribute(
      'href',
      '/installations',
    );
  });
});
