// frontend/src/components/layout/WorkspaceSwitcher.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { WorkspaceSwitcher } from '@/components/layout/WorkspaceSwitcher';
import { AppRole } from '@/shared/types/enums';

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

vi.mock('@/lib/me', () => ({
  setActiveWorkspace: vi.fn(),
}));

import { useAuth } from '@/contexts/AuthContext';
import { setActiveWorkspace } from '@/lib/me';

describe('WorkspaceSwitcher', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows workspace name when user has one membership', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: {
        id: '1',
        email: 'user@example.com',
        full_name: 'User',
        status: 'active',
        platform_role: null,
        workspace_id: 'ws-1',
        workspace_plan: 'free',
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
      refetchUser: vi.fn(),
    } as unknown as ReturnType<typeof useAuth>);

    render(<WorkspaceSwitcher />);

    expect(screen.getByText('Acme')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /switch workspace/i })).not.toBeInTheDocument();
  });

  it('switches workspace when another membership is selected', async () => {
    const refetchUser = vi.fn().mockResolvedValue(null);
    vi.mocked(setActiveWorkspace).mockResolvedValue({
      id: '1',
      email: 'user@example.com',
      full_name: 'User',
      locale: 'en',
      timezone: 'UTC',
      status: 'active',
      platform_role: null,
      workspace_id: 'ws-2',
      workspace_plan: null,
      role: AppRole.viewer,
      memberships: [],
    });
    vi.mocked(useAuth).mockReturnValue({
      user: {
        id: '1',
        email: 'user@example.com',
        full_name: 'User',
        status: 'active',
        platform_role: null,
        workspace_id: 'ws-1',
        workspace_plan: 'free',
        role: AppRole.admin,
        memberships: [
          {
            workspace_id: 'ws-1',
            workspace_name: 'Acme',
            workspace_slug: 'acme',
            role: AppRole.admin,
          },
          {
            workspace_id: 'ws-2',
            workspace_name: 'Beta',
            workspace_slug: 'beta',
            role: AppRole.viewer,
          },
        ],
      },
      refetchUser,
    } as unknown as ReturnType<typeof useAuth>);

    const user = userEvent.setup();
    render(<WorkspaceSwitcher />);

    await user.click(screen.getByRole('button', { name: /switch workspace/i }));
    await user.click(screen.getByRole('option', { name: 'Beta' }));

    expect(setActiveWorkspace).toHaveBeenCalledWith('ws-2');
    expect(refetchUser).toHaveBeenCalled();
  });
});
