// frontend/src/features/dashboard/widgets/SetupChecklistWidget.test.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { SetupChecklistWidget } from '@/features/dashboard/widgets/SetupChecklistWidget';
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
        <SetupChecklistWidget />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('SetupChecklistWidget', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders incomplete steps with links', async () => {
    vi.mocked(useAuth).mockReturnValue({
      user: {
        id: '1',
        email: 'admin@example.com',
        full_name: 'Admin User',
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
      data: { workspaceId: 'ws-1', memberCount: 1, installationCount: 0 },
      isLoading: false,
    } as unknown as ReturnType<typeof useChecklistContext>);

    renderWidget();

    expect(await screen.findByText(/get started/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /invite a teammate/i })).toHaveAttribute(
      'href',
      '/settings/team',
    );
    expect(screen.getByRole('link', { name: /connect a github installation/i })).toHaveAttribute(
      'href',
      '/installations',
    );
  });

  it('hides when all available steps are complete', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: {
        id: '1',
        email: 'admin@example.com',
        full_name: 'Admin User',
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
      data: { workspaceId: 'ws-1', memberCount: 2, installationCount: 1 },
      isLoading: false,
    } as unknown as ReturnType<typeof useChecklistContext>);

    const { container } = renderWidget();

    expect(container).toBeEmptyDOMElement();
  });
});
