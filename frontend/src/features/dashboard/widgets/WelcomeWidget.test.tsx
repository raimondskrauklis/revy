// frontend/src/features/dashboard/widgets/WelcomeWidget.test.tsx
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { WelcomeWidget } from '@/features/dashboard/widgets/WelcomeWidget';
import { AppRole } from '@/shared/types/enums';

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

import { useAuth } from '@/contexts/AuthContext';

describe('WelcomeWidget', () => {
  it('shows no-workspace message', () => {
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

    render(<WelcomeWidget />);

    expect(screen.getByText(/select a workspace/i)).toBeInTheDocument();
  });

  it('shows greeting and workspace name', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: {
        id: '1',
        email: 'admin@example.com',
        full_name: 'Admin User',
        status: 'active',
        platform_role: null,
        workspace_id: 'ws-1',
        role: AppRole.admin,
        memberships: [
          {
            workspace_id: 'ws-1',
            workspace_name: 'Acme Corp',
            workspace_slug: 'acme',
            role: AppRole.admin,
          },
        ],
        locale: 'en',
        timezone: 'UTC',
      },
    } as unknown as ReturnType<typeof useAuth>);

    render(<WelcomeWidget />);

    expect(screen.getByText(/welcome, admin user/i)).toBeInTheDocument();
    expect(screen.getByText(/acme corp/i)).toBeInTheDocument();
  });
});
