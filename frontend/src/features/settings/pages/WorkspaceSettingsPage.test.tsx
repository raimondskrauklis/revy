// frontend/src/features/settings/pages/WorkspaceSettingsPage.test.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { WorkspaceSettingsPage } from '@/features/settings/pages/WorkspaceSettingsPage';
import { AppRole } from '@/shared/types/enums';

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

vi.mock('@/features/settings/api', () => ({
  patchWorkspace: vi.fn(),
}));

import { useAuth } from '@/contexts/AuthContext';
import { patchWorkspace } from '@/features/settings/api';

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <WorkspaceSettingsPage />
    </QueryClientProvider>,
  );
}

describe('WorkspaceSettingsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders workspace form and saves changes', async () => {
    const refetchUser = vi.fn().mockResolvedValue(null);
    vi.mocked(useAuth).mockReturnValue({
      user: {
        id: '1',
        email: 'admin@example.com',
        full_name: 'Admin',
        locale: 'en',
        timezone: 'UTC',
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
      },
      refetchUser,
    } as unknown as ReturnType<typeof useAuth>);
    vi.mocked(patchWorkspace).mockResolvedValue({
      id: 'ws-1',
      name: 'Acme Labs',
      slug: 'acme',
      status: 'active',
    });

    const user = userEvent.setup();
    renderPage();

    expect(screen.getByDisplayValue('acme')).toBeDisabled();
    await user.clear(screen.getByDisplayValue('Acme'));
    await user.type(screen.getByLabelText(/workspace name/i), 'Acme Labs');
    await user.click(screen.getByRole('button', { name: /save/i }));

    await waitFor(() => {
      expect(patchWorkspace).toHaveBeenCalledWith('ws-1', { name: 'Acme Labs' });
    });
    expect(refetchUser).toHaveBeenCalled();
  });
});
