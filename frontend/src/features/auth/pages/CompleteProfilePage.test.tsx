// frontend/src/features/auth/pages/CompleteProfilePage.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
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
        <Routes>
          <Route path="/" element={<CompleteProfilePage />} />
          <Route path="/reviewer" element={<div>Reviewer</div>} />
          <Route path="/pending-approval" element={<div>Pending</div>} />
        </Routes>
      </MemoryRouter>,
    );

    await user.type(screen.getByRole('textbox'), 'Ada');
    await user.click(screen.getByRole('button', { name: /continue/i }));

    expect(completeProfile).toHaveBeenCalledWith({ full_name: 'Ada' });
    expect(refetchUser).toHaveBeenCalled();
    await waitFor(() => {
      expect(screen.getByText('Reviewer')).toBeInTheDocument();
    });
  });

  it('sends already-active users to reviewer', () => {
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: {
        id: '1',
        email: 'user@example.com',
        full_name: 'Ada',
        status: 'active',
        platform_role: null,
        workspace_id: 'ws',
        workspace_plan: null,
        role: AppRole.admin,
        memberships: [],
      },
      refetchUser: vi.fn(),
    } as unknown as ReturnType<typeof useAuth>);

    render(
      <MemoryRouter>
        <Routes>
          <Route path="/" element={<CompleteProfilePage />} />
          <Route path="/reviewer" element={<div>Reviewer</div>} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText('Reviewer')).toBeInTheDocument();
  });

  it('keeps pending_approval users on pending-approval', () => {
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: {
        id: '1',
        email: 'user@example.com',
        full_name: 'Ada',
        status: 'pending_approval',
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
        <Routes>
          <Route path="/" element={<CompleteProfilePage />} />
          <Route path="/pending-approval" element={<div>Pending</div>} />
          <Route path="/reviewer" element={<div>Reviewer</div>} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText('Pending')).toBeInTheDocument();
    expect(screen.queryByText('Reviewer')).not.toBeInTheDocument();
  });
});
