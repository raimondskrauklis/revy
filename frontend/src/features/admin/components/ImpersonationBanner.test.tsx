// frontend/src/features/admin/components/ImpersonationBanner.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { ImpersonationBanner } from '@/features/admin/components/ImpersonationBanner';

const refetchUser = vi.fn();
const navigate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => navigate,
  };
});

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({
    user: {
      id: 'u1',
      email: 'target@example.com',
      impersonation: {
        active: true,
        actor_user_id: 'admin-1',
        target_user_id: 'u1',
        target_email: 'target@example.com',
        reason: 'Support ticket #42 — cannot access billing settings',
      },
    },
    refetchUser,
  }),
}));

vi.mock('@/features/admin/api', () => ({
  stopImpersonation: vi.fn(),
}));

import { stopImpersonation } from '@/features/admin/api';

describe('ImpersonationBanner', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    refetchUser.mockResolvedValue(null);
    vi.mocked(stopImpersonation).mockResolvedValue({ active: false });
  });

  it('renders when impersonation is active', () => {
    render(
      <MemoryRouter>
        <ImpersonationBanner />
      </MemoryRouter>,
    );

    expect(screen.getByText(/target@example.com/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /stop impersonation/i })).toBeInTheDocument();
  });

  it('stops impersonation and navigates to dashboard', async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <ImpersonationBanner />
      </MemoryRouter>,
    );

    await user.click(screen.getByRole('button', { name: /stop impersonation/i }));

    await waitFor(() => {
      expect(stopImpersonation).toHaveBeenCalled();
      expect(refetchUser).toHaveBeenCalled();
      expect(navigate).toHaveBeenCalledWith('/dashboard');
    });
  });
});
