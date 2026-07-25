// frontend/src/components/layout/UserMenu.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { UserMenu } from '@/components/layout/UserMenu';
import { AppRole } from '@/shared/types/enums';

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

import { useAuth } from '@/contexts/AuthContext';

describe('UserMenu', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('links profile to settings and signs out', async () => {
    const logout = vi.fn();
    vi.mocked(useAuth).mockReturnValue({
      user: {
        id: '1',
        email: 'user@example.com',
        full_name: 'Test User',
        status: 'active',
        platform_role: null,
        workspace_id: 'ws-1',
        role: AppRole.admin,
        memberships: [],
      },
      logout,
    } as unknown as ReturnType<typeof useAuth>);

    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <UserMenu />
      </MemoryRouter>,
    );

    await user.click(screen.getByRole('button', { name: /account menu/i }));

    const profileLink = screen.getByRole('link', { name: /profile & settings/i });
    expect(profileLink).toHaveAttribute('href', '/settings/profile');

    await user.click(screen.getByRole('button', { name: /sign out/i }));
    expect(logout).toHaveBeenCalled();
  });
});
