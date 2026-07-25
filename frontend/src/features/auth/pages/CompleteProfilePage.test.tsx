// frontend/src/features/auth/pages/CompleteProfilePage.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { CompleteProfilePage } from '@/features/auth/pages/CompleteProfilePage';
import { AppRole } from '@/shared/types/enums';

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

vi.mock('@/features/auth/api', () => ({
  completeProfile: vi.fn(),
}));

import { useAuth } from '@/contexts/AuthContext';
import { completeProfile } from '@/features/auth/api';

describe('CompleteProfilePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders profile form for pending_profile user', () => {
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: {
        id: '1',
        email: 'user@example.com',
        full_name: null,
        status: 'pending_profile',
        platform_role: null,
        workspace_id: null,
        workspace_plan: null,
        role: null,
        memberships: [],
      },
      refetchUser: vi.fn(),
    } as unknown as ReturnType<typeof useAuth>);

    render(
      <MemoryRouter>
        <CompleteProfilePage />
      </MemoryRouter>,
    );

    expect(screen.getByRole('button', { name: /continue/i })).toBeInTheDocument();
  });

  it('submits display name', async () => {
    const refetchUser = vi.fn().mockResolvedValue(null);
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: {
        id: '1',
        email: 'user@example.com',
        full_name: null,
        status: 'pending_profile',
        platform_role: null,
        workspace_id: null,
        workspace_plan: null,
        role: null,
        memberships: [],
      },
      refetchUser,
    } as unknown as ReturnType<typeof useAuth>);
    vi.mocked(completeProfile).mockResolvedValue({
      id: '1',
      email: 'user@example.com',
      full_name: 'Ada',
      locale: 'en',
      timezone: 'UTC',
      status: 'active',
      platform_role: null,
      workspace_id: 'ws',
      workspace_plan: null,
      role: AppRole.admin,
      memberships: [],
    });

    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <CompleteProfilePage />
      </MemoryRouter>,
    );

    await user.type(screen.getByRole('textbox'), 'Ada');
    await user.click(screen.getByRole('button', { name: /continue/i }));

    expect(completeProfile).toHaveBeenCalledWith({ full_name: 'Ada' });
    expect(refetchUser).toHaveBeenCalled();
  });
});
