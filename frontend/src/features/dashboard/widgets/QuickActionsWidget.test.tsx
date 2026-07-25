// frontend/src/features/dashboard/widgets/QuickActionsWidget.test.tsx
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { QuickActionsWidget } from '@/features/dashboard/widgets/QuickActionsWidget';
import { AppRole } from '@/shared/types/enums';

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

import { useAuth } from '@/contexts/AuthContext';

describe('QuickActionsWidget', () => {
  it('hides when no workspace is selected', () => {
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

    const { container } = render(
      <MemoryRouter>
        <QuickActionsWidget />
      </MemoryRouter>,
    );

    expect(container).toBeEmptyDOMElement();
  });

  it('shows invite link for admins', () => {
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

    render(
      <MemoryRouter>
        <QuickActionsWidget />
      </MemoryRouter>,
    );

    expect(screen.getByRole('link', { name: /settings/i })).toHaveAttribute(
      'href',
      '/settings/profile',
    );
    expect(screen.getByRole('link', { name: /installations/i })).toHaveAttribute(
      'href',
      '/installations',
    );
    expect(screen.getByRole('link', { name: /invite teammate/i })).toHaveAttribute(
      'href',
      '/settings/team',
    );
  });

  it('hides invite link for viewers', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: {
        id: '2',
        email: 'viewer@example.com',
        full_name: null,
        status: 'active',
        platform_role: null,
        workspace_id: 'ws-1',
        role: AppRole.viewer,
        memberships: [],
        locale: 'en',
        timezone: 'UTC',
      },
    } as unknown as ReturnType<typeof useAuth>);

    render(
      <MemoryRouter>
        <QuickActionsWidget />
      </MemoryRouter>,
    );

    expect(screen.queryByRole('link', { name: /invite teammate/i })).not.toBeInTheDocument();
  });
});
